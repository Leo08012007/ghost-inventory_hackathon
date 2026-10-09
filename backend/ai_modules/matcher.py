from typing import List, Tuple
import re
import difflib

_transformer_model = None

def get_transformer_model():
    global _transformer_model
    if _transformer_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _transformer_model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            print(f"Warning: Could not load SentenceTransformer model ({e}), falling back to token matcher.")
            _transformer_model = False
    return _transformer_model

def simple_token_similarity(query: str, text: str) -> float:
    """Fallback fuzzy/substring match score between 0.0 and 1.0"""
    q_words = re.findall(r'\w+', query.lower())
    t_words = set(re.findall(r'\w+', text.lower()))
    if not q_words or not t_words:
        return 0.0
    
    match_count = 0
    for qw in q_words:
        if qw in t_words:
            match_count += 1
        else:
            # Check for spelling variations
            matches = difflib.get_close_matches(qw, t_words, n=1, cutoff=0.8)
            if matches:
                match_count += 1

    if match_count == 0:
        # Check partial string containment
        if query.lower().strip() in text.lower():
            return 0.6
        return 0.0
    
    score = match_count / len(q_words)
    return round(score, 2)

def find_best_matches(query: str, part_names: List[str], threshold: float = 0.3) -> List[int]:
    """
    Original function signature preserved for backward compatibility.
    Returns list of matched indices where similarity > threshold.
    """
    if not part_names or not query or not query.strip():
        return []
    
    model = get_transformer_model()
    
    if model:
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            query_embedding = model.encode([query])
            parts_embedding = model.encode(part_names)
            similarities = cosine_similarity(query_embedding, parts_embedding)[0]
            matched_indices = [
                i for i, score in enumerate(similarities) if score > threshold
            ]
            return matched_indices
        except Exception as e:
            print(f"Error in SentenceTransformer match: {e}")
            
    # Fallback to simple token similarity
    matched_indices = []
    for i, name in enumerate(part_names):
        score = simple_token_similarity(query, name)
        if score > threshold:
            matched_indices.append(i)
    return matched_indices

def find_best_matches_with_scores(query: str, items: List[dict], threshold: float = 0.25) -> List[Tuple[int, float, str]]:
    """
    Enhanced matcher taking structured items (part_name, model_number, part_number, manufacturer, material, description).
    Returns list of tuples: (index, similarity_score, match_explanation).
    """
    if not items or not query or not query.strip():
        return []

    # Build rich textual descriptions for matching
    texts = []
    for item in items:
        p_name = item.get("part_name") or ""
        m_num = item.get("model_number") or ""
        p_num = item.get("part_number") or ""
        mfr = item.get("manufacturer") or ""
        mat = item.get("material") or ""
        sz = item.get("size") or ""
        desc = item.get("description") or ""
        combined = f"{p_name} {m_num} {p_num} {mfr} {mat} {sz} {desc}".strip()
        texts.append(combined)

    model = get_transformer_model()
    results = []

    if model:
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            query_embedding = model.encode([query])
            parts_embedding = model.encode(texts)
            similarities = cosine_similarity(query_embedding, parts_embedding)[0]

            for i, score in enumerate(similarities):
                score_val = float(score)
                if score_val >= threshold or query.lower().strip() in texts[i].lower():
                    # Generate human-readable match explanation
                    matched_field = "part description"
                    if item_m_num := items[i].get("model_number"):
                        if query.lower() in item_m_num.lower():
                            matched_field = f"exact model number ({item_m_num})"
                    if item_p_num := items[i].get("part_number"):
                        if query.lower() in item_p_num.lower():
                            matched_field = f"part number ({item_p_num})"

                    explanation = f"Matched by {matched_field} (Semantic Score: {int(score_val * 100)}%)"
                    results.append((i, score_val, explanation))

            return sorted(results, key=lambda x: x[1], reverse=True)
        except Exception as e:
            print(f"Error in SentenceTransformer enhanced match: {e}")

    # Fallback matching
    for i, text in enumerate(texts):
        score = simple_token_similarity(query, text)
        if score >= threshold or query.lower().strip() in text.lower():
            explanation = f"Matched by keyword relevance (Relevance Score: {int(score * 100)}%)"
            results.append((i, max(score, 0.4), explanation))

    return sorted(results, key=lambda x: x[1], reverse=True)