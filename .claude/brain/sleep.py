#!/usr/bin/env python3
"""
sleep.py - Brain consolidation cycle ("sleep phases")

Inspired by biological sleep, this script runs 5 phases of consolidation
to transform the brain from a star topology (all structural edges) into
a rich semantic network.

Phases:
  1. dedup    - Find and merge duplicate nodes
  2. connect  - Parse content, discover cross-references (ADR/PAT/EXP/wikilinks)
  3. relate   - Cosine similarity between embeddings -> RELATED_TO edges
  4. themes   - Group commits by scope, create Theme nodes
  5. calibrate - Adjust edge weights by access patterns

Usage:
    python3 sleep.py              # Run full cycle
    python3 sleep.py connect      # Run single phase
    python3 sleep.py dedup connect # Run specific phases
"""

import json
import re
import sys
import hashlib
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional

sys.path.insert(0, str(Path(__file__).parent))

from brain_sqlite import BrainSQLite as Brain, HAS_NUMPY

if HAS_NUMPY:
    import numpy as np


def _update_node_labels(brain, node_id: str, labels: list):
    """Update a node's labels via the appropriate backend."""
    if hasattr(brain, '_set_labels'):
        # SQLite v2 backend — normalized node_labels table
        brain._set_labels(node_id, labels)
        brain._get_conn().commit()
    else:
        # JSON backend — direct graph mutation (used in tests)
        try:
            node = brain.graph.nodes[node_id]
        except (KeyError, TypeError):
            node = brain.graph._nodes.get(node_id)
        if node:
            node["labels"] = labels


# ══════════════════════════════════════════════════════════
# PHASE 1: DEDUP
# ══════════════════════════════════════════════════════════

def phase_dedup(brain: Brain) -> Dict:
    """Find and merge duplicate nodes.

    Duplicates are detected by:
    - Same title (case-insensitive)
    - Same adr_id/pat_id/exp_id/commit_hash prop
    """
    stats = {"merged": 0, "removed": []}
    all_nodes = brain.get_all_nodes()

    # Group by title
    by_title: Dict[str, List[str]] = defaultdict(list)
    for nid, ndata in all_nodes.items():
        title = ndata.get("props", {}).get("title", "").lower().strip()
        if title:
            by_title[title].append(nid)

    # Group by prop keys
    prop_keys = ["adr_id", "pat_id", "exp_id", "commit_hash"]
    for pkey in prop_keys:
        by_prop: Dict[str, List[str]] = defaultdict(list)
        for nid, ndata in all_nodes.items():
            val = ndata.get("props", {}).get(pkey)
            if val:
                by_prop[val].append(nid)
        # Merge into by_title groups
        for val, nids in by_prop.items():
            if len(nids) > 1:
                key = f"_prop_{pkey}_{val}"
                by_title[key] = nids

    # Merge duplicates: keep the one with most edges, absorb others
    for key, nids in by_title.items():
        if len(nids) <= 1:
            continue

        # Pick survivor: most edges wins
        best_id = None
        best_degree = -1
        for nid in nids:
            if not brain._node_exists(nid):
                continue
            degree = len(brain.get_neighbors(nid)) + len(brain.get_predecessors(nid))
            if degree > best_degree:
                best_degree = degree
                best_id = nid

        if not best_id:
            continue

        # Absorb others into survivor
        for nid in nids:
            if nid == best_id or not brain._node_exists(nid):
                continue

            # Transfer incoming edges
            for pred in list(brain.get_predecessors(nid)):
                if pred != best_id and not brain.has_edge(pred, best_id):
                    edge = brain.get_edge(pred, nid)
                    if edge:
                        brain.add_edge(pred, best_id, edge.get("type", "REFERENCES"), edge.get("weight", 0.5))

            # Transfer outgoing edges
            for succ in list(brain.get_neighbors(nid)):
                if succ != best_id and not brain.has_edge(best_id, succ):
                    edge = brain.get_edge(nid, succ)
                    if edge:
                        brain.add_edge(best_id, succ, edge.get("type", "REFERENCES"), edge.get("weight", 0.5))

            # Merge labels — use API for SQLite compat
            survivor = brain.get_node(best_id)
            victim = brain.get_node(nid)
            if survivor and victim:
                merged_labels = list(set(survivor.get("labels", []) + victim.get("labels", [])))
                _update_node_labels(brain, best_id, merged_labels)

            brain.remove_node(nid)
            stats["merged"] += 1
            stats["removed"].append(nid)

    return stats


# ══════════════════════════════════════════════════════════
# PHASE 2: CONNECT
# ══════════════════════════════════════════════════════════

def _extract_all_refs(text: str) -> List[str]:
    """Extract all reference patterns from text."""
    refs = []
    # ADR-NNN
    for m in re.finditer(r'\bADR-(\d+)\b', text, re.IGNORECASE):
        refs.append(f"ADR-{m.group(1).zfill(3)}")
    # PAT-NNN
    for m in re.finditer(r'\bPAT-(\d+)\b', text, re.IGNORECASE):
        refs.append(f"PAT-{m.group(1).zfill(3)}")
    # EXP-NNN
    for m in re.finditer(r'\bEXP-(\d+)\b', text, re.IGNORECASE):
        refs.append(f"EXP-{m.group(1).zfill(3)}")
    # [[wikilinks]]
    for m in re.finditer(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', text):
        refs.append(m.group(1).strip())
    return list(set(refs))


def _read_node_content(brain: Brain, props: dict) -> str:
    """Read full content for a node from in-graph storage.

    Content is stored directly in props.content (brain-only architecture).
    Falls back to summary for legacy nodes without content.
    """
    return props.get("content", "") or props.get("summary", "")


def _parse_knowledge_from_graph(brain: Brain) -> Dict[str, List[str]]:
    """Extract cross-references from all nodes' in-graph content.

    Reads props.content from every node in the graph and extracts
    ADR/PAT/EXP/wikilink references. Zero disk I/O.

    Returns: {node_id: [ref_strings]} mapping graph nodes to their refs.
    """
    refs_by_node: Dict[str, List[str]] = {}
    all_nodes = brain.get_all_nodes()

    for nid, ndata in all_nodes.items():
        props = ndata.get("props", {})
        content = props.get("content", "")
        if not content:
            continue

        # Extract self-ID to exclude self-references
        self_ids = set()
        for key in ("adr_id", "pat_id", "exp_id", "rule_id"):
            val = props.get(key)
            if val:
                self_ids.add(val)
        title = props.get("title", "")
        m = re.match(r'^((?:ADR|PAT|EXP|RN)-\d+)', title)
        if m:
            self_ids.add(m.group(1))

        refs = _extract_all_refs(content)
        external = [r for r in refs if r not in self_ids]
        if external:
            refs_by_node[nid] = external

    return refs_by_node


def phase_connect(brain: Brain) -> Dict:
    """Parse all node content (in-graph) and create cross-reference edges.

    All content is read from props.content — zero disk I/O.

    Creates edge types:
    - REFERENCES: explicit ADR/PAT/EXP/wikilink references
    - INFORMED_BY: Pattern -> ADR (when pattern mentions ADR)
    - APPLIES: Commit -> Pattern (when commit mentions pattern)
    - SAME_SCOPE: Commit <-> Commit with same scope
    - MODIFIES_SAME: Commit <-> Commit that touch same files
    """
    stats = {"references": 0, "informed_by": 0, "applies": 0, "same_scope": 0, "modifies_same": 0}
    all_nodes = brain.get_all_nodes()

    def _create_ref_edge(source_nid, source_labels, target_nid):
        """Create a typed reference edge between source and target."""
        if brain.has_edge(source_nid, target_nid):
            return False
        target_node = brain.get_node(target_nid)
        target_labels = target_node.get("labels", []) if target_node else []

        if "Pattern" in source_labels and "ADR" in target_labels:
            brain.add_edge(source_nid, target_nid, "INFORMED_BY", 0.7)
            stats["informed_by"] += 1
        elif "Commit" in source_labels and "Pattern" in target_labels:
            brain.add_edge(source_nid, target_nid, "APPLIES", 0.6)
            stats["applies"] += 1
        else:
            brain.add_edge(source_nid, target_nid, "REFERENCES", 0.6)
            stats["references"] += 1
        return True

    # Pass 1a: Explicit references from in-graph content
    for nid, ndata in all_nodes.items():
        props = ndata.get("props", {})
        labels = ndata.get("labels", [])
        content = _read_node_content(brain, props)
        text = f"{props.get('title', '')} {content}"

        refs = _extract_all_refs(text)
        for ref in refs:
            target = brain._resolve_link(ref)
            if target and target != nid:
                _create_ref_edge(nid, labels, target)

    # Pass 1b: Cross-references from in-graph content
    # Extracts refs from props.content of all nodes (zero disk I/O)
    knowledge_refs = _parse_knowledge_from_graph(brain)
    for source_nid, refs in knowledge_refs.items():
        source_node = brain.get_node(source_nid)
        source_labels = source_node.get("labels", []) if source_node else []
        for ref in refs:
            # Direct node ID reference (from CURRENT_STATE co-mentions)
            if ref.startswith("__node__"):
                target = ref[8:]
            else:
                target = brain._resolve_link(ref)
            if target and target != source_nid:
                _create_ref_edge(source_nid, source_labels, target)

    # Pass 2: Same scope connections between commits
    by_scope: Dict[str, List[str]] = defaultdict(list)
    for nid, ndata in all_nodes.items():
        if "Commit" not in ndata.get("labels", []):
            continue
        scope = ndata.get("props", {}).get("scope")
        if scope:
            by_scope[scope].append(nid)

    for scope, nids in by_scope.items():
        if len(nids) < 2:
            continue
        # Connect recent commits in same scope (max 5 per scope to avoid explosion)
        for i, nid_a in enumerate(nids[:5]):
            for nid_b in nids[i+1:6]:
                if not brain.has_edge(nid_a, nid_b, "SAME_SCOPE") and not brain.has_edge(nid_b, nid_a, "SAME_SCOPE"):
                    brain.add_edge(nid_a, nid_b, "SAME_SCOPE", 0.4,
                                   props={"scope": scope})
                    stats["same_scope"] += 1

    # Pass 3: Commits modifying same files
    by_file: Dict[str, List[str]] = defaultdict(list)
    for nid, ndata in all_nodes.items():
        if "Commit" not in ndata.get("labels", []):
            continue
        files = ndata.get("props", {}).get("files", [])
        if isinstance(files, list):
            for f in files:
                by_file[f].append(nid)

    for filepath, nids in by_file.items():
        if len(nids) < 2:
            continue
        # Connect commits touching same file (max 3 per file)
        for i, nid_a in enumerate(nids[:3]):
            for nid_b in nids[i+1:4]:
                if not brain.has_edge(nid_a, nid_b, "MODIFIES_SAME") and not brain.has_edge(nid_b, nid_a, "MODIFIES_SAME"):
                    brain.add_edge(nid_a, nid_b, "MODIFIES_SAME", 0.5,
                                   props={"file": filepath})
                    stats["modifies_same"] += 1

    return stats


# ══════════════════════════════════════════════════════════
# PHASE 3: RELATE (semantic similarity)
# ══════════════════════════════════════════════════════════

def _text_to_vector(text: str, vocab: Dict[str, int] = None) -> Optional[list]:
    """Simple TF vector for text (no external deps). Returns sparse vector."""
    if not text.strip():
        return None
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    if not words:
        return None

    # Use provided vocab or build from text
    if vocab is None:
        return None  # Need global vocab

    vec = [0.0] * len(vocab)
    for w in words:
        if w in vocab:
            vec[vocab[w]] += 1.0

    # Normalize
    norm = sum(v*v for v in vec) ** 0.5
    if norm > 0:
        vec = [v/norm for v in vec]
    return vec


def phase_relate(brain: Brain, threshold: float = 0.75) -> Dict:
    """Create RELATED_TO edges between semantically similar nodes.

    Uses embeddings if available, falls back to TF-IDF-like similarity.
    """
    stats = {"related_to": 0, "method": "none"}
    all_nodes = brain.get_all_nodes()

    # Collect texts for all content nodes (skip Person, Domain)
    skip_labels = {"Person", "Domain"}
    texts: Dict[str, str] = {}
    for nid, ndata in all_nodes.items():
        labels = set(ndata.get("labels", []))
        if labels & skip_labels:
            continue
        props = ndata.get("props", {})
        content = props.get("content", "") or props.get("summary", "")
        text = f"{props.get('title', '')} {content[:500]}"
        if len(text.strip()) > 10:
            texts[nid] = text

    if len(texts) < 2:
        return stats

    # Try numpy embeddings first (via get_embedding_vectors for ChromaDB compat)
    candidate_ids = list(texts.keys())
    if HAS_NUMPY and hasattr(brain, 'get_embedding_vectors'):
        emb_vectors = brain.get_embedding_vectors(candidate_ids)
    elif HAS_NUMPY:
        emb_vectors = {nid: brain.embeddings[nid] for nid in candidate_ids if nid in brain.embeddings}
    else:
        emb_vectors = {}

    if emb_vectors:
        stats["method"] = "embeddings"
        node_ids = [nid for nid in candidate_ids if nid in emb_vectors]

        if len(node_ids) >= 2:
            # Build matrix
            matrix = np.array([emb_vectors[nid] for nid in node_ids])
            # Normalize rows
            norms = np.linalg.norm(matrix, axis=1, keepdims=True)
            norms[norms == 0] = 1
            matrix = matrix / norms
            # Cosine similarity matrix
            sim_matrix = matrix @ matrix.T

            for i in range(len(node_ids)):
                for j in range(i+1, len(node_ids)):
                    if sim_matrix[i, j] >= threshold:
                        nid_a, nid_b = node_ids[i], node_ids[j]
                        if not brain.has_edge(nid_a, nid_b) and not brain.has_edge(nid_b, nid_a):
                            brain.add_edge(nid_a, nid_b, "RELATED_TO",
                                           weight=float(sim_matrix[i, j]),
                                           props={"method": "embedding"})
                            stats["related_to"] += 1

    # Fallback: TF-based similarity (only if embeddings weren't available)
    if stats["related_to"] == 0 and stats["method"] != "embeddings":
        stats["method"] = "tf_vectors"

        # Build vocabulary from all texts
        word_counts: Dict[str, int] = defaultdict(int)
        for text in texts.values():
            for w in set(re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())):
                word_counts[w] += 1

        # Filter: keep words appearing in 2+ but less than 80% of docs
        max_df = len(texts) * 0.8
        vocab_words = [w for w, c in word_counts.items() if 2 <= c <= max_df]
        if len(vocab_words) < 5:
            return stats

        vocab = {w: i for i, w in enumerate(sorted(vocab_words))}

        # Build vectors
        vectors: Dict[str, list] = {}
        for nid, text in texts.items():
            vec = _text_to_vector(text, vocab)
            if vec:
                vectors[nid] = vec

        if len(vectors) < 2:
            return stats

        # Compare pairs (only for non-huge graphs)
        node_ids = list(vectors.keys())
        if len(node_ids) > 500:
            # Sample to avoid O(n^2) explosion
            import random
            random.shuffle(node_ids)
            node_ids = node_ids[:500]

        for i in range(len(node_ids)):
            for j in range(i+1, len(node_ids)):
                nid_a, nid_b = node_ids[i], node_ids[j]
                vec_a, vec_b = vectors[nid_a], vectors[nid_b]

                # Cosine similarity
                dot = sum(a*b for a, b in zip(vec_a, vec_b))
                if dot >= threshold:
                    if not brain.has_edge(nid_a, nid_b) and not brain.has_edge(nid_b, nid_a):
                        brain.add_edge(nid_a, nid_b, "RELATED_TO",
                                       weight=dot,
                                       props={"method": "tf_vector"})
                        stats["related_to"] += 1

    return stats


# ══════════════════════════════════════════════════════════
# PHASE 4: THEMES
# ══════════════════════════════════════════════════════════

def phase_themes(brain: Brain) -> Dict:
    """Group commits by scope, create Theme nodes and PatternCluster nodes.

    Creates:
    - Theme nodes for scopes with 3+ commits
    - BELONGS_TO_THEME edges from commits to themes
    - PatternCluster nodes for patterns in same domain
    - CLUSTERED_IN edges from patterns to clusters
    """
    stats = {"themes_created": 0, "clusters_created": 0, "edges_created": 0}
    all_nodes = brain.get_all_nodes()

    # Group commits by scope
    by_scope: Dict[str, List[str]] = defaultdict(list)
    for nid, ndata in all_nodes.items():
        if "Commit" not in ndata.get("labels", []):
            continue
        scope = ndata.get("props", {}).get("scope")
        if scope:
            by_scope[scope].append(nid)

    # Create Theme nodes for scopes with 3+ commits
    for scope, commit_ids in by_scope.items():
        if len(commit_ids) < 3:
            continue

        theme_title = f"Theme: {scope}"
        theme_id_source = f"{theme_title}|Theme"
        theme_id = hashlib.md5(theme_id_source.encode()).hexdigest()[:8]

        if not brain._node_exists(theme_id):
            # Summarize the theme
            commit_types = defaultdict(int)
            for cid in commit_ids:
                cnode = brain.get_node(cid)
                if cnode:
                    ct = cnode.get("props", {}).get("commit_type", "other")
                    commit_types[ct] += 1

            summary = f"Theme '{scope}' with {len(commit_ids)} commits: " + \
                      ", ".join(f"{ct}({n})" for ct, n in sorted(commit_types.items(), key=lambda x: -x[1]))

            now = datetime.now().isoformat()

            # Use add_node_raw for synthetic nodes (works on both backends)
            if hasattr(brain, 'add_node_raw'):
                brain.add_node_raw(theme_id,
                    labels=["Theme"],
                    props={
                        "title": theme_title,
                        "scope": scope,
                        "commit_count": len(commit_ids),
                        "summary": summary
                    },
                    memory={
                        "strength": 0.8,
                        "access_count": 0,
                        "last_accessed": now,
                        "created_at": now,
                        "decay_rate": 0.002
                    })
            else:
                node_data = {
                    "labels": ["Theme"],
                    "props": {
                        "title": theme_title,
                        "scope": scope,
                        "commit_count": len(commit_ids),
                        "summary": summary
                    },
                    "memory": {
                        "strength": 0.8,
                        "access_count": 0,
                        "last_accessed": now,
                        "created_at": now,
                        "decay_rate": 0.002
                    }
                }
                brain.graph.add_node(theme_id, **node_data)

            stats["themes_created"] += 1

        # Create BELONGS_TO_THEME edges
        for cid in commit_ids:
            if brain._node_exists(cid) and not brain.has_edge(cid, theme_id):
                brain.add_edge(cid, theme_id, "BELONGS_TO_THEME", 0.6)
                stats["edges_created"] += 1

    # Group patterns by domain inference
    by_domain: Dict[str, List[str]] = defaultdict(list)
    for nid, ndata in all_nodes.items():
        if "Pattern" not in ndata.get("labels", []):
            continue
        # Find domain edge
        for succ in brain.get_neighbors(nid):
            if brain.has_edge(nid, succ, "BELONGS_TO"):
                succ_node = brain.get_node(succ)
                if succ_node and "Domain" in succ_node.get("labels", []):
                    domain = succ_node.get("props", {}).get("name", "unknown")
                    by_domain[domain].append(nid)
                    break

    # Create PatternCluster nodes for domains with 2+ patterns
    for domain, pattern_ids in by_domain.items():
        if len(pattern_ids) < 2:
            continue

        cluster_title = f"PatternCluster: {domain}"
        cluster_id_source = f"{cluster_title}|PatternCluster"
        cluster_id = hashlib.md5(cluster_id_source.encode()).hexdigest()[:8]

        if not brain._node_exists(cluster_id):
            now = datetime.now().isoformat()

            if hasattr(brain, 'add_node_raw'):
                brain.add_node_raw(cluster_id,
                    labels=["PatternCluster"],
                    props={
                        "title": cluster_title,
                        "domain": domain,
                        "pattern_count": len(pattern_ids),
                        "summary": f"Cluster of {len(pattern_ids)} patterns in '{domain}' domain"
                    },
                    memory={
                        "strength": 0.7,
                        "access_count": 0,
                        "last_accessed": now,
                        "created_at": now,
                        "decay_rate": 0.003
                    })
            else:
                node_data = {
                    "labels": ["PatternCluster"],
                    "props": {
                        "title": cluster_title,
                        "domain": domain,
                        "pattern_count": len(pattern_ids),
                        "summary": f"Cluster of {len(pattern_ids)} patterns in '{domain}' domain"
                    },
                    "memory": {
                        "strength": 0.7,
                        "access_count": 0,
                        "last_accessed": now,
                        "created_at": now,
                        "decay_rate": 0.003
                    }
                }
                brain.graph.add_node(cluster_id, **node_data)

            stats["clusters_created"] += 1

        for pid in pattern_ids:
            if brain._node_exists(pid) and not brain.has_edge(pid, cluster_id):
                brain.add_edge(pid, cluster_id, "CLUSTERED_IN", 0.5)
                stats["edges_created"] += 1

    return stats


# ══════════════════════════════════════════════════════════
# PHASE 5: CALIBRATE
# ══════════════════════════════════════════════════════════

def phase_calibrate(brain: Brain) -> Dict:
    """Adjust edge weights based on node access patterns.

    Rules:
    - Edges between frequently accessed nodes get boosted
    - Edges between never-accessed nodes get decayed
    - Semantic edges get slight boost over structural
    """
    stats = {"boosted": 0, "decayed": 0}
    structural_types = {"AUTHORED_BY", "BELONGS_TO"}

    if hasattr(brain, '_get_conn'):
        # SQLite v2 backend — batch UPDATE via SQL
        conn = brain._get_conn()
        rows = conn.execute(
            """SELECT e.id, e.type, e.weight,
                      n1.access_count AS src_access, n2.access_count AS tgt_access
               FROM edges e
               JOIN nodes n1 ON e.from_id = n1.id
               JOIN nodes n2 ON e.to_id = n2.id"""
        ).fetchall()

        for row in rows:
            etype = row["type"]
            current_weight = row["weight"]
            combined_access = row["src_access"] + row["tgt_access"]
            is_semantic = etype not in structural_types

            new_weight = current_weight
            if combined_access > 5 and is_semantic:
                new_weight = min(1.0, current_weight * 1.15)
                stats["boosted"] += 1
            elif combined_access == 0 and current_weight > 0.2:
                new_weight = max(0.1, current_weight * 0.95)
                stats["decayed"] += 1

            if new_weight != current_weight:
                conn.execute(
                    "UPDATE edges SET weight = ? WHERE id = ?",
                    (new_weight, row["id"])
                )

        conn.commit()
    else:
        # JSON backend — direct mutation
        edges_list = list(brain.graph.edges) if hasattr(brain.graph, 'has_edge') else list(brain.graph._edges.keys())

        for edge_key in edges_list:
            u, v = edge_key
            if hasattr(brain.graph, 'has_edge'):
                edge = brain.graph.edges[u, v]
            else:
                edge = brain.graph._edges.get((u, v), {})

            etype = edge.get("type", "")
            current_weight = edge.get("weight", 0.5)

            u_node = brain.get_node(u)
            v_node = brain.get_node(v)
            if not u_node or not v_node:
                continue

            u_access = u_node.get("memory", {}).get("access_count", 0)
            v_access = v_node.get("memory", {}).get("access_count", 0)
            combined_access = u_access + v_access
            is_semantic = etype not in structural_types

            if combined_access > 5 and is_semantic:
                new_weight = min(1.0, current_weight * 1.15)
                edge["weight"] = new_weight
                stats["boosted"] += 1
            elif combined_access == 0 and current_weight > 0.2:
                new_weight = max(0.1, current_weight * 0.95)
                edge["weight"] = new_weight
                stats["decayed"] += 1

    return stats


# ══════════════════════════════════════════════════════════
# ORCHESTRATOR
# ══════════════════════════════════════════════════════════

PHASES = {
    "dedup": phase_dedup,
    "connect": phase_connect,
    "relate": phase_relate,
    "themes": phase_themes,
    "calibrate": phase_calibrate
}

PHASE_ORDER = ["dedup", "connect", "relate", "themes", "calibrate"]


def run_sleep(brain: Brain, phases: List[str] = None) -> Dict:
    """Run sleep cycle (all phases or specific ones)."""
    if phases is None:
        phases = PHASE_ORDER

    results = {
        "started_at": datetime.now().isoformat(),
        "phases": {}
    }

    # Stats before
    stats_before = brain.get_stats()
    results["before"] = {
        "nodes": stats_before["nodes"],
        "edges": stats_before["edges"],
        "semantic_edges": stats_before.get("semantic_edges", 0)
    }

    for phase_name in phases:
        if phase_name not in PHASES:
            print(f"  Unknown phase: {phase_name}, skipping")
            continue

        print(f"  Phase [{phase_name}]...")
        try:
            phase_stats = PHASES[phase_name](brain)
            results["phases"][phase_name] = phase_stats
            print(f"    -> {json.dumps(phase_stats)}")
        except Exception as e:
            results["phases"][phase_name] = {"error": str(e)}
            print(f"    -> ERROR: {e}")

    # Stats after
    stats_after = brain.get_stats()
    results["after"] = {
        "nodes": stats_after["nodes"],
        "edges": stats_after["edges"],
        "semantic_edges": stats_after.get("semantic_edges", 0)
    }

    results["finished_at"] = datetime.now().isoformat()
    results["delta"] = {
        "nodes": stats_after["nodes"] - stats_before["nodes"],
        "edges": stats_after["edges"] - stats_before["edges"],
        "semantic_edges": stats_after.get("semantic_edges", 0) - stats_before.get("semantic_edges", 0)
    }

    return results


# ══════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════

if __name__ == "__main__":
    phases = None

    if len(sys.argv) > 1:
        if sys.argv[1] in ("-h", "--help"):
            print(__doc__)
            sys.exit(0)
        phases = [p for p in sys.argv[1:] if p in PHASES]
        if not phases:
            print(f"Unknown phases: {sys.argv[1:]}. Available: {', '.join(PHASE_ORDER)}")
            sys.exit(1)

    brain = Brain()
    if not brain.load():
        print("Error: Could not load brain. Run populate.py first.")
        sys.exit(1)

    print(f"=== Brain Sleep Cycle ===")
    print(f"Phases: {phases or PHASE_ORDER}")
    print()

    results = run_sleep(brain, phases)

    print()
    print(f"=== Results ===")
    print(f"Before: {results['before']['nodes']} nodes, {results['before']['edges']} edges ({results['before']['semantic_edges']} semantic)")
    print(f"After:  {results['after']['nodes']} nodes, {results['after']['edges']} edges ({results['after']['semantic_edges']} semantic)")
    print(f"Delta:  {results['delta']['nodes']:+d} nodes, {results['delta']['edges']:+d} edges ({results['delta']['semantic_edges']:+d} semantic)")

    print()
    print("Saving brain...")
    brain.save()

    # Save sleep log
    log_path = Path(".claude/brain/sleep-log.jsonl")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(results, default=str) + "\n")
    print(f"Log saved to {log_path}")
