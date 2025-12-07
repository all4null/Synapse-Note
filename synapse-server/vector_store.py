import os
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

load_dotenv()

class VectorDBClient:
    def __init__(self):
        # Persistent storage path
        self.db_path = os.path.join(os.path.dirname(__file__), "chroma_db")
        
        # Initialize Client
        self.client = chromadb.PersistentClient(path=self.db_path)
        
        # OpenAI Embedding Function
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("Warning: OPENAI_API_KEY not found. Embeddings will fail.")
            
        self.embedding_fn = embedding_functions.OpenAIEmbeddingFunction(
            api_key=api_key,
            model_name="text-embedding-3-small"
        )
        
        # Get or Create Collection
        self.collection = self.client.get_or_create_collection(
            name="meeting_docs",
            embedding_function=self.embedding_fn
        )

    def add_document(self, doc_id: str, text: str, metadata: dict = None):
        """
        Splits text into chunks and strictly indexes them.
        Removes existing chunks for this doc_id before adding (to avoid duplicates/stale data).
        """
        # 1. Clear existing chunks for this doc (if any)
        # Note: Chroma doesn't have a direct "delete by metadata" in strictly simple API, 
        # but we can try filtering if needed. 
        # For simplicity in V1, we rely on upsert overwriting IDs, but IDs are chunk-based.
        # Ideally we should delete old ones first. 
        self._delete_doc_chunks(doc_id)

        # 2. Chunking
        chunks = self._split_text(text)
        
        if not chunks:
            return

        ids = []
        documents = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            # ID format: "doc_filename_chunk_0"
            chunk_id = f"{doc_id}_chunk_{i}"
            ids.append(chunk_id)
            documents.append(chunk)
            
            meta = metadata.copy() if metadata else {}
            meta["doc_id"] = doc_id
            meta["chunk_index"] = i
            metadatas.append(meta)
            
        # 3. Upsert
        if ids:
            self.collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            print(f"VectorDB: Indexed {len(ids)} chunks for {doc_id}")

    def query(self, query_text: str, n_results: int = 5):
        """
        Semantic search. Returns list of text chunks.
        """
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        
        # results['documents'] is a list of list of strings
        # results['metadatas'] is a list of list of dicts
        if results and results['documents']:
            # Flatten the list of lists (since we only query one text at a time)
            docs = results['documents'][0]
            metas = results['metadatas'][0] if 'metadatas' in results else [{}] * len(docs)
            
            combined_results = []
            for doc, meta in zip(docs, metas):
                combined_results.append({
                    "content": doc,
                    "metadata": meta
                })
            return combined_results 
        return []

    def _delete_doc_chunks(self, doc_id: str):
        """
        Deletes chunks belonging to a specific doc_id.
        """
        try:
            self.collection.delete(
                where={"doc_id": doc_id}
            )
        except Exception as e:
            print(f"VectorDB: Delete error (might be empty): {e}")

    def _split_text(self, text, chunk_size=800, overlap=100):
        """
        Simple sliding window splitter.
        """
        if not text:
            return []
            
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = min(start + chunk_size, text_len)
            chunk = text[start:end]
            chunks.append(chunk)
            
            if end == text_len:
                break
                
            start += (chunk_size - overlap)
            
        return chunks

# Singleton instance
vector_db = VectorDBClient()
