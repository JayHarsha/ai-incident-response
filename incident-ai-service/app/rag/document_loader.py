"""Loads markdown documents from the knowledge base into memory."""

import hashlib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class DocumentLoader:

    def __init__(self, knowledge_base_path: str):
        self.base = Path(knowledge_base_path)

    def load_all_documents(self) -> list[dict]:
        docs = (
            self._load_dir("past_incidents", "past_incident")
            + self._load_dir("runbooks", "runbook")
            + self._load_dir("architecture", "architecture")
        )
        logger.info("Loaded %d documents from knowledge base", len(docs))
        return docs

    def _load_dir(self, subdir: str, doc_type: str) -> list[dict]:
        docs = []
        folder = self.base / subdir
        if not folder.exists():
            logger.warning("Knowledge base folder not found: %s", folder)
            return docs
        for path in folder.glob("*.md"):
            try:
                content = path.read_text(encoding="utf-8")
                docs.append({
                    "content": content,
                    "type": doc_type,
                    "filename": path.name,
                    "source": str(path),
                    # SHA-256 of file content — used to detect changes since last index
                    "content_hash": hashlib.sha256(content.encode()).hexdigest(),
                })
            except Exception as e:
                logger.error("Failed to read %s: %s", path, e)
        return docs
