import os
from typing import Any, Dict, List
from backend.documents.pdf_processor import pdf_processor
from backend.rag.chunker import chunker
from backend.rag.embeddings import get_embedder
from backend.rag.vector_store import vector_store


class KnowledgeIngestionEngine:
    """
    Ingests local industrial knowledge base documents (PDFs, Markdown, text) into vector store.
    Operates 100% on-premise without cloud transmission.
    """

    SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".json"}

    def __init__(self, store=None, embedder=None):
        self.store = store or vector_store
        self.embedder = embedder or get_embedder()

    def ingest_directory(self, directory_path: str, force_reindex: bool = False) -> Dict[str, Any]:
        """
        Scan directory, parse documents, chunk, generate embeddings, and index into vector store.
        """
        if not os.path.exists(directory_path):
            os.makedirs(directory_path, exist_ok=True)

        if force_reindex:
            self.store.clear()

        all_chunks: List[Dict[str, Any]] = []
        documents_processed = 0

        for root, _, files in os.walk(directory_path):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext not in self.SUPPORTED_EXTENSIONS:
                    continue

                file_path = os.path.join(root, file)
                try:
                    chunks = self.process_file(file_path, file)
                    all_chunks.extend(chunks)
                    documents_processed += 1
                except Exception as exc:
                    print(f"Error processing {file}: {exc}")

        # Generate embeddings and index
        if all_chunks:
            texts = [c["content"] for c in all_chunks]
            embeddings = self.embedder.embed_texts(texts)
            self.store.add_documents(all_chunks, embeddings)

        return {
            "status": "success",
            "documents_indexed": documents_processed,
            "chunks_created": len(all_chunks),
            "total_indexed_chunks": self.store.count(),
            "message": f"Successfully indexed {documents_processed} document(s) into local vector store."
        }

    def process_file(self, file_path: str, filename: str) -> List[Dict[str, Any]]:
        """Parse single file and return chunked items."""
        ext = os.path.splitext(filename)[1].lower()

        if ext == ".pdf":
            pdf_data = pdf_processor.process_pdf(file_path)
            file_chunks = []
            for p in pdf_data["pages_data"]:
                page_chunks = chunker.chunk_text(
                    text=p["text"],
                    document_name=filename,
                    page=p["page"],
                    metadata={"source_path": file_path, "total_pages": pdf_data["pages"]}
                )
                file_chunks.extend(page_chunks)
            return file_chunks

        elif ext in (".txt", ".md", ".json"):
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            return chunker.chunk_text(
                text=text,
                document_name=filename,
                page=1,
                metadata={"source_path": file_path}
            )

        return []


ingestion_engine = KnowledgeIngestionEngine()
