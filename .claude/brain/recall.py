#!/usr/bin/env python3
"""
recall.py — Consulta o Cérebro Organizacional

Uso:
    python3 recall.py "como funciona a autenticação"
    python3 recall.py "arquitetura" --type ADR
    python3 recall.py "bug login" --author @thiago
    python3 recall.py "padrões" --depth 3 --top 10
"""

import argparse
import json
import sys
from pathlib import Path

# Add brain to path
BRAIN_PATH = Path(__file__).parent
sys.path.insert(0, str(BRAIN_PATH))

try:
    from brain import Brain
    HAS_DEPS = True
except ImportError as e:
    HAS_DEPS = False
    IMPORT_ERROR = str(e)

try:
    import embeddings
    HAS_EMBEDDINGS = True
except (ImportError, SystemExit):
    HAS_EMBEDDINGS = False


def search_brain(
    query: str,
    filter_type: str = None,
    filter_author: str = None,
    depth: int = 2,
    top_k: int = 10
) -> dict:
    """
    Busca no cérebro organizacional.

    Args:
        query: Pergunta ou tema para buscar
        filter_type: Filtrar por tipo (ADR, Concept, Pattern, etc)
        filter_author: Filtrar por autor (@nome)
        depth: Profundidade do spreading activation
        top_k: Número máximo de resultados

    Returns:
        Dict com query, results e total
    """
    if not HAS_DEPS:
        return {
            "error": f"Dependências não disponíveis: {IMPORT_ERROR}",
            "fallback": "Consulte .claude/knowledge/ diretamente"
        }

    brain = Brain()
    if not brain.load():
        return {
            "error": "Não foi possível carregar o cérebro",
            "fallback": "Execute /init-engram para popular o cérebro"
        }

    # Preparar filtros
    labels = None
    if filter_type:
        # Mapear tipos comuns para labels
        type_map = {
            "adr": ["ADR", "Decision"],
            "decision": ["ADR", "Decision"],
            "concept": ["Concept", "Glossary"],
            "pattern": ["Pattern", "ApprovedPattern"],
            "episode": ["Episode", "Commit", "BugFix"],
            "rule": ["Rule", "BusinessRule"],
            "person": ["Person"]
        }
        labels = type_map.get(filter_type.lower(), [filter_type])

    # Gerar embedding da query
    query_embedding = None
    if HAS_EMBEDDINGS:
        try:
            query_embedding = embeddings.get_embedding(query)
        except Exception as e:
            sys.stderr.write(f"Aviso: Usando busca textual (embedding falhou: {e})\n")

    # Executar busca
    if query_embedding is not None:
        results = brain.retrieve(
            query_embedding=query_embedding,
            labels=labels,
            author=filter_author,
            top_k=top_k,
            spread_depth=depth
        )
    else:
        results = brain.retrieve(
            query=query,
            labels=labels,
            author=filter_author,
            top_k=top_k,
            spread_depth=depth
        )

    # Persist reinforcement — closes the self-feeding loop
    # Every recall strengthens accessed memories AND saves to disk
    try:
        brain.save()
    except Exception:
        pass

    # Formatar resultados
    formatted = []
    for item in results:
        props = item.get("props", {})
        labels_list = item.get("labels", [])

        # Determinar tipo principal
        type_priority = ["ADR", "Decision", "Pattern", "Concept", "Rule", "Episode", "Commit", "Person"]
        item_type = "Memory"
        for t in type_priority:
            if t in labels_list:
                item_type = t
                break

        # Get content from in-graph storage (brain-only architecture)
        node_content = props.get("content", "")

        # Collect semantic connections for this node
        semantic_connections = []
        semantic_types = {"REFERENCES", "INFORMED_BY", "APPLIES", "RELATED_TO",
                          "SAME_SCOPE", "MODIFIES_SAME", "BELONGS_TO_THEME", "CLUSTERED_IN"}
        node_id = item.get("id", "")

        try:
            for neighbor in brain.graph.successors(node_id):
                edge = brain.get_edge(node_id, neighbor)
                if edge and edge.get("type") in semantic_types:
                    nb_node = brain.get_node(neighbor)
                    nb_title = nb_node.get("props", {}).get("title", neighbor) if nb_node else neighbor
                    semantic_connections.append({
                        "target": neighbor,
                        "title": nb_title,
                        "type": edge.get("type"),
                        "weight": round(edge.get("weight", 0.5), 2)
                    })
            for neighbor in brain.graph.predecessors(node_id):
                edge = brain.get_edge(neighbor, node_id)
                if edge and edge.get("type") in semantic_types:
                    nb_node = brain.get_node(neighbor)
                    nb_title = nb_node.get("props", {}).get("title", neighbor) if nb_node else neighbor
                    semantic_connections.append({
                        "source": neighbor,
                        "title": nb_title,
                        "type": edge.get("type"),
                        "weight": round(edge.get("weight", 0.5), 2)
                    })
        except Exception:
            pass

        # Boost score for well-connected nodes
        connection_boost = min(0.3, len(semantic_connections) * 0.05)

        formatted.append({
            "id": item.get("id"),
            "title": props.get("title", item.get("id", "Sem título")),
            "type": item_type,
            "labels": labels_list,
            "summary": props.get("summary", "")[:200],
            "content": node_content[:2000] if node_content else None,
            "score": round(item.get("score", 0) + connection_boost, 3),
            "author": props.get("author"),
            "connections": semantic_connections[:10]
        })

    # Re-sort after connection boost
    formatted.sort(key=lambda x: x["score"], reverse=True)

    return {
        "query": query,
        "filters": {
            "type": filter_type,
            "author": filter_author,
            "depth": depth
        },
        "results": formatted,
        "total": len(formatted)
    }


def format_human_readable(data: dict) -> str:
    """Formata resultado para leitura humana."""
    if "error" in data:
        return f"⚠️ Erro: {data['error']}\n💡 {data.get('fallback', '')}"

    lines = []
    lines.append(f'🧠 Recall: "{data["query"]}"')
    lines.append("═" * 50)
    lines.append("")

    if data["total"] == 0:
        lines.append("Nenhuma memória encontrada.")
        lines.append("")
        lines.append("💡 Sugestões:")
        lines.append("   - Tente termos mais genéricos")
        lines.append("   - Execute /learn para registrar conhecimento")
        lines.append("   - Verifique se o cérebro foi populado (/init-engram)")
    else:
        lines.append(f"Encontrei {data['total']} memórias relevantes:")
        lines.append("")

        for item in data["results"]:
            score_bar = "█" * int(item["score"] * 5) + "░" * (5 - int(item["score"] * 5))
            lines.append(f"📋 [{score_bar}] {item['type']}: {item['title']}")
            if item["summary"]:
                lines.append(f"   {item['summary'][:100]}...")
            if item.get("content"):
                lines.append(f"   📝 {item['content'][:200]}...")
            if item["author"]:
                lines.append(f"   👤 {item['author']}")
            # Show semantic connections
            connections = item.get("connections", [])
            if connections:
                lines.append(f"   🔗 {len(connections)} conexões:")
                for conn in connections[:5]:
                    direction = "→" if "target" in conn else "←"
                    lines.append(f"      {direction} [{conn['type']}] {conn['title']}")
            lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Consulta o Cérebro Organizacional",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python3 recall.py "como funciona a autenticação"
  python3 recall.py "arquitetura" --type ADR
  python3 recall.py "bug" --type Episode --top 5
  python3 recall.py "padrões" --format json
        """
    )

    parser.add_argument("query", help="Pergunta ou tema para buscar")
    parser.add_argument("--type", "-t", dest="filter_type",
                        help="Filtrar por tipo (ADR, Concept, Pattern, Episode, Rule)")
    parser.add_argument("--author", "-a", dest="filter_author",
                        help="Filtrar por autor (@nome)")
    parser.add_argument("--depth", "-d", type=int, default=2,
                        help="Profundidade do spreading activation (default: 2)")
    parser.add_argument("--top", "-k", type=int, default=10,
                        help="Número máximo de resultados (default: 10)")
    parser.add_argument("--format", "-f", choices=["json", "human"], default="human",
                        help="Formato de saída (default: human)")

    args = parser.parse_args()

    result = search_brain(
        query=args.query,
        filter_type=args.filter_type,
        filter_author=args.filter_author,
        depth=args.depth,
        top_k=args.top
    )

    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(format_human_readable(result))


if __name__ == "__main__":
    main()
