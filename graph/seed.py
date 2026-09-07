from __future__ import annotations

from .asset_graph import AssetGraph


if __name__ == "__main__":
    graph = AssetGraph()
    if graph.backend != "neo4j":
        raise SystemExit("Set NEO4J_URI and NEO4J_PASSWORD before seeding Neo4j.")
    graph.seed()
    print("Seeded the APEX-AI P-101 asset graph in Neo4j.")
    graph.close()