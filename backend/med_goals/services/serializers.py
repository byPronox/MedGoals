"""
Lightweight Adapter helpers to serialize Odoo records to JSON-friendly
structures for the API layer.
"""
from typing import Dict


class Many2OneAdapter:
    """Adapter pattern: converts Odoo many2one tuple/list into dict."""

    @staticmethod
    def to_dict(value):
        if isinstance(value, (list, tuple)) and len(value) >= 2:
            return {"id": value[0], "name": value[1]}
        return None


class RecordSerializer:
    """Centralizes recurring serialization helpers (SRP)."""

    def map_many2one(self, record: Dict, mapping: Dict[str, str]) -> Dict:
        """
        mapping example: {"employee_id": "employee"}
        pops the source key and stores the adapted value in the target key.
        """
        for source, target in mapping.items():
            record[target] = Many2OneAdapter.to_dict(record.pop(source, None))
        return record
