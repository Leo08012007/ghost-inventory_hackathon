from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

model = SentenceTransformer('all-MiniLM-L6-v2')

def find_best_matches(query, part_names, threshold=0.4):
    if not part_names:
        return []

    query_embedding = model.encode([query])
    parts_embedding = model.encode(part_names)

    similarities = cosine_similarity(query_embedding, parts_embedding)[0]

    matched_indices = [
        i for i, score in enumerate(similarities) if score > threshold
    ]

    return matched_indices
    