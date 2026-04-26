import json
import os
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

load_dotenv()

# Use sentence-transformers for free local embeddings
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

def get_chroma_client():
    """Initialize ChromaDB client with persistent storage."""
    client = chromadb.PersistentClient(path="./chroma_db")
    return client


def get_embedding_function():
    """Get sentence-transformers embedding function."""
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )
    return ef


def initialize_resource_store() -> chromadb.Collection:
    """
    Load resources from resources.json and store in ChromaDB.
    Only loads if collection is empty to avoid duplicates.
    """
    client = get_chroma_client()
    ef = get_embedding_function()

    collection = client.get_or_create_collection(
        name="learning_resources",
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"}
    )

    # Only load if empty
    if collection.count() > 0:
        return collection

    # Load resources from JSON
    resources_path = os.path.join(os.path.dirname(__file__), "../data/resources.json")
    with open(resources_path, "r") as f:
        data = json.load(f)

    resources = data["resources"]

    # Prepare data for ChromaDB
    documents = []
    metadatas = []
    ids = []

    for i, resource in enumerate(resources):
        # Document text for embedding — skill + title + type
        doc_text = f"{resource['skill']} {resource['title']} {resource['type']} {resource.get('level', '')}"
        
        documents.append(doc_text)
        metadatas.append({
            "skill": resource["skill"],
            "title": resource["title"],
            "url": resource["url"],
            "type": resource["type"],
            "level": resource.get("level", "all"),
            "estimated_hours": resource.get("estimated_hours", 0)
        })
        ids.append(f"resource_{i}")

    # Add to ChromaDB
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )

    print(f"✅ Loaded {len(resources)} resources into ChromaDB")
    return collection


def query_resources(skill: str, n_results: int = 3) -> list:
    """
    Semantically search ChromaDB for resources relevant to a skill.
    
    Input: skill name (e.g. "transformer architecture", "SQL joins")
    Output: list of resource dicts with title, url, type
    """
    client = get_chroma_client()
    ef = get_embedding_function()

    collection = client.get_or_create_collection(
        name="learning_resources",
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"}
    )

    if collection.count() == 0:
        initialize_resource_store()

    results = collection.query(
        query_texts=[skill],
        n_results=min(n_results, collection.count())
    )

    # Format results
    resources = []
    if results and results["metadatas"]:
        for metadata in results["metadatas"][0]:
            resources.append({
                "title": metadata["title"],
                "url": metadata["url"],
                "type": metadata["type"],
                "level": metadata["level"],
                "estimated_hours": metadata["estimated_hours"]
            })

    return resources