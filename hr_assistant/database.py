# database.py
import chromadb
from chromadb.utils import embedding_functions
from config import Config


class Database:
    def __init__(self):
        self.openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=Config.OPENAI_KEY, model_name=Config.MODEL_NAME
        )

        self.client = chromadb.PersistentClient(path=Config.PERSISTENT_DIR)
        self.collection = self.client.get_or_create_collection(
            name=Config.COLLECTION_NAME, embedding_function=self.openai_ef
        )

    def add_documents(self, documents, metadatas, ids):
        self.collection.add(documents=documents, metadatas=metadatas, ids=ids)

    def query(self, query_text, n_results=1):
        return self.collection.query(query_texts=[query_text], n_results=n_results)

    def query_best_cv_chunks(self, query_text):
        initial = self.collection.query(
            query_texts=[query_text],
            n_results=1,
        )

        if not initial["documents"] or not initial["documents"][0]:
            return {
                "source": None,
                "chunks": [],
                "combined_text": "",
                "metadata": None,
            }

        best_metadata = initial["metadatas"][0][0]
        source = best_metadata["source"]

        result = self.collection.get(
            where={"source": source},
            include=["documents", "metadatas"],
        )

        if not result["documents"]:
            return {
                "source": source,
                "chunks": [],
                "combined_text": "",
                "metadata": best_metadata,
            }

        items = list(
            zip(
                result["documents"],
                result["metadatas"],
            )
        )
        items.sort(key=lambda item: item[1].get("chunk_index", 0))

        chunks = [document for document, _ in items]
        combined_text = "\n\n".join(chunks)

        return {
            "source": source,
            "chunks": chunks,
            "combined_text": combined_text,
            "metadata": best_metadata,
        }

    def reset_database(self):
        self.client.delete_collection(Config.COLLECTION_NAME)

        self.collection = self.client.get_or_create_collection(
            name=Config.COLLECTION_NAME,
            embedding_function=self.openai_ef,
        )

    def get_tracked_files(self):
        """Get all unique files and their metadata from the database"""
        result = self.collection.get()
        tracked_files = {}

        if result and result["metadatas"]:
            for metadata in result["metadatas"]:
                if metadata["source"] not in tracked_files:
                    tracked_files[metadata["source"]] = {
                        "hash": metadata["hash"],
                        "last_modified": metadata["last_modified"],
                        "source": metadata["source"],
                    }

        return tracked_files

    def remove_document_by_source(self, source):
        """Remove all entries for a specific source file"""
        result = self.collection.get(where={"source": source})
        if result and result["ids"]:
            self.collection.delete(ids=result["ids"])

    def get_stats(self):
        result = self.collection.get()
        unique_sources = {metadata["source"] for metadata in result["metadatas"]}

        return f"""
            Nome Collezione: {self.collection.name}
            Numero totale Frammenti: {self.collection.count()}
            Numero Files Elaborati: {len(unique_sources)}
        """
