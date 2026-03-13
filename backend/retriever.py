from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

COLLECTION      = "lexcorp"
QDRANT_PATH     = "qdrant_data"
EMBED_MODEL     = "all-MiniLM-L6-v2"
SCORE_THRESHOLD = 0.2
TOP_K           = 4

# Lazy-initialized globals to avoid file-lock conflicts on reload
_model  = None
_client = None


def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBED_MODEL)
    return _model


def _get_client():
    global _client
    if _client is None:
        _client = QdrantClient(path=QDRANT_PATH)
    return _client


def embed_query(query: str) -> list:
    return _get_model().encode([query])[0].tolist()


def search(query_vector: list) -> list:
    results = _get_client().query_points(
        collection_name=COLLECTION,
        query=query_vector,
        limit=TOP_K,
        score_threshold=SCORE_THRESHOLD
    )
    return results.points


def build_citation(payload: dict) -> str:
    parts = []
    if payload.get("section_title"):
        parts.append(payload["section_title"])
    if payload.get("part"):
        parts.append(payload["part"])
    parts.append(f"Page {payload['page']}")
    return " | ".join(parts)


def format_results(results: list) -> list:
    return [
        {
            "text":     r.payload["text"],
            "citation": build_citation(r.payload),
            "score":    round(r.score, 3),
            "type":     r.payload["type"]
        }
        for r in results
    ]


def retrieve(query: str) -> dict:
    query_vector = embed_query(query)
    results      = search(query_vector)

    if not results:
        return {
            "found":   False,
            "chunks":  [],
            "message": "I don't have enough information to answer that. Please consult a lawyer directly."
        }

    return {
        "found":  True,
        "chunks": format_results(results)
    }


if __name__ == "__main__":
    result = retrieve("what is the billing rate for a senior associate?")
    print("Found:", result["found"])
    for chunk in result.get("chunks", []):
        print(f"\n[Score: {chunk['score']}] {chunk['citation']}")
        print(chunk["text"][:200])