from app.embeddings.ollama_api_embedder import OllamaAPIEmbedder
from app.embeddings.ollama_generator import OllamaGenerator
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

def search_opensearch(request, query: str, index_name: str, top_k: int = 5, filter_category: str = None):
    client = request.app.state.opensearch_client
    embedder = OllamaAPIEmbedder()
    q_vec = embedder.embed(query).tolist()

    # Use native k-NN query for better performance
    knn_query = {
        "knn": {
            "embedding": {
                "vector": q_vec,
                "k": top_k
            }
        }
    }

    if filter_category:
        # Add filter to k-NN query
        body = {
            "size": top_k,
            "query": {
                "bool": {
                    "must": [knn_query],
                    "filter": [{"term": {"category": filter_category}}]
                }
            },
            "_source": ["doc_id", "chunk_id", "title", "category", "text_snippet"]
        }
    else:
        body = {
            "size": top_k,
            "query": knn_query,
            "_source": ["doc_id", "chunk_id", "title", "category", "text_snippet"]
        }

    res = client.search(index=index_name, body=body)
    hits = []
    for h in res["hits"]["hits"]:
        src = h["_source"]
        hits.append(
            {"id": h["_id"], "score": float(h["_score"]), "doc_id": src.get("doc_id"), "title": src.get("title"),
             "category": src.get("category"), "text_snippet": src.get("text_snippet")})
    return hits

def rag_answer(request, query: str, index_name: str, top_k: int = 5, filter_category: str = None):
    hits = search_opensearch(request, query, index_name, top_k=top_k, filter_category=filter_category)
    generator = OllamaGenerator()
    answer = generator.generate(query, hits)
    return {"query": query, "answer": answer, "contexts": hits}