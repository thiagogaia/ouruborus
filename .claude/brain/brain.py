#!/usr/bin/env python3
"""
brain.py - Cerebro Organizacional do Engram

Grafo de conhecimento em memoria usando NetworkX.
Persistencia em JSON para compatibilidade com Git.

Uso:
    from brain import Brain

    brain = Brain()
    brain.load()

    # Adicionar memoria
    brain.add_memory(...)

    # Buscar
    results = brain.retrieve(query_embedding)

    # Salvar
    brain.save()
"""

import json
import math
import hashlib
import subprocess
import re
import os
import site
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from uuid import uuid4

# ── Auto-activate brain venv (PAT-012) ──
# The brain's dependencies (numpy, networkx) live in .claude/brain/.venv/
# This block activates it transparently so all scripts just work.
_venv_dir = Path(__file__).parent / ".venv"
if _venv_dir.exists() and "brain/.venv" not in os.environ.get("VIRTUAL_ENV", ""):
    _site_packages = list(_venv_dir.glob("lib/python*/site-packages"))
    if _site_packages:
        site.addsitedir(str(_site_packages[0]))

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False


class FallbackGraph:
    """Grafo simples quando NetworkX nao esta disponivel."""

    def __init__(self):
        self._nodes = {}
        self._edges = {}
        self._adj_out = {}
        self._adj_in = {}

    def add_node(self, node_id: str, **attrs):
        self._nodes[node_id] = attrs
        if node_id not in self._adj_out:
            self._adj_out[node_id] = []
        if node_id not in self._adj_in:
            self._adj_in[node_id] = []

    def add_edge(self, source: str, target: str, **attrs):
        edge_key = (source, target)
        self._edges[edge_key] = attrs
        if source not in self._adj_out:
            self._adj_out[source] = []
        if target not in self._adj_in:
            self._adj_in[target] = []
        if target not in self._adj_out[source]:
            self._adj_out[source].append(target)
        if source not in self._adj_in[target]:
            self._adj_in[target].append(source)

    @property
    def nodes(self):
        return self._nodes

    @property
    def edges(self):
        return self._edges

    def successors(self, node_id: str):
        return self._adj_out.get(node_id, [])

    def predecessors(self, node_id: str):
        return self._adj_in.get(node_id, [])

    def number_of_nodes(self):
        return len(self._nodes)

    def number_of_edges(self):
        return len(self._edges)

    def degree(self):
        result = []
        for node_id in self._nodes:
            out_deg = len(self._adj_out.get(node_id, []))
            in_deg = len(self._adj_in.get(node_id, []))
            result.append((node_id, out_deg + in_deg))
        return result


class Brain:
    """
    Cerebro organizacional - grafo de conhecimento com processos cognitivos.
    """

    def __init__(self, base_path: Path = None):
        if base_path is None:
            base_path = Path(".claude/brain")
        self.base_path = Path(base_path)
        self.memory_path = self.base_path.parent / "memory"

        # Grafo
        if HAS_NETWORKX:
            self.graph = nx.DiGraph()
        else:
            self.graph = FallbackGraph()

        # Embeddings
        self.embeddings: Dict[str, Any] = {}

        # Cache de estatisticas
        self._stats_cache = None
        self._stats_time = None

    # ══════════════════════════════════════════════════════════
    # PERSISTENCIA
    # ══════════════════════════════════════════════════════════

    def load(self) -> bool:
        """Carrega grafo e embeddings do disco."""
        graph_file = self.base_path / "graph.json"

        if not graph_file.exists():
            print(f"Info: No graph found at {graph_file}")
            return False

        try:
            data = json.loads(graph_file.read_text(encoding='utf-8'))

            # Carrega nos
            for node_id, node_data in data.get("nodes", {}).items():
                if HAS_NETWORKX:
                    self.graph.add_node(node_id, **node_data)
                else:
                    self.graph.add_node(node_id, **node_data)

            # Carrega arestas
            for edge in data.get("edges", []):
                if HAS_NETWORKX:
                    self.graph.add_edge(
                        edge["src"],
                        edge["tgt"],
                        type=edge.get("type", "REFERENCES"),
                        weight=edge.get("weight", 0.5),
                        props=edge.get("props", {})
                    )
                else:
                    self.graph.add_edge(
                        edge["src"],
                        edge["tgt"],
                        type=edge.get("type", "REFERENCES"),
                        weight=edge.get("weight", 0.5),
                        props=edge.get("props", {})
                    )

            print(f"Loaded: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")
        except Exception as e:
            print(f"Error loading graph: {e}")
            return False

        # Carrega embeddings
        if HAS_NUMPY:
            emb_file = self.base_path / "embeddings.npz"
            if emb_file.exists():
                try:
                    loaded = np.load(emb_file)
                    self.embeddings = {k: loaded[k] for k in loaded.files}
                    print(f"Loaded: {len(self.embeddings)} embeddings")
                except Exception as e:
                    print(f"Error loading embeddings: {e}")

        return True

    def save(self):
        """Salva grafo e embeddings no disco."""
        self.base_path.mkdir(parents=True, exist_ok=True)

        # Serializa grafo
        nodes_data = {}
        for node_id in (self.graph.nodes if HAS_NETWORKX else self.graph._nodes):
            if HAS_NETWORKX:
                nodes_data[node_id] = dict(self.graph.nodes[node_id])
            else:
                nodes_data[node_id] = dict(self.graph._nodes[node_id])

        edges_data = []
        if HAS_NETWORKX:
            for u, v in self.graph.edges:
                edge_attrs = dict(self.graph.edges[u, v])
                edges_data.append({"src": u, "tgt": v, **edge_attrs})
        else:
            for (u, v), attrs in self.graph._edges.items():
                edges_data.append({"src": u, "tgt": v, **attrs})

        data = {
            "version": "1.0",
            "meta": {
                "saved_at": datetime.now().isoformat(),
                "node_count": self.graph.number_of_nodes(),
                "edge_count": self.graph.number_of_edges()
            },
            "nodes": nodes_data,
            "edges": edges_data
        }

        graph_file = self.base_path / "graph.json"
        graph_file.write_text(
            json.dumps(data, indent=2, ensure_ascii=False, default=str),
            encoding='utf-8'
        )
        print(f"Saved: {graph_file}")

        # Salva embeddings
        if HAS_NUMPY and self.embeddings:
            emb_file = self.base_path / "embeddings.npz"
            np.savez_compressed(emb_file, **self.embeddings)
            print(f"Saved: {emb_file}")

    # ══════════════════════════════════════════════════════════
    # ENCODING (criar memoria)
    # ══════════════════════════════════════════════════════════

    def add_memory(
        self,
        title: str,
        content: str,
        labels: List[str],
        author: str,
        props: Dict[str, Any] = None,
        references: List[str] = None,
        embedding: Any = None
    ) -> str:
        """
        Adiciona uma nova memoria ao cerebro.

        Args:
            title: Titulo da memoria
            content: Conteudo completo
            labels: Labels do no (Episode, Concept, Pattern, etc)
            author: Autor (@username)
            props: Propriedades adicionais
            references: IDs de nos referenciados
            embedding: Vetor de embedding (opcional)

        Returns:
            ID do no criado
        """
        # Deterministic ID: md5(title|labels) for dedup
        id_source = f"{title}|{'|'.join(sorted(labels))}"
        node_id = hashlib.md5(id_source.encode()).hexdigest()[:8]
        now = datetime.now().isoformat()

        # Upsert: if node already exists, update instead of duplicate
        if self._node_exists(node_id):
            return self._upsert_node(node_id, title, content, labels, author, props, references, embedding)

        # Cria summary
        summary = self._generate_summary(content)

        # Propriedades do no — content stored in-graph (no disk I/O)
        node_props = {
            "title": title,
            "author": author,
            "content": content,
            "summary": summary,
            **(props or {})
        }

        # Estado de memoria
        memory_state = {
            "strength": 1.0,
            "access_count": 1,
            "last_accessed": now,
            "created_at": now,
            "decay_rate": self._get_decay_rate(labels)
        }

        # Adiciona no
        if HAS_NETWORKX:
            self.graph.add_node(
                node_id,
                labels=labels,
                props=node_props,
                memory=memory_state
            )
        else:
            self.graph.add_node(
                node_id,
                labels=labels,
                props=node_props,
                memory=memory_state
            )

        # Adiciona embedding
        if embedding is not None and HAS_NUMPY:
            self.embeddings[node_id] = np.array(embedding)

        # Cria aresta de autoria
        author_node = self._ensure_person_node(author)
        self.add_edge(node_id, author_node, "AUTHORED_BY")

        # Cria arestas de referencia
        if references:
            for ref_id in references:
                if self._node_exists(ref_id):
                    self.add_edge(node_id, ref_id, "REFERENCES")

        # Extrai e cria referencias de [[links]] no conteudo
        links = self._extract_links(content)
        for link in links:
            target = self._resolve_link(link)
            if target:
                self.add_edge(node_id, target, "REFERENCES")

        # Detecta dominio
        domain = self._infer_domain(content, labels)
        if domain:
            domain_node = self._ensure_domain_node(domain)
            self.add_edge(node_id, domain_node, "BELONGS_TO")

        return node_id

    def _upsert_node(
        self,
        node_id: str,
        title: str,
        content: str,
        labels: List[str],
        author: str,
        props: Dict[str, Any] = None,
        references: List[str] = None,
        embedding: Any = None
    ) -> str:
        """Update existing node instead of creating duplicate."""
        node = self.graph.nodes[node_id] if HAS_NETWORKX else self.graph._nodes[node_id]

        # Merge props
        existing_props = node.get("props", {})
        existing_props.update(props or {})
        existing_props["title"] = title
        existing_props["content"] = content
        existing_props["summary"] = self._generate_summary(content)
        node["props"] = existing_props

        # Merge labels (union)
        existing_labels = set(node.get("labels", []))
        existing_labels.update(labels)
        node["labels"] = list(existing_labels)

        # Update memory timestamp
        memory = node.get("memory", {})
        memory["last_accessed"] = datetime.now().isoformat()
        node["memory"] = memory

        # Update embedding
        if embedding is not None and HAS_NUMPY:
            self.embeddings[node_id] = np.array(embedding)

        # Add new references
        if references:
            for ref_id in references:
                resolved = self._resolve_link(ref_id) if not self._node_exists(ref_id) else ref_id
                if resolved and not self.has_edge(node_id, resolved):
                    self.add_edge(node_id, resolved, "REFERENCES")

        return node_id

    def add_edge(
        self,
        source: str,
        target: str,
        edge_type: str,
        weight: float = 0.5,
        props: Dict[str, Any] = None
    ):
        """Adiciona aresta ao grafo."""
        if HAS_NETWORKX:
            self.graph.add_edge(
                source,
                target,
                type=edge_type,
                weight=weight,
                props=props or {},
                created_at=datetime.now().isoformat()
            )
        else:
            self.graph.add_edge(
                source,
                target,
                type=edge_type,
                weight=weight,
                props=props or {},
                created_at=datetime.now().isoformat()
            )

    def add_node_raw(self, node_id: str, labels: List[str] = None,
                     props: Dict[str, Any] = None, memory: Dict[str, Any] = None):
        """Add a synthetic node directly (for Theme, PatternCluster, etc.).

        Bypasses add_memory() — no author edge, no domain inference.
        """
        labels = labels or []
        props = props or {}
        memory = memory or {}
        now = datetime.now().isoformat()

        if not memory.get("last_accessed"):
            memory["last_accessed"] = now
        if not memory.get("created_at"):
            memory["created_at"] = now

        node_data = {
            "labels": labels,
            "props": props,
            "memory": memory
        }

        if HAS_NETWORKX:
            self.graph.add_node(node_id, **node_data)
        else:
            self.graph.add_node(node_id, **node_data)

    def _get_content_type(self, labels: List[str]) -> str:
        """[DEPRECATED] Determina tipo de conteudo pelos labels.

        No longer used — content is stored in-graph (props.content) since
        the brain-only self-feeding architecture migration.
        """
        return None

    def _save_content(
        self,
        node_id: str,
        content_type: str,
        title: str,
        content: str,
        author: str,
        labels: List[str]
    ) -> Optional[Path]:
        """[DEPRECATED] Content is now stored in-graph (props.content).

        No longer writes to disk. Returns None always.
        """
        return None

    def _generate_summary(self, content: str, max_length: int = 500) -> str:
        """Gera summary do conteudo."""
        # Remove markdown formatting
        text = re.sub(r'#+ ', '', content)
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)
        text = re.sub(r'\n+', ' ', text)
        text = text.strip()

        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."

    def _get_decay_rate(self, labels: List[str]) -> float:
        """Taxa de decay por tipo de memoria."""
        if "Decision" in labels:
            return 0.001
        elif "Pattern" in labels:
            return 0.005
        elif "Concept" in labels:
            return 0.003
        elif "Episode" in labels:
            return 0.01
        elif "Person" in labels:
            return 0.0001  # Pessoas quase nao decaem
        else:
            return 0.02

    def _ensure_person_node(self, author: str) -> str:
        """Garante que existe no para a pessoa.

        Aceita email (canonical) ou @username (legacy).
        ID do nó: person-{email} para devs reais, person-{name} para sistema.
        """
        # Resolve author para person_id
        if "@" in author and not author.startswith("@"):
            # É um email — formato canônico (ADR-010)
            person_id = f"person-{author}"
            display_name = author.split("@")[0]
        elif author.startswith("@"):
            # Legacy @username — tenta encontrar nó existente por alias
            existing = self._find_person_by_alias(author)
            if existing:
                return existing
            person_id = f"person-{author[1:]}"
            display_name = author[1:]
        else:
            person_id = f"person-{author}"
            display_name = author

        if not self._node_exists(person_id):
            now = datetime.now().isoformat()
            self.graph.add_node(
                person_id,
                labels=["Person"],
                props={
                    "email": author if "@" in author and not author.startswith("@") else "",
                    "name": display_name,
                    "aliases": [author] if author.startswith("@") else [],
                },
                memory={
                    "strength": 1.0,
                    "access_count": 0,
                    "last_accessed": now,
                    "created_at": now,
                    "decay_rate": 0.0001
                }
            )

        return person_id

    def _find_person_by_alias(self, alias: str) -> Optional[str]:
        """Busca nó Person por alias (@username)."""
        for node_id in self.graph.nodes:
            node = self.get_node(node_id)
            if node and "Person" in node.get("labels", []):
                aliases = node.get("props", {}).get("aliases", [])
                if alias in aliases:
                    return node_id
        return None

    def update_dev_state(self, email: str, focus: str = None,
                         last_session: str = None, name: str = None) -> str:
        """Atualiza estado do desenvolvedor no nó Person.

        Grava foco atual, resumo da última sessão e deriva expertise
        das edges AUTHORED_BY. Chamado pelo /learn ao final de sessão.

        Args:
            email: Email canônico do dev (git config user.email)
            focus: O que o dev está trabalhando agora
            last_session: Resumo do que foi feito na sessão
            name: Nome display (atualiza se fornecido)
        """
        person_id = self._ensure_person_node(email)
        node = self.get_node(person_id)
        if node is None:
            return person_id

        props = node.get("props", {})
        now = datetime.now().isoformat()

        if focus is not None:
            props["focus"] = focus
            props["focus_updated_at"] = now
        if last_session is not None:
            props["last_session"] = last_session
            props["last_session_at"] = now
        if name is not None:
            props["name"] = name

        # Derive expertise from AUTHORED_BY edges
        expertise = {}
        for edge_data in self.graph.edges(person_id, data=True) if HAS_NETWORKX else []:
            src, tgt, data = edge_data
            # Edges pointing TO this person are AUTHORED_BY
            pass
        # Walk all edges where tgt == person_id
        authored_nodes = []
        if HAS_NETWORKX:
            for src, tgt, data in self.graph.edges(data=True):
                if tgt == person_id and data.get("type") == "AUTHORED_BY":
                    authored_nodes.append(src)
        else:
            for e in self.graph._edges:
                if e.get("tgt") == person_id and e.get("type") == "AUTHORED_BY":
                    authored_nodes.append(e["src"])

        # Count labels from authored nodes to derive expertise areas
        from collections import Counter
        label_counts = Counter()
        for nid in authored_nodes:
            n = self.get_node(nid)
            if n:
                for label in n.get("labels", []):
                    if label.endswith("Domain"):
                        label_counts[label.replace("Domain", "")] += 1
        if label_counts:
            props["expertise"] = [area for area, _ in label_counts.most_common(10) if area]

        props["sessions_count"] = props.get("sessions_count", 0) + (1 if last_session else 0)

        # Update node
        if HAS_NETWORKX:
            self.graph.nodes[person_id]["props"] = props
            self.graph.nodes[person_id]["memory"]["last_accessed"] = now
        else:
            self.graph._nodes[person_id]["props"] = props
            self.graph._nodes[person_id]["memory"]["last_accessed"] = now

        return person_id

    def get_dev_state(self, email: str) -> Optional[Dict]:
        """Retorna estado atual do desenvolvedor.

        Útil no início de sessão para contextualizar o recall.
        """
        person_id = f"person-{email}"
        node = self.get_node(person_id)
        if node is None:
            return None
        props = node.get("props", {})
        return {
            "email": props.get("email", email),
            "name": props.get("name", ""),
            "focus": props.get("focus", ""),
            "last_session": props.get("last_session", ""),
            "last_session_at": props.get("last_session_at", ""),
            "expertise": props.get("expertise", []),
            "sessions_count": props.get("sessions_count", 0),
            "aliases": props.get("aliases", []),
        }

    def _ensure_domain_node(self, domain: str) -> str:
        """Garante que existe no para o dominio."""
        domain_id = f"domain-{domain.lower()}"

        if not self._node_exists(domain_id):
            if HAS_NETWORKX:
                self.graph.add_node(
                    domain_id,
                    labels=["Domain"],
                    props={"name": domain},
                    memory={
                        "strength": 1.0,
                        "access_count": 0,
                        "last_accessed": datetime.now().isoformat(),
                        "created_at": datetime.now().isoformat(),
                        "decay_rate": 0.0001
                    }
                )
            else:
                self.graph.add_node(
                    domain_id,
                    labels=["Domain"],
                    props={"name": domain},
                    memory={
                        "strength": 1.0,
                        "access_count": 0,
                        "last_accessed": datetime.now().isoformat(),
                        "created_at": datetime.now().isoformat(),
                        "decay_rate": 0.0001
                    }
                )

        return domain_id

    def _node_exists(self, node_id: str) -> bool:
        """Verifica se no existe."""
        if HAS_NETWORKX:
            return node_id in self.graph.nodes
        else:
            return node_id in self.graph._nodes

    def _extract_links(self, content: str) -> List[str]:
        """Extrai [[links]] do conteudo."""
        return re.findall(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', content)

    def _resolve_link(self, link: str) -> Optional[str]:
        """Resolve link para ID de no. Searches by prop, prefix, and exact title."""
        # Pessoa
        if link.startswith("@"):
            pid = f"person-{link[1:]}"
            if self._node_exists(pid):
                return pid
            return None

        # ADR-XXX: search by adr_id prop first
        if link.upper().startswith("ADR-"):
            found = self._find_node_by_prop("adr_id", link.upper())
            if found:
                return found
            # Legacy format fallback
            legacy = f"decision-{link.lower()}"
            if self._node_exists(legacy):
                return legacy

        # PAT-XXX: search by pat_id prop
        if link.upper().startswith("PAT-"):
            found = self._find_node_by_prop("pat_id", link.upper())
            if found:
                return found

        # EXP-XXX: search by exp_id prop
        if link.upper().startswith("EXP-"):
            found = self._find_node_by_prop("exp_id", link.upper())
            if found:
                return found

        # Search by title prefix (e.g. "ADR-001:" matches "ADR-001: Title")
        found = self._find_node_by_title_prefix(link)
        if found:
            return found

        # Exact title match
        for node_id in (self.graph.nodes if HAS_NETWORKX else self.graph._nodes):
            node = self.graph.nodes[node_id] if HAS_NETWORKX else self.graph._nodes[node_id]
            props = node.get("props", {})
            if props.get("title", "").lower() == link.lower():
                return node_id

        return None

    def _find_node_by_prop(self, prop_name: str, prop_value: str) -> Optional[str]:
        """Find a node by a specific property value."""
        for node_id in (self.graph.nodes if HAS_NETWORKX else self.graph._nodes):
            node = self.graph.nodes[node_id] if HAS_NETWORKX else self.graph._nodes[node_id]
            props = node.get("props", {})
            if props.get(prop_name, "").upper() == prop_value.upper():
                return node_id
        return None

    def _find_node_by_title_prefix(self, prefix: str) -> Optional[str]:
        """Find a node whose title starts with prefix."""
        prefix_lower = prefix.lower()
        for node_id in (self.graph.nodes if HAS_NETWORKX else self.graph._nodes):
            node = self.graph.nodes[node_id] if HAS_NETWORKX else self.graph._nodes[node_id]
            props = node.get("props", {})
            title = props.get("title", "").lower()
            if title.startswith(prefix_lower):
                return node_id
        return None

    def _infer_domain(self, content: str, labels: List[str]) -> Optional[str]:
        """Infere dominio do conteudo."""
        content_lower = content.lower()

        domain_keywords = {
            "auth": ["auth", "login", "jwt", "token", "password", "session", "oauth"],
            "payments": ["payment", "billing", "stripe", "invoice", "subscription"],
            "database": ["database", "sql", "postgres", "migration", "query", "index"],
            "api": ["api", "endpoint", "rest", "graphql", "request", "response"],
            "frontend": ["react", "vue", "component", "css", "html", "ui", "ux"],
            "infra": ["deploy", "docker", "kubernetes", "ci", "cd", "aws", "cloud"],
            "testing": ["test", "spec", "mock", "fixture", "coverage"]
        }

        scores = {}
        for domain, keywords in domain_keywords.items():
            score = sum(1 for kw in keywords if kw in content_lower)
            if score > 0:
                scores[domain] = score

        if scores:
            return max(scores, key=scores.get)
        return None

    # ══════════════════════════════════════════════════════════
    # RETRIEVAL (buscar conhecimento)
    # ══════════════════════════════════════════════════════════

    def search_by_embedding(
        self,
        query_embedding: Any,
        top_k: int = 10
    ) -> List[Tuple[str, float]]:
        """Busca por similaridade semantica."""
        if not HAS_NUMPY or not self.embeddings:
            return []

        query_emb = np.array(query_embedding)
        results = []

        for node_id, emb in self.embeddings.items():
            # Cosine similarity
            dot = np.dot(query_emb, emb)
            norm = np.linalg.norm(query_emb) * np.linalg.norm(emb)
            if norm > 0:
                sim = dot / norm
                results.append((node_id, float(sim)))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def spreading_activation(
        self,
        seed_nodes: List[str],
        max_depth: int = 3,
        decay: float = 0.5
    ) -> Dict[str, float]:
        """
        Spreading activation a partir de nos seed.
        Ativa vizinhos com forca decrescente.
        """
        activation = {node: 1.0 for node in seed_nodes if self._node_exists(node)}
        frontier = set(seed_nodes)

        for depth in range(max_depth):
            next_frontier = set()

            for node in frontier:
                if not self._node_exists(node):
                    continue

                current_activation = activation.get(node, 0)
                node_data = self.graph.nodes[node] if HAS_NETWORKX else self.graph._nodes.get(node, {})
                node_strength = node_data.get("memory", {}).get("strength", 1.0)

                # Propaga para vizinhos (out-edges)
                for neighbor in self.graph.successors(node):
                    if HAS_NETWORKX:
                        edge_data = self.graph.edges[node, neighbor]
                    else:
                        edge_data = self.graph._edges.get((node, neighbor), {})

                    edge_weight = edge_data.get("weight", 0.5)
                    neighbor_data = self.graph.nodes[neighbor] if HAS_NETWORKX else self.graph._nodes.get(neighbor, {})
                    neighbor_strength = neighbor_data.get("memory", {}).get("strength", 1.0)

                    new_activation = current_activation * edge_weight * decay * neighbor_strength

                    if neighbor in activation:
                        activation[neighbor] = max(activation[neighbor], new_activation)
                    else:
                        activation[neighbor] = new_activation
                        next_frontier.add(neighbor)

                # Propaga para vizinhos (in-edges)
                for neighbor in self.graph.predecessors(node):
                    if HAS_NETWORKX:
                        edge_data = self.graph.edges[neighbor, node]
                    else:
                        edge_data = self.graph._edges.get((neighbor, node), {})

                    edge_weight = edge_data.get("weight", 0.5)
                    neighbor_data = self.graph.nodes[neighbor] if HAS_NETWORKX else self.graph._nodes.get(neighbor, {})
                    neighbor_strength = neighbor_data.get("memory", {}).get("strength", 1.0)

                    new_activation = current_activation * edge_weight * decay * 0.5 * neighbor_strength

                    if neighbor in activation:
                        activation[neighbor] = max(activation[neighbor], new_activation)
                    else:
                        activation[neighbor] = new_activation
                        next_frontier.add(neighbor)

            frontier = next_frontier
            if not frontier:
                break

        return activation

    def retrieve(
        self,
        query: str = None,
        query_embedding: Any = None,
        labels: List[str] = None,
        author: str = None,
        top_k: int = 20,
        spread_depth: int = 2,
        since: str = None,
        sort_by: str = "score"
    ) -> List[Dict]:
        """
        Busca completa: embedding + spreading activation + filtros.

        Args:
            since: Ignored in JSON fallback (no temporal indexing).
            sort_by: "score" (default) or "date".
        """
        results = {}

        # 1. Busca por embedding
        if query_embedding is not None and HAS_NUMPY:
            seeds = self.search_by_embedding(query_embedding, top_k=5)
            seed_nodes = [node_id for node_id, _ in seeds]

            # Spreading activation
            activated = self.spreading_activation(seed_nodes, max_depth=spread_depth)

            for node_id, score in seeds:
                results[node_id] = score * 2  # Boost para seeds

            for node_id, act_score in activated.items():
                if node_id in results:
                    results[node_id] += act_score
                else:
                    results[node_id] = act_score

        # 2. Busca por texto simples (fallback)
        elif query:
            query_lower = query.lower()
            for node_id in (self.graph.nodes if HAS_NETWORKX else self.graph._nodes):
                node = self.graph.nodes[node_id] if HAS_NETWORKX else self.graph._nodes[node_id]
                props = node.get("props", {})

                title = props.get("title", "").lower()
                summary = props.get("summary", "").lower()
                content_text = props.get("content", "").lower()

                if query_lower in title:
                    results[node_id] = results.get(node_id, 0) + 1.0
                if query_lower in summary:
                    results[node_id] = results.get(node_id, 0) + 0.5
                if query_lower in content_text:
                    results[node_id] = results.get(node_id, 0) + 0.3

        # 3. Aplica filtros
        if labels:
            results = {
                nid: score for nid, score in results.items()
                if self._has_labels(nid, labels)
            }

        if author:
            results = {
                nid: score for nid, score in results.items()
                if self._has_author(nid, author)
            }

        # 4. Ordena e retorna
        sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)

        # 5. Reforca memorias acessadas
        for node_id, _ in sorted_results[:10]:
            self._reinforce(node_id)

        # 6. Formata resultado
        output = []
        for node_id, score in sorted_results[:top_k]:
            if self._node_exists(node_id):
                node = self.graph.nodes[node_id] if HAS_NETWORKX else self.graph._nodes[node_id]
                output.append({
                    "id": node_id,
                    "score": score,
                    **node
                })

        return output

    def _has_labels(self, node_id: str, labels: List[str]) -> bool:
        """Verifica se no tem os labels."""
        if not self._node_exists(node_id):
            return False
        node = self.graph.nodes[node_id] if HAS_NETWORKX else self.graph._nodes[node_id]
        node_labels = node.get("labels", [])
        return any(l in node_labels for l in labels)

    def _has_author(self, node_id: str, author: str) -> bool:
        """Verifica se no foi criado pelo autor."""
        if not self._node_exists(node_id):
            return False
        node = self.graph.nodes[node_id] if HAS_NETWORKX else self.graph._nodes[node_id]
        node_author = node.get("props", {}).get("author", "")
        return author.lower() in node_author.lower()

    def _reinforce(self, node_id: str):
        """Reforca memoria acessada."""
        if not self._node_exists(node_id):
            return

        node = self.graph.nodes[node_id] if HAS_NETWORKX else self.graph._nodes[node_id]
        memory = node.get("memory", {})
        memory["access_count"] = memory.get("access_count", 0) + 1
        memory["last_accessed"] = datetime.now().isoformat()
        memory["strength"] = min(1.0, memory.get("strength", 0.5) * 1.05)
        node["memory"] = memory

    # ══════════════════════════════════════════════════════════
    # CONSOLIDATION (fortalecer e compactar)
    # ══════════════════════════════════════════════════════════

    def consolidate(self) -> Dict:
        """Processo de consolidacao de memorias.

        Two steps:
        1. Strengthen existing edges between co-accessed nodes (+10%)
        2. Create CO_ACCESSED edges between nodes accessed in the same
           time window (7 days) that share no direct connection yet.
           This gives spreading activation new paths to follow.
        """
        stats = {
            "edges_strengthened": 0,
            "edges_created": 0,
            "patterns_detected": 0,
            "summaries_created": 0
        }

        recent_cutoff = datetime.now() - timedelta(days=7)

        # 1. Fortalece arestas co-ativadas recentemente
        edges_list = list(self.graph.edges) if HAS_NETWORKX else list(self.graph._edges.keys())

        for edge_key in edges_list:
            if HAS_NETWORKX:
                u, v = edge_key
                u_data = self.graph.nodes.get(u, {})
                v_data = self.graph.nodes.get(v, {})
                edge = self.graph.edges[u, v]
            else:
                u, v = edge_key
                u_data = self.graph._nodes.get(u, {})
                v_data = self.graph._nodes.get(v, {})
                edge = self.graph._edges.get((u, v), {})

            u_accessed = u_data.get("memory", {}).get("last_accessed", "")
            v_accessed = v_data.get("memory", {}).get("last_accessed", "")

            if u_accessed and v_accessed:
                try:
                    u_time = datetime.fromisoformat(u_accessed.replace('Z', '+00:00').split('+')[0])
                    v_time = datetime.fromisoformat(v_accessed.replace('Z', '+00:00').split('+')[0])

                    if u_time > recent_cutoff and v_time > recent_cutoff:
                        new_weight = min(1.0, edge.get("weight", 0.5) * 1.1)
                        edge["weight"] = new_weight
                        stats["edges_strengthened"] += 1
                except:
                    pass

        # 2. Cria arestas CO_ACCESSED entre nós co-acessados sem conexão direta
        # Coleta nós acessados recentemente (access_count >= 2 para filtrar ruído)
        recently_accessed = []
        all_node_ids = list(self.graph.nodes) if HAS_NETWORKX else list(self.graph._nodes.keys())

        for nid in all_node_ids:
            ndata = self.graph.nodes.get(nid, {}) if HAS_NETWORKX else self.graph._nodes.get(nid, {})
            memory = ndata.get("memory", {})
            accessed = memory.get("last_accessed", "")
            count = memory.get("access_count", 0)
            labels = ndata.get("labels", [])

            # Skip structural nodes (Person, Domain) — they connect to everything
            if "Person" in labels or "Domain" in labels:
                continue

            if count >= 2 and accessed:
                try:
                    t = datetime.fromisoformat(accessed.replace('Z', '+00:00').split('+')[0])
                    if t > recent_cutoff:
                        recently_accessed.append(nid)
                except:
                    pass

        # Create CO_ACCESSED edges between pairs (max 50 edges per cycle)
        created = 0
        max_new_edges = 50
        for i, nid_a in enumerate(recently_accessed):
            if created >= max_new_edges:
                break
            for nid_b in recently_accessed[i + 1:]:
                if created >= max_new_edges:
                    break
                # Only connect if no direct edge exists in either direction
                if not self.has_edge(nid_a, nid_b) and not self.has_edge(nid_b, nid_a):
                    self.add_edge(nid_a, nid_b, "CO_ACCESSED", 0.3)
                    created += 1

        stats["edges_created"] = created

        # 3. Identifica hubs
        hubs = sorted(
            self.graph.degree(),
            key=lambda x: x[1],
            reverse=True
        )[:20]

        stats["hubs"] = [(h, d) for h, d in hubs]

        return stats

    # ══════════════════════════════════════════════════════════
    # DECAY (esquecimento)
    # ══════════════════════════════════════════════════════════

    def apply_decay(self) -> Dict:
        """Aplica curva de esquecimento (Ebbinghaus)."""
        now = datetime.now()
        weak = []
        to_archive = []

        nodes_list = list(self.graph.nodes) if HAS_NETWORKX else list(self.graph._nodes.keys())

        for node_id in nodes_list:
            node = self.graph.nodes[node_id] if HAS_NETWORKX else self.graph._nodes[node_id]
            memory = node.get("memory", {})

            last_accessed = memory.get("last_accessed")
            if not last_accessed:
                continue

            try:
                last_time = datetime.fromisoformat(last_accessed.replace('Z', '+00:00').split('+')[0])
                days_since = (now - last_time).days
                decay_rate = memory.get("decay_rate", 0.01)

                # Ebbinghaus: strength = e^(-decay * time)
                decay_factor = math.exp(-decay_rate * days_since)
                new_strength = memory.get("strength", 1.0) * decay_factor

                memory["strength"] = new_strength
                node["memory"] = memory

                labels = node.get("labels", [])

                if new_strength < 0.1:
                    to_archive.append(node_id)
                elif new_strength < 0.3:
                    weak.append(node_id)
                    if "WeakMemory" not in labels:
                        node["labels"] = labels + ["WeakMemory"]
                else:
                    if "WeakMemory" in labels:
                        node["labels"] = [l for l in labels if l != "WeakMemory"]
            except Exception as e:
                pass

        return {
            "weak_count": len(weak),
            "archive_count": len(to_archive),
            "weak_nodes": weak[:10],
            "archive_nodes": to_archive[:10]
        }

    # ══════════════════════════════════════════════════════════
    # QUERIES UTEIS
    # ══════════════════════════════════════════════════════════

    def get_by_label(self, label: str) -> List[str]:
        """Retorna nos com determinado label."""
        result = []
        nodes_iter = self.graph.nodes if HAS_NETWORKX else self.graph._nodes

        for node_id in nodes_iter:
            node = self.graph.nodes[node_id] if HAS_NETWORKX else self.graph._nodes[node_id]
            if label in node.get("labels", []):
                result.append(node_id)

        return result

    def get_node(self, node_id: str) -> Optional[Dict]:
        """Retorna no pelo ID."""
        if not self._node_exists(node_id):
            return None

        if HAS_NETWORKX:
            return dict(self.graph.nodes[node_id])
        else:
            return dict(self.graph._nodes[node_id])

    def get_neighbors(self, node_id: str, edge_type: str = None) -> List[str]:
        """Retorna vizinhos de um no."""
        neighbors = []

        for neighbor in self.graph.successors(node_id):
            if edge_type is None:
                neighbors.append(neighbor)
            else:
                if HAS_NETWORKX:
                    if self.graph.edges[node_id, neighbor].get("type") == edge_type:
                        neighbors.append(neighbor)
                else:
                    if self.graph._edges.get((node_id, neighbor), {}).get("type") == edge_type:
                        neighbors.append(neighbor)

        return neighbors

    def get_predecessors(self, node_id: str, edge_type: str = None) -> List[str]:
        """Return predecessors of a node."""
        predecessors = []
        for neighbor in self.graph.predecessors(node_id):
            if edge_type is None:
                predecessors.append(neighbor)
            else:
                if HAS_NETWORKX:
                    if self.graph.edges[neighbor, node_id].get("type") == edge_type:
                        predecessors.append(neighbor)
                else:
                    if self.graph._edges.get((neighbor, node_id), {}).get("type") == edge_type:
                        predecessors.append(neighbor)
        return predecessors

    def get_all_nodes(self) -> Dict[str, Dict]:
        """Return all nodes as {id: data} dict."""
        result = {}
        nodes_iter = self.graph.nodes if HAS_NETWORKX else self.graph._nodes
        for node_id in nodes_iter:
            result[node_id] = self.graph.nodes[node_id] if HAS_NETWORKX else self.graph._nodes[node_id]
        return result

    def has_edge(self, source: str, target: str, edge_type: str = None) -> bool:
        """Check if an edge exists between source and target."""
        if HAS_NETWORKX:
            if not self.graph.has_edge(source, target):
                return False
            if edge_type:
                return self.graph.edges[source, target].get("type") == edge_type
            return True
        else:
            key = (source, target)
            if key not in self.graph._edges:
                return False
            if edge_type:
                return self.graph._edges[key].get("type") == edge_type
            return True

    def get_edge(self, source: str, target: str) -> Optional[Dict]:
        """Get edge data between two nodes."""
        if HAS_NETWORKX:
            if self.graph.has_edge(source, target):
                return dict(self.graph.edges[source, target])
            return None
        else:
            key = (source, target)
            if key in self.graph._edges:
                return dict(self.graph._edges[key])
            return None

    def remove_node(self, node_id: str):
        """Remove a node and all its edges from the graph."""
        if not self._node_exists(node_id):
            return
        if HAS_NETWORKX:
            self.graph.remove_node(node_id)
        else:
            # Remove edges
            to_remove = []
            for (u, v) in list(self.graph._edges.keys()):
                if u == node_id or v == node_id:
                    to_remove.append((u, v))
            for key in to_remove:
                del self.graph._edges[key]
            # Remove from adjacency
            self.graph._adj_out.pop(node_id, None)
            self.graph._adj_in.pop(node_id, None)
            for nid in list(self.graph._adj_out.keys()):
                if node_id in self.graph._adj_out[nid]:
                    self.graph._adj_out[nid].remove(node_id)
            for nid in list(self.graph._adj_in.keys()):
                if node_id in self.graph._adj_in[nid]:
                    self.graph._adj_in[nid].remove(node_id)
            # Remove node
            del self.graph._nodes[node_id]
        # Remove embedding
        self.embeddings.pop(node_id, None)

    def get_edges_by_type(self, edge_type: str) -> List[Tuple[str, str, Dict]]:
        """Return all edges of a specific type."""
        result = []
        if HAS_NETWORKX:
            for u, v in self.graph.edges:
                edata = self.graph.edges[u, v]
                if edata.get("type") == edge_type:
                    result.append((u, v, dict(edata)))
        else:
            for (u, v), edata in self.graph._edges.items():
                if edata.get("type") == edge_type:
                    result.append((u, v, dict(edata)))
        return result

    def get_stats(self) -> Dict:
        """Estatisticas do cerebro."""
        node_count = self.graph.number_of_nodes()
        edge_count = self.graph.number_of_edges()

        # Conta por label
        label_counts = {}
        nodes_iter = self.graph.nodes if HAS_NETWORKX else self.graph._nodes
        for node_id in nodes_iter:
            node = self.graph.nodes[node_id] if HAS_NETWORKX else self.graph._nodes[node_id]
            for label in node.get("labels", []):
                label_counts[label] = label_counts.get(label, 0) + 1

        # Conta memorias fracas
        weak_count = label_counts.get("WeakMemory", 0)

        # Conta por tipo de aresta
        edge_type_counts = {}
        if HAS_NETWORKX:
            for u, v in self.graph.edges:
                etype = self.graph.edges[u, v].get("type", "UNKNOWN")
                edge_type_counts[etype] = edge_type_counts.get(etype, 0) + 1
        else:
            for (u, v), edata in self.graph._edges.items():
                etype = edata.get("type", "UNKNOWN")
                edge_type_counts[etype] = edge_type_counts.get(etype, 0) + 1

        structural_types = {"AUTHORED_BY", "BELONGS_TO"}
        semantic_edges = sum(v for k, v in edge_type_counts.items() if k not in structural_types)

        return {
            "nodes": node_count,
            "edges": edge_count,
            "semantic_edges": semantic_edges,
            "embeddings": len(self.embeddings),
            "by_label": label_counts,
            "by_edge_type": edge_type_counts,
            "weak_memories": weak_count,
            "avg_degree": sum(d for _, d in self.graph.degree()) / max(1, node_count)
        }


# ══════════════════════════════════════════════════════════
# UTILITARIOS
# ══════════════════════════════════════════════════════════

def get_current_developer() -> Dict[str, str]:
    """Obtem identidade do desenvolvedor atual via git config.

    Retorna email como identificador canônico (ADR-010).
    O campo 'author' é o que deve ser passado para add_memory().
    """
    try:
        email = subprocess.check_output(
            ["git", "config", "user.email"],
            text=True,
            stderr=subprocess.DEVNULL
        ).strip()

        name = subprocess.check_output(
            ["git", "config", "user.name"],
            text=True,
            stderr=subprocess.DEVNULL
        ).strip()
    except:
        import getpass
        email = f"{getpass.getuser()}@local"
        name = getpass.getuser()

    return {
        "email": email,
        "name": name,
        "author": email,  # canonical — usar em add_memory()
    }


# ══════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    from brain_sqlite import BrainSQLite
    brain = BrainSQLite()

    if len(sys.argv) < 2:
        print("Usage: brain.py <command> [args]")
        print("Commands: load, save, stats, search, consolidate, decay")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "load":
        brain.load()
        print(json.dumps(brain.get_stats(), indent=2))

    elif cmd == "save":
        brain.load()
        brain.save()

    elif cmd == "stats":
        brain.load()
        print(json.dumps(brain.get_stats(), indent=2))

    elif cmd == "search":
        if len(sys.argv) < 3:
            print("Usage: brain.py search <query>")
            sys.exit(1)

        brain.load()
        query = " ".join(sys.argv[2:])
        results = brain.retrieve(query=query, top_k=10)

        for r in results:
            print(f"{r['score']:.2f} | {r.get('props', {}).get('title', 'N/A')} | {r['id']}")

    elif cmd == "consolidate":
        brain.load()
        stats = brain.consolidate()
        brain.save()
        print(json.dumps(stats, indent=2))

    elif cmd == "decay":
        brain.load()
        stats = brain.apply_decay()
        brain.save()
        print(json.dumps(stats, indent=2))

    elif cmd == "add":
        if len(sys.argv) < 4:
            print("Usage: brain.py add <title> <content>")
            sys.exit(1)

        brain.load()
        dev = get_current_developer()

        title = sys.argv[2]
        content = " ".join(sys.argv[3:])

        node_id = brain.add_memory(
            title=title,
            content=content,
            labels=["Episode"],
            author=dev["author"]
        )

        brain.save()
        print(f"Created: {node_id}")

    elif cmd == "dev-state":
        brain.load()
        dev = get_current_developer()
        state = brain.get_dev_state(dev["email"])
        if state:
            print(json.dumps(state, indent=2, ensure_ascii=False))
        else:
            print(f"No state found for {dev['email']}")

    elif cmd == "update-dev-state":
        if len(sys.argv) < 3:
            print("Usage: brain.py update-dev-state --focus 'text' --session 'text'")
            sys.exit(1)
        brain.load()
        dev = get_current_developer()
        focus = None
        session = None
        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == "--focus" and i + 1 < len(sys.argv):
                focus = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--session" and i + 1 < len(sys.argv):
                session = sys.argv[i + 1]
                i += 2
            else:
                i += 1
        brain.update_dev_state(dev["email"], focus=focus, last_session=session, name=dev["name"])
        brain.save()
        print(json.dumps(brain.get_dev_state(dev["email"]), indent=2, ensure_ascii=False))

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
