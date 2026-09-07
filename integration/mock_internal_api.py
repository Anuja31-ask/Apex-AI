from __future__ import annotations

from fastapi import HTTPException


_ASSETS = {
    "P101": {
        "asset_id": "P-101",
        "type": "Pump",
        "location": "Unit-A",
        "motor": "M-101",
        "sensor": "S-101",
        "connected_to": ["L-204"],
        "status": "Operating",
        "access": "read-only synthetic demo data",
    }
}

_MAINTENANCE = {
    "P101": {
        "asset_id": "P-101",
        "records": [
            {"date": "2026-08-15", "action": "Bearing lubrication", "work_order": "WO-101"},
            {"date": "2026-06-10", "action": "Coupling alignment inspection", "work_order": "WO-088"},
        ],
        "access": "read-only synthetic demo data",
    }
}

_SENSORS = {
    "P101": {
        "asset_id": "P-101",
        "sensors": [{"sensor_id": "S-101", "type": "vibration", "unit": "mm/s RMS"}],
        "access": "read-only synthetic demo data",
    }
}


def _get(mapping: dict, asset_id: str) -> dict:
    normalized = asset_id.upper().replace("-", "")
    if normalized not in mapping:
        raise HTTPException(status_code=404, detail=f"Synthetic asset not found: {asset_id}")
    return mapping[normalized]


def get_asset(asset_id: str) -> dict:
    return _get(_ASSETS, asset_id)


def get_maintenance(asset_id: str) -> dict:
    return _get(_MAINTENANCE, asset_id)


def get_sensor(asset_id: str) -> dict:
    return _get(_SENSORS, asset_id)
