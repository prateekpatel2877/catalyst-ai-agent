import json
import os
import numpy as np
from sentence_transformers import SentenceTransformer, util

# Load model once
_model = None
_resources = None
_embeddings = None

def _load_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def _load_resources():
    global _resources, _embeddings
    if _resources is None:
        resources_path = os.path.join(os.path.dirname(__file__), "../data/resources.json")
        with open(resources_path, "r") as f:
            data = json.load(f)
        _resources = data["resources"]
        model = _load_model()
        texts = [f"{r['skill']} {r['title']} {r['type']} {r.get('level', '')}" for r in _resources]
        _embeddings = model.encode(texts, convert_to_tensor=True)
    return _resources, _embeddings

def initialize_resource_store():
    """Load resources and embeddings into memory."""
    _load_resources()
    print("✅ Resources loaded into memory")
    return True

def query_resources(skill: str, n_results: int = 3) -> list:
    """Semantically search for resources relevant to a skill."""
    try:
        resources, embeddings = _load_resources()
        model = _load_model()
        query_embedding = model.encode(skill, convert_to_tensor=True)
        scores = util.cos_sim(query_embedding, embeddings)[0]
        top_indices = scores.argsort(descending=True)[:n_results]
        results = []
        for idx in top_indices:
            r = resources[idx]
            results.append({
                "title": r["title"],
                "url": r["url"],
                "type": r["type"],
                "level": r.get("level", "all"),
                "estimated_hours": r.get("estimated_hours", 0)
            })
        return results
    except Exception as e:
        print(f"Resource query error: {e}")
        return []