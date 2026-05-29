import re
import numpy as np

from sklearn.metrics.pairwise import cosine_similarity
from config import Config
from openai import OpenAI


client = OpenAI(api_key=Config.OPENAI_KEY)


class SemanticChunking:

    @staticmethod
    def calculate_cosine_distances(sentences):

        distances = []

        for i in range(len(sentences) - 1):

            embedding_current = sentences[i]["combined_sentence_embedding"]

            embedding_next = sentences[i + 1]["combined_sentence_embedding"]

            similarity = cosine_similarity(
                [embedding_current],
                [embedding_next]
            )[0][0]

            distance = 1 - similarity

            distances.append(distance)

            sentences[i]["distance_to_next"] = distance

        return distances, sentences

    @staticmethod
    def combine_sentences(sentences, buffer_size=1):

        for i in range(len(sentences)):

            combined_sentence = ""

            for j in range(i - buffer_size, i):

                if j >= 0:

                    combined_sentence += sentences[j]["sentence"] + " "

            combined_sentence += sentences[i]["sentence"]

            for j in range(i + 1, i + 1 + buffer_size):

                if j < len(sentences):

                    combined_sentence += " " + sentences[j]["sentence"]

            sentences[i]["combined_sentence"] = combined_sentence

        return sentences

    @staticmethod
    def get_embeddings(texts):

        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )

        return [item.embedding for item in response.data]

    @staticmethod
    def chunk_it(txt):

        single_sentences_list = re.split(
            r"(?<=[.?!])\s+",
            txt
        )

        sentences = [
            {"sentence": x, "index": i}
            for i, x in enumerate(single_sentences_list)
            if x.strip()
        ]

        sentences = SemanticChunking.combine_sentences(sentences)

        embeddings = SemanticChunking.get_embeddings(
            [x["combined_sentence"] for x in sentences]
        )

        for i, sentence in enumerate(sentences):

            sentence["combined_sentence_embedding"] = embeddings[i]

        distances, sentences = (
            SemanticChunking.calculate_cosine_distances(sentences)
        )

        breakpoint_percentile_threshold = 95

        breakpoint_distance_threshold = np.percentile(
            distances,
            breakpoint_percentile_threshold
        )

        indices_above_thresh = [
            i
            for i, x in enumerate(distances)
            if x > breakpoint_distance_threshold
        ]

        start_index = 0

        chunks = []

        for index in indices_above_thresh:

            end_index = index

            group = sentences[start_index : end_index + 1]

            combined_text = " ".join(
                [d["sentence"] for d in group]
            )

            chunks.append(combined_text)

            start_index = index + 1

        if start_index < len(sentences):

            combined_text = " ".join(
                [d["sentence"] for d in sentences[start_index:]]
            )

            chunks.append(combined_text)

        return chunks
