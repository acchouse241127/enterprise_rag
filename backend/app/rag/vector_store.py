"""ChromaDB vector store adapter using direct HTTP API (Python 3.14 compatible)."""

import httpx


class ChromaVectorStore:
    """Store vectors in ChromaDB collections via HTTP API."""

    def __init__(self, host: str, port: int, collection_prefix: str) -> None:
        self.host = host
        self.port = port
        self.collection_prefix = collection_prefix
        self.base_url = f"http://{host}:{port}/api/v2"
        self.tenant = "default_tenant"
        self.database = "default_database"

    def _collection_name(self, knowledge_base_id: int) -> str:
        return f"{self.collection_prefix}_{knowledge_base_id}"

    def _ensure_collection(self, name: str) -> tuple[str | None, str | None]:
        """Ensure collection exists, return collection_id or error."""
        # Try to get existing collection
        try:
            resp = httpx.get(
                f"{self.base_url}/tenants/{self.tenant}/databases/{self.database}/collections/{name}",
                timeout=30,
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("id"), None
        except Exception:
            pass

        # Create collection if not exists
        try:
            resp = httpx.post(
                f"{self.base_url}/tenants/{self.tenant}/databases/{self.database}/collections",
                json={
                    "name": name,
                    "metadata": {"hnsw:space": "cosine"},
                    "get_or_create": True,
                },
                timeout=30,
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                return data.get("id"), None
            return None, f"创建集合失败: {resp.status_code} {resp.text}"
        except Exception as exc:
            return None, f"创建集合异常: {exc}"

    def upsert_document_chunks(
        self,
        knowledge_base_id: int,
        document_id: int,
        chunks: list[str],
        embeddings: list[list[float]],
    ) -> tuple[bool, str | None]:
        """Upsert chunk vectors to ChromaDB."""
        if not chunks:
            return True, None
        if len(chunks) != len(embeddings):
            return False, "chunk 数量与 embedding 数量不一致"

        collection_name = self._collection_name(knowledge_base_id)
        collection_id, err = self._ensure_collection(collection_name)
        if err:
            return False, err

        ids = [f"doc{document_id}_chunk{idx}" for idx in range(len(chunks))]
        metadatas = [
            {
                "knowledge_base_id": knowledge_base_id,
                "document_id": document_id,
                "chunk_index": idx,
            }
            for idx in range(len(chunks))
        ]

        try:
            resp = httpx.post(
                f"{self.base_url}/tenants/{self.tenant}/databases/{self.database}/collections/{collection_id}/upsert",
                json={
                    "ids": ids,
                    "documents": chunks,
                    "embeddings": embeddings,
                    "metadatas": metadatas,
                },
                timeout=60,
            )
            if resp.status_code in (200, 201):
                return True, None
            return False, f"向量化失败: {resp.status_code} {resp.text}"
        except Exception as exc:
            return False, f"向量化异常: {exc}"

    def delete_document_chunks(
        self,
        knowledge_base_id: int,
        document_id: int,
    ) -> tuple[bool, str | None]:
        """Delete all chunk vectors for a specific document from ChromaDB."""
        collection_name = self._collection_name(knowledge_base_id)
        collection_id, err = self._ensure_collection(collection_name)
        if err:
            return False, err

        try:
            # Delete by metadata filter: document_id
            resp = httpx.post(
                f"{self.base_url}/tenants/{self.tenant}/databases/{self.database}/collections/{collection_id}/delete",
                json={
                    "where": {"document_id": document_id},
                },
                timeout=30,
            )
            if resp.status_code in (200, 201):
                return True, None
            return False, f"删除向量失败: {resp.status_code} {resp.text}"
        except Exception as exc:
            return False, f"删除向量异常: {exc}"

    def query_knowledge_base(
        self,
        knowledge_base_id: int,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> tuple[list[dict], str | None]:
        """Query chunk vectors from a knowledge base collection."""
        if not query_embedding:
            return [], "query embedding 不能为空"
        if top_k <= 0:
            return [], "top_k 必须大于 0"

        collection_name = self._collection_name(knowledge_base_id)
        collection_id, err = self._ensure_collection(collection_name)
        if err:
            return [], err

        try:
            resp = httpx.post(
                f"{self.base_url}/tenants/{self.tenant}/databases/{self.database}/collections/{collection_id}/query",
                json={
                    "query_embeddings": [query_embedding],
                    "n_results": top_k,
                    "include": ["documents", "metadatas", "distances"],
                },
                timeout=30,
            )
            if resp.status_code != 200:
                return [], f"查询失败: {resp.status_code} {resp.text}"

            result = resp.json()
            ids = result.get("ids", [[]])[0]
            documents = result.get("documents", [[]])[0]
            metadatas = result.get("metadatas", [[]])[0]
            distances = result.get("distances", [[]])[0]
            rows: list[dict] = []
            for idx, chunk_id in enumerate(ids):
                rows.append(
                    {
                        "chunk_id": chunk_id,
                        "content": documents[idx] if idx < len(documents) else "",
                        "metadata": metadatas[idx] if idx < len(metadatas) else {},
                        "distance": distances[idx] if idx < len(distances) else None,
                    }
                )
            return rows, None
        except Exception as exc:
            return [], f"查询异常: {exc}"

