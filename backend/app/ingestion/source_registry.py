"""
IP-SAKTI Sahayak — Source Registry
Loads and validates official Indian IP source definitions.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from app.logging_config import get_logger

logger = get_logger(__name__)

REGISTRY_PATH = Path(__file__).parent.parent.parent.parent / "data" / "metadata" / "source_registry.json"


@dataclass
class SourceEntry:
    """A single entry in the source registry."""
    id: str
    name: str
    authority: str
    authority_tier: str           # TIER_1 | TIER_2 | TIER_3
    domain: str
    document_type: str
    url: str
    description: str
    language: str = "en"
    status: str = "ACTIVE"
    alternate_urls: List[str] = field(default_factory=list)


class SourceRegistry:
    """
    Manages the registry of official Indian IP/regulatory sources.
    Loaded from data/metadata/source_registry.json.
    """

    def __init__(self, registry_path: Optional[Path] = None) -> None:
        self._path = registry_path or REGISTRY_PATH
        self._sources: Dict[str, SourceEntry] = {}
        self._loaded_at: Optional[datetime] = None
        self._load()

    def _load(self) -> None:
        """Load and parse the registry JSON file."""
        if not self._path.exists():
            logger.warning("Source registry not found", path=str(self._path))
            return

        with open(self._path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for item in data.get("sources", []):
            try:
                entry = SourceEntry(
                    id=item["id"],
                    name=item["name"],
                    authority=item["authority"],
                    authority_tier=item.get("authority_tier", "TIER_1"),
                    domain=item["domain"],
                    document_type=item["document_type"],
                    url=item["url"],
                    description=item.get("description", ""),
                    language=item.get("language", "en"),
                    status=item.get("status", "ACTIVE"),
                    alternate_urls=item.get("alternate_urls", []),
                )
                self._sources[entry.id] = entry
            except KeyError as exc:
                logger.error("Invalid source registry entry", missing_key=str(exc), item=item)

        self._loaded_at = datetime.now(timezone.utc)
        logger.info(
            "Source registry loaded",
            count=len(self._sources),
            path=str(self._path),
        )

    def get_all(self) -> List[SourceEntry]:
        """Return all active source entries."""
        return [s for s in self._sources.values() if s.status == "ACTIVE"]

    def get_by_domain(self, domain: str) -> List[SourceEntry]:
        """Return active sources for a given domain."""
        return [s for s in self.get_all() if s.domain == domain]

    def get_by_id(self, source_id: str) -> Optional[SourceEntry]:
        return self._sources.get(source_id)

    def get_by_document_type(self, doc_type: str) -> List[SourceEntry]:
        return [s for s in self.get_all() if s.document_type == doc_type]

    @property
    def domains(self) -> List[str]:
        return sorted({s.domain for s in self.get_all()})

    @property
    def count(self) -> int:
        return len(self._sources)


# Singleton instance
_registry: Optional[SourceRegistry] = None


def get_source_registry() -> SourceRegistry:
    """Return the global source registry singleton."""
    global _registry
    if _registry is None:
        _registry = SourceRegistry()
    return _registry
