from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Relationship:
    source: str
    relationship: str
    target: str
    target_type: str

    def as_dict(self) -> dict[str, str]:
        return {
            "source": self.source,
            "relationship": self.relationship,
            "target": self.target,
            "target_type": self.target_type,
        }


_RELATIONSHIPS = (
    Relationship("P-101", "DRIVEN_BY", "M-101", "Motor"),
    Relationship("P-101", "MONITORED_BY", "S-101", "Sensor"),
    Relationship("P-101", "CONNECTED_TO", "L-204", "Pipeline"),
)


class AssetGraph:
    """Query the demo asset graph locally or through Neo4j.

    The local mode keeps development and tests independent from Docker. Set
    NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD to use Neo4j instead.
    """

    def __init__(self) -> None:
        self._driver = None
        self.backend = "memory"
        uri = os.getenv("NEO4J_URI")
        username = os.getenv("NEO4J_USERNAME", "neo4j")
        password = os.getenv("NEO4J_PASSWORD")
        if uri and password:
            from neo4j import GraphDatabase

            self._driver = GraphDatabase.driver(uri, auth=(username, password))
            self.backend = "neo4j"

    @staticmethod
    def _normalize_asset_id(asset_id: str) -> str:
        normalized = asset_id.upper().replace(" ", "")
        if normalized == "P101":
            return "P-101"
        return normalized

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()

    def seed(self) -> None:
        if self._driver is None:
            return
        query = """
        MERGE (pump:Asset {asset_id: $pump_id, type: 'Pump'})
        MERGE (motor:Asset {asset_id: 'M-101', type: 'Motor'})
        MERGE (sensor:Asset {asset_id: 'S-101', type: 'Sensor'})
        MERGE (pipeline:Asset {asset_id: 'L-204', type: 'Pipeline'})
        MERGE (pump)-[:DRIVEN_BY]->(motor)
        MERGE (pump)-[:MONITORED_BY]->(sensor)
        MERGE (pump)-[:CONNECTED_TO]->(pipeline)
        """
        with self._driver.session(database=os.getenv("NEO4J_DATABASE", "neo4j")) as session:
            session.run(query, pump_id="P-101").consume()

    def relationships(self, asset_id: str) -> list[dict[str, str]]:
        normalized = self._normalize_asset_id(asset_id)
        if self._driver is None:
            return [item.as_dict() for item in _RELATIONSHIPS if item.source == normalized]

        query = """
        MATCH (source:Asset {asset_id: $asset_id})-[relation]->(target:Asset)
        RETURN source.asset_id AS source,
               type(relation) AS relationship,
               target.asset_id AS target,
               target.type AS target_type
        ORDER BY relationship, target
        """
        with self._driver.session(database=os.getenv("NEO4J_DATABASE", "neo4j")) as session:
            return [dict(record) for record in session.run(query, asset_id=normalized)]

    def related(self, asset_id: str, relationship: str | None = None) -> list[dict[str, str]]:
        records = self.relationships(asset_id)
        if relationship is None:
            return records
        return [record for record in records if record["relationship"] == relationship.upper()]

    def summary(self, asset_id: str) -> dict[str, Any]:
        normalized = self._normalize_asset_id(asset_id)
        records = self.relationships(normalized)
        return {
            "asset_id": normalized,
            "backend": self.backend,
            "relationships": records,
            "relationship_count": len(records),
        }