from graph.asset_graph import AssetGraph


def test_memory_graph_returns_pump_relationships() -> None:
    graph = AssetGraph()
    result = graph.summary("P101")

    assert result["asset_id"] == "P-101"
    assert result["backend"] == "memory"
    assert result["relationship_count"] == 3
    assert {item["target"] for item in result["relationships"]} == {"M-101", "S-101", "L-204"}


def test_memory_graph_supports_relationship_queries() -> None:
    graph = AssetGraph()

    assert graph.related("P-101", "DRIVEN_BY")[0]["target"] == "M-101"
    assert graph.related("P-101", "MONITORED_BY")[0]["target"] == "S-101"
    assert graph.related("P-101", "CONNECTED_TO")[0]["target"] == "L-204"