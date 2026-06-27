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

    def _empty_match(self):
        return {
            "source": None,
            "chunks": [],
            "combined_text": "",
            "metadata": None,
            "score": None,
        }

    def _pick_best_source(self, metadatas, distances):
        source_stats = {}

        for metadata, distance in zip(metadatas, distances):
            source = metadata["source"]
            stats = source_stats.setdefault(
                source,
                {"best_distance": distance, "hits": 0, "metadata": metadata},
            )
            stats["hits"] += 1
            if distance < stats["best_distance"]:
                stats["best_distance"] = distance
                stats["metadata"] = metadata

        best_source = min(
            source_stats,
            key=lambda source: (
                source_stats[source]["best_distance"],
                -source_stats[source]["hits"],
            ),
        )

        return (
            best_source,
            source_stats[best_source]["metadata"],
            source_stats[best_source]["best_distance"],
        )

    def query_best_cv_chunks(self, query_text):
        total_chunks = self.collection.count()
        if total_chunks == 0:
            return self._empty_match()

        n_results = min(total_chunks, 30)
        initial = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            include=["metadatas", "distances"],
        )

        if not initial["metadatas"] or not initial["metadatas"][0]:
            return self._empty_match()

        best_source, best_metadata, best_score = self._pick_best_source(
            initial["metadatas"][0],
            initial["distances"][0],
        )

        result = self.collection.get(
            where={"source": best_source},
            include=["documents", "metadatas"],
        )

        if not result["documents"]:
            return {
                "source": best_source,
                "chunks": [],
                "combined_text": "",
                "metadata": best_metadata,
                "score": best_score,
            }

        items = list(zip(result["documents"], result["metadatas"]))
        items.sort(key=lambda item: item[1].get("chunk_index", 0))

        chunks = [document for document, _ in items]
        combined_text = "\n\n".join(chunks)

        return {
            "source": best_source,
            "chunks": chunks,
            "combined_text": combined_text,
            "metadata": best_metadata,
            "score": best_score,
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
