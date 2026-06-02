import re
import numpy as np

from sklearn.metrics.pairwise import cosine_similarity
from openai import OpenAI

from config import Config


class SemanticChunking:

    def __init__(self, breakpoint_percentile=95, buffer_size=1):

        self.client = OpenAI(
            api_key=Config.OPENAI_KEY
        )

        self.breakpoint_percentile = breakpoint_percentile
        self.buffer_size = buffer_size

    def _process_sentences(self, text):

        sentences = [
            {
                "sentence": s,
                "index": i
            }
            for i, s in enumerate(
                re.split(r"(?<=[.?!])\s+", text)
            )
        ]

        for i, current in enumerate(sentences):

            context_range = range(
                max(0, i - self.buffer_size),
                min(len(sentences), i + self.buffer_size + 1),
            )

            current["combined_sentence"] = " ".join(
                sentences[j]["sentence"]
                for j in context_range
            )

        return sentences

    def _get_embeddings(self, texts):

        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )

        return [item.embedding for item in response.data]

    def _calculate_distances(self, sentences):

        embeddings = self._get_embeddings(
            [s["combined_sentence"] for s in sentences]
        )

        distances = []

        for i in range(len(sentences) - 1):

            distance = 1 - cosine_similarity(
                [embeddings[i]],
                [embeddings[i + 1]]
            )[0][0]

            distances.append(distance)

        return distances

    def chunk_text(self, text):

        sentences = self._process_sentences(text)

        print("SENTENCES:", sentences[:2])

        if len(sentences) <= 1:
            return [text]

        distances = self._calculate_distances(sentences)

        print("DISTANCES:", distances[:2])

        if not distances:
            return [text]

        threshold = np.percentile(
            distances,
            self.breakpoint_percentile
        )

        split_points = [
            i for i, d in enumerate(distances)
            if d > threshold
        ]

        print("SPLIT POINTS:", split_points)

        chunks = []

        start = 0

        for point in split_points + [len(sentences) - 1]:

            chunk = " ".join(
                s["sentence"]
                for s in sentences[start: point + 1]
            )

            print("CHUNK:", chunk[:100])

            chunks.append(chunk)

            start = point + 1

        return chunks