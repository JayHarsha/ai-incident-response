"""Qdrant vector store wrapper for semantic RAG search."""

import logging
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, FieldCondition, Filter, MatchValue, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

COLLECTION = "incident_knowledge_base"
VECTOR_SIZE = 384  # all-MiniLM-L6-v2 output dimension


class QdrantService:

    def __init__(self, host: str, port: int):
        self.client = QdrantClient(host=host, port=port)
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        existing = {c.name for c in self.client.get_collections().collections}
        if COLLECTION not in existing:
            self.client.create_collection(
                collection_name=COLLECTION,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )
            logger.info("Created Qdrant collection: %s", COLLECTION)

    def _get_indexed_hashes(self) -> dict[str, str]:
        """Returns {filename: content_hash} for every document already in Qdrant."""
        hashes = {}
        offset = None
        while True:
            result, next_offset = self.client.scroll(
                collection_name=COLLECTION,
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            for point in result:
                filename = point.payload.get("filename")
                content_hash = point.payload.get("content_hash")
                if filename and content_hash:
                    hashes[filename] = content_hash
            if next_offset is None:
                break
            offset = next_offset
        return hashes

    def sync_documents(self, documents: list[dict]) -> None:
        """
        Smart sync: only index new or changed files.
        Compares SHA-256 hash of each file against what is stored in Qdrant.
        Unchanged files are skipped — no re-embedding, no wasted compute.
        """
        if not documents:
            return

        indexed_hashes = self._get_indexed_hashes()
        to_index = [
            doc for doc in documents
            if indexed_hashes.get(doc["filename"]) != doc["content_hash"]
        ]

        if not to_index:
            logger.info("Knowledge base is up to date — no files changed, skipping index")
            return

        logger.info(
            "%d/%d files are new or changed — indexing",
            len(to_index), len(documents)
        )
        points = []
        for doc in to_index:
            vector = self.encoder.encode(doc["content"]).tolist()
            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload=doc,
                )
            )
        self.client.upsert(collection_name=COLLECTION, points=points)
        logger.info("Indexed %d documents into Qdrant", len(points))

    def search(self, query: str, limit: int = 5, doc_type: str | None = None) -> list[dict]:
        query_vector = self.encoder.encode(query).tolist()
        query_filter = None
        if doc_type:
            query_filter = Filter(must=[FieldCondition(key="type", match=MatchValue(value=doc_type))])

        hits = self.client.search(
            collection_name=COLLECTION,
            query_vector=query_vector,
            limit=limit,
            query_filter=query_filter,
        )
        return [
            {
                "content": h.payload.get("content", ""),
                "score": h.score,
                "source": h.payload.get("source", ""),
                "type": h.payload.get("type", ""),
            }
            for h in hits
        ]
