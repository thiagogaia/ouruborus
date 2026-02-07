#!/usr/bin/env python3
"""
cognitive.py - Processos cognitivos do cerebro

Jobs periodicos que mantem o cerebro saudavel:
- consolidate: Fortalece conexoes, detecta patterns
- decay: Aplica esquecimento (Ebbinghaus)
- archive: Move memorias fracas para arquivo

Uso:
    python cognitive.py consolidate    # Roda consolidacao
    python cognitive.py decay          # Roda decay
    python cognitive.py daily          # Roda decay (para cron diario)
    python cognitive.py weekly         # Roda consolidate (para cron semanal)
    python cognitive.py health         # Mostra saude do cerebro
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Importa o cerebro
sys.path.insert(0, str(Path(__file__).parent))

from brain_sqlite import BrainSQLite as Brain


def consolidate(brain: Brain) -> dict:
    """
    Processo de consolidacao.

    Roda semanalmente para:
    - Fortalecer arestas entre nos co-acessados
    - Detectar patterns emergentes
    - Identificar hubs de conhecimento
    """
    stats = brain.consolidate()

    # Adiciona metadata
    stats["ran_at"] = datetime.now().isoformat()
    stats["type"] = "consolidate"

    return stats


def decay(brain: Brain) -> dict:
    """
    Processo de esquecimento.

    Roda diariamente para:
    - Aplicar curva de Ebbinghaus (decay exponencial)
    - Marcar memorias fracas
    - Identificar candidatos a arquivo
    """
    stats = brain.apply_decay()

    # Adiciona metadata
    stats["ran_at"] = datetime.now().isoformat()
    stats["type"] = "decay"

    return stats


def archive(brain: Brain, threshold: float = 0.1) -> dict:
    """
    Marca memorias muito fracas como arquivadas no grafo.

    Memorias com strength < threshold recebem label 'Archived'.
    Tudo in-graph — sem gravacao em disco separada (ADR-009).
    """
    archived = []
    all_nodes = brain.get_all_nodes()

    for node_id, node in all_nodes.items():
        memory = node.get("memory", {})
        strength = memory.get("strength", 1.0)
        labels = node.get("labels", [])

        # Nao arquiva pessoas, dominios, decisions
        protected_labels = ["Person", "Domain", "Decision"]
        if any(l in labels for l in protected_labels):
            continue

        if "Archived" in labels:
            continue

        if strength < threshold:
            new_labels = labels + ["Archived"]
            # Update via backend-appropriate method
            if hasattr(brain, '_add_labels'):
                # SQLite v2 — normalized node_labels table
                brain._add_labels(node_id, ["Archived"])
                brain._get_conn().commit()
            else:
                brain.graph.nodes[node_id]["labels"] = new_labels
            archived.append(node_id)

    return {
        "archived_count": len(archived),
        "archived_nodes": archived[:20],
        "ran_at": datetime.now().isoformat(),
        "type": "archive"
    }


def sleep(brain: Brain, phases: list = None) -> dict:
    """
    Run brain sleep cycle for semantic consolidation.
    """
    try:
        from sleep import run_sleep
        stats = run_sleep(brain, phases)
        stats["ran_at"] = datetime.now().isoformat()
        stats["type"] = "sleep"
        return stats
    except ImportError as e:
        return {"error": f"sleep.py not available: {e}", "type": "sleep"}


def health_check(brain: Brain) -> dict:
    """
    Verifica saude do cerebro.

    Score composition:
    - 30% weak memory ratio (fewer weak = better)
    - 40% semantic connectivity (more semantic edges = better)
    - 30% embedding coverage

    Also reports:
    - Code coverage: number of Code nodes (Module, Class, Function, Interface)
    - Diff enrichment: percentage of Commit nodes with diff_enriched_at
    """
    stats = brain.get_stats()

    total_nodes = stats.get("nodes", 0)
    total_edges = stats.get("edges", 0)
    weak_count = stats.get("weak_memories", 0)
    semantic_edges = stats.get("semantic_edges", 0)
    embeddings_count = stats.get("embeddings", 0)

    if total_nodes == 0:
        health_score = 1.0
    else:
        # 30% - Weak memory ratio
        weak_score = 1.0 - (weak_count / total_nodes)

        # 40% - Semantic connectivity
        # Target: at least 1 semantic edge per content node
        content_nodes = total_nodes - stats.get("by_label", {}).get("Person", 0) - stats.get("by_label", {}).get("Domain", 0)
        if content_nodes > 0:
            semantic_ratio = min(1.0, semantic_edges / content_nodes)
        else:
            semantic_ratio = 0.0

        # 30% - Embedding coverage
        if total_nodes > 0:
            embed_score = min(1.0, embeddings_count / total_nodes)
        else:
            embed_score = 0.0

        health_score = (weak_score * 0.3) + (semantic_ratio * 0.4) + (embed_score * 0.3)

    # Classifica saude
    if health_score >= 0.8:
        status = "healthy"
    elif health_score >= 0.5:
        status = "needs_attention"
    else:
        status = "critical"

    # Code coverage report
    by_label = stats.get("by_label", {})
    code_coverage = {
        "modules": by_label.get("Module", 0),
        "classes": by_label.get("Class", 0),
        "functions": by_label.get("Function", 0),
        "interfaces": by_label.get("Interface", 0),
        "total_code_nodes": sum(by_label.get(l, 0) for l in ("Module", "Class", "Function", "Interface")),
    }

    # Diff enrichment report
    commit_count = by_label.get("Commit", 0)
    enriched_count = 0
    if commit_count > 0:
        try:
            conn = brain._get_conn()
            row = conn.execute(
                """SELECT COUNT(*) AS cnt FROM nodes n
                   JOIN node_labels nl ON n.id = nl.node_id
                   WHERE nl.label = 'Commit'
                   AND json_extract(n.properties, '$.diff_enriched_at') IS NOT NULL"""
            ).fetchone()
            enriched_count = row["cnt"] if row else 0
        except Exception:
            pass

    diff_enrichment = {
        "total_commits": commit_count,
        "enriched_commits": enriched_count,
        "enrichment_pct": round(enriched_count / commit_count * 100, 1) if commit_count > 0 else 0,
    }

    return {
        **stats,
        "health_score": round(health_score, 2),
        "status": status,
        "code_coverage": code_coverage,
        "diff_enrichment": diff_enrichment,
        "recommendations": get_recommendations(stats, health_score, code_coverage, diff_enrichment)
    }


def get_recommendations(stats: dict, health_score: float,
                        code_coverage: dict = None, diff_enrichment: dict = None) -> list:
    """Gera recomendacoes baseadas no estado do cerebro."""
    recommendations = []

    weak_count = stats.get("weak_memories", 0)
    total_nodes = stats.get("nodes", 0)
    embeddings_count = stats.get("embeddings", 0)
    semantic_edges = stats.get("semantic_edges", 0)

    if weak_count > total_nodes * 0.3:
        recommendations.append({
            "type": "archive",
            "message": f"{weak_count} memorias fracas. Considere rodar 'cognitive.py archive'."
        })

    if embeddings_count < total_nodes * 0.5:
        recommendations.append({
            "type": "embeddings",
            "message": f"Apenas {embeddings_count}/{total_nodes} nos tem embeddings. Rode 'embeddings.py build'."
        })

    vector_backend = stats.get("vector_backend", "none")
    if vector_backend == "npz":
        recommendations.append({
            "type": "vector_store",
            "message": "Usando npz fallback (brute-force O(n)). Instale chromadb para HNSW O(log n): pip install chromadb pydantic-settings"
        })

    if total_nodes > 0 and semantic_edges < total_nodes * 0.5:
        recommendations.append({
            "type": "sleep",
            "message": f"Apenas {semantic_edges} arestas semanticas para {total_nodes} nos. Rode 'sleep.py' para consolidar."
        })

    if total_nodes > 0 and stats.get("avg_degree", 0) < 2:
        recommendations.append({
            "type": "connections",
            "message": "Grafo pouco conectado. Rode 'sleep.py connect' ou adicione [[links]]."
        })

    # Code coverage recommendations
    if code_coverage:
        total_code = code_coverage.get("total_code_nodes", 0)
        if total_code == 0:
            recommendations.append({
                "type": "ast",
                "message": "Nenhum Code node encontrado. Rode 'populate.py ast' para ingerir estrutura do codigo."
            })

    # Diff enrichment recommendations
    if diff_enrichment:
        pct = diff_enrichment.get("enrichment_pct", 0)
        total_commits = diff_enrichment.get("total_commits", 0)
        if total_commits > 0 and pct < 50:
            recommendations.append({
                "type": "diffs",
                "message": f"Apenas {pct}% dos commits tem diff analysis. Rode 'populate.py diffs --unenriched' para enriquecer."
            })

    if not recommendations:
        recommendations.append({
            "type": "ok",
            "message": "Cerebro saudavel. Nenhuma acao necessaria."
        })

    return recommendations


def log_job(stats: dict, log_path: Path = None):
    """Loga resultado do job."""
    if log_path is None:
        log_path = Path(".claude/brain/cognitive-log.jsonl")

    log_path.parent.mkdir(parents=True, exist_ok=True)

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(stats, default=str) + "\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: cognitive.py <command>")
        print("Commands:")
        print("  consolidate    Run consolidation (weekly)")
        print("  decay          Run memory decay (daily)")
        print("  archive        Archive weak memories")
        print("  sleep [phase]  Run sleep cycle (semantic consolidation)")
        print("  daily          Alias for decay")
        print("  weekly         Alias for consolidate")
        print("  health         Show brain health")
        sys.exit(1)

    cmd = sys.argv[1]

    brain = Brain()
    brain.load()

    if cmd in ["consolidate", "weekly"]:
        print("Running consolidation...")
        stats = consolidate(brain)
        brain.save()
        log_job(stats)
        print(json.dumps(stats, indent=2))

    elif cmd in ["decay", "daily"]:
        print("Running memory decay...")
        stats = decay(brain)
        brain.save()
        log_job(stats)
        print(json.dumps(stats, indent=2))

    elif cmd == "archive":
        print("Archiving weak memories...")
        stats = archive(brain)
        brain.save()
        log_job(stats)
        print(json.dumps(stats, indent=2))

    elif cmd == "sleep":
        phases = sys.argv[2:] if len(sys.argv) > 2 else None
        print(f"Running sleep cycle{f' ({phases})' if phases else ''}...")
        stats = sleep(brain, phases)
        brain.save()
        log_job(stats)
        print(json.dumps(stats, indent=2))

    elif cmd == "health":
        print("Checking brain health...")
        stats = health_check(brain)
        print(json.dumps(stats, indent=2))

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
