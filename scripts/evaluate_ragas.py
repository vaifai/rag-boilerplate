"""
Ragas Evaluation Script - LLM as a Judge (Sequential Processing)
Evaluates RAG pipeline one query at a time using Ragas metrics with Ollama as the judge.

IMPORTANT: This script requires a model that can follow JSON schema instructions well.
Recommended models: llama3.1, mistral, qwen2.5
Avoid: llama3.2 (poor JSON formatting)
"""

import json
import sys
import os
from datasets import Dataset
import pandas as pd
import numpy as np

# Add app to path
sys.path.append(os.getcwd())

from app.core.config import settings
from app.clients.opensearch_client import create_opensearch_client
from app.embeddings.ollama_api_embedder import OllamaAPIEmbedder
from app.embeddings.ollama_generator import OllamaGenerator

# Ragas imports
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall
)

# Langchain Ollama imports for Ragas
from langchain_ollama import ChatOllama, OllamaEmbeddings

# Constants from config
INDEX_NAME = "bechmark_index"
# Use a model better at JSON formatting for Ragas
# llama3.1, mistral, or qwen2.5 work better than llama3.2
RAGAS_MODEL = "llama3.1:8b"  # Change this if you have a different model
OLLAMA_BASE_URL = "http://localhost:11434"

def search_opensearch_direct(client, embedder, query: str, index_name: str, top_k: int = 5):
    """
    Direct OpenSearch query without mocking.
    Returns hits with text_snippet for contexts.
    """
    q_vec = embedder.embed(query).tolist()

    knn_query = {
        "knn": {
            "embedding": {
                "vector": q_vec,
                "k": top_k
            }
        }
    }

    body = {
        "size": top_k,
        "query": knn_query,
        "_source": ["doc_id", "chunk_id", "title", "category", "text_snippet"]
    }

    res = client.search(index=index_name, body=body)
    hits = []
    for h in res["hits"]["hits"]:
        src = h["_source"]
        hits.append({
            "doc_id": src.get("doc_id"),
            "title": src.get("title"),
            "category": src.get("category"),
            "text_snippet": src.get("text_snippet", ""),
            "score": float(h["_score"])
        })
    return hits

def evaluate_single_query(query_text, answer, contexts, ground_truth, llm, embeddings, max_retries=2):
    """
    Evaluate a single query using Ragas with retry logic.
    Returns a dictionary with metric scores.
    """
    # Create a single-item dataset
    data = {
        "question": [query_text],
        "answer": [answer],
        "contexts": [contexts],
        "ground_truth": [ground_truth]
    }
    
    dataset = Dataset.from_dict(data)
    
    for attempt in range(max_retries):
        try:
            result = evaluate(
                dataset,
                metrics=[
                    faithfulness,
                    answer_relevancy,
                    context_recall
                ],
                llm=llm,
                embeddings=embeddings
            )
            
            # Extract scores
            df = result.to_pandas()
            
            # Check for NaN values
            scores = {
                "question": query_text,
                "answer": answer,
                "faithfulness": df.iloc[0]["faithfulness"],
                "answer_relevancy": df.iloc[0]["answer_relevancy"],
                "context_precision": np.nan,  # Not evaluated to avoid timeouts
                "context_recall": df.iloc[0]["context_recall"]
            }
            
            # If we got valid scores (not all NaN), return
            if not all(np.isnan(v) if isinstance(v, float) else False for k, v in scores.items() if k not in ["question", "answer"]):
                return scores
            else:
                print(f"      ⚠ Attempt {attempt + 1}: Got NaN values, retrying...")
                
        except Exception as e:
            print(f"      ⚠ Attempt {attempt + 1} failed: {str(e)[:100]}...")
            if attempt < max_retries - 1:
                print(f"      Retrying...")
            else:
                print(f"      ✗ All retries exhausted, returning NaN values")
    
    # If all retries failed, return NaN
    return {
        "question": query_text,
        "answer": answer,
        "faithfulness": np.nan,
        "answer_relevancy": np.nan,
        "context_precision": np.nan,
        "context_recall": np.nan
    }

def main():
    print("=" * 80)
    print("RAGAS EVALUATION - LLM as a Judge (Sequential Processing)")
    print("=" * 80)
    
    # Step 1: Initialize OpenSearch client
    print("\n[Step 1] Initializing OpenSearch client...")
    try:
        opensearch_client = create_opensearch_client()
        print(f"✓ OpenSearch client initialized (host: {settings.OPENSEARCH_HOST})")
    except Exception as e:
        print(f"✗ Failed to initialize OpenSearch: {e}")
        return
    
    # Step 2: Initialize embedder and generator
    print("\n[Step 2] Initializing embedder and generator...")
    try:
        embedder = OllamaAPIEmbedder()
        print(f"✓ Embedder initialized (model: {settings.OLLAMA_EMBEDDING_MODEL})")
        
        generator = OllamaGenerator()
        print(f"✓ Generator initialized (model: {settings.OLLAMA_GENERATE_MODEL})")
    except Exception as e:
        print(f"✗ Failed to initialize embedder/generator: {e}")
        return
    
    # Step 3: Initialize Ollama for Ragas
    print("\n[Step 3] Initializing Ollama LLM and Embeddings for Ragas...")
    print(f"⚠ Using model: {RAGAS_MODEL}")
    print(f"⚠ Make sure you have this model: ollama pull {RAGAS_MODEL}")
    try:
        llm = ChatOllama(
            model=RAGAS_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=0,
            num_ctx=4096,  # Increase context window
            timeout=600,  # 10 minute timeout for LLM calls
            request_timeout=600  # Request timeout
        )
        embeddings = OllamaEmbeddings(
            model=RAGAS_MODEL,
            base_url=OLLAMA_BASE_URL
        )
        print(f"✓ Ollama initialized for Ragas with model: {RAGAS_MODEL}")
        print(f"✓ Timeout set to 300 seconds (10 minutes) per LLM call")
    except Exception as e:
        print(f"✗ Failed to initialize Ollama for Ragas: {e}")
        print(f"Make sure Ollama is running and {RAGAS_MODEL} is installed:")
        print(f"  1. ollama serve")
        print(f"  2. ollama pull {RAGAS_MODEL}")
        return
    
    # Step 4: Load queries
    print("\n[Step 4] Loading benchmark queries...")
    try:
        with open("benchmark_queries.json", 'r') as f:
            queries = json.load(f)
        
        # Process fewer queries initially (change to [:50] for full evaluation)
        queries = queries[:10]  # Start with 5 for testing
        print(f"✓ Loaded {len(queries)} queries to evaluate")
    except Exception as e:
        print(f"✗ Failed to load queries: {e}")
        return
    
    # Step 5: Process queries ONE BY ONE
    print("\n[Step 5] Processing queries sequentially...")
    print("=" * 80)
    print("Note: Each query will be fully processed before moving to the next.")
    print("This includes: Search → Generate → Evaluate with Ragas")
    print("Expected time: ~2-3 minutes per query")
    print("=" * 80)
    
    results = []
    
    for i, item in enumerate(queries):
        query_text = item["query"]
        print(f"\n{'='*80}")
        print(f"QUERY {i+1}/{len(queries)}")
        print(f"{'='*80}")
        print(f"Question: {query_text}")
        
        try:
            # Step A: Search OpenSearch
            print(f"\n  [A] Searching OpenSearch for relevant contexts...")
            hits = search_opensearch_direct(opensearch_client, embedder, query_text, INDEX_NAME, top_k=10)
            print(f"      ✓ Retrieved {len(hits)} results")
            
            # Step B: Generate answer
            print(f"\n  [B] Generating answer using {settings.OLLAMA_GENERATE_MODEL}...")
            answer = generator.generate(query_text, hits)
            print(f"      ✓ Answer generated ({len(answer)} characters)")
            print(f"      Preview: {answer[:100]}...")
            
            # Step C: Prepare data for Ragas
            contexts = [hit["text_snippet"] for hit in hits if hit.get("text_snippet")]
            ground_truth = " ".join([doc["text"] for doc in item["expected_top_10"][:3]])
            
            # Step D: Evaluate with Ragas (this is the slow part)
            print(f"\n  [C] Evaluating with Ragas using {RAGAS_MODEL}...")
            print(f"      (This may take 1-2 minutes per query)")
            result = evaluate_single_query(
                query_text,
                answer,
                contexts,
                ground_truth,
                llm,
                embeddings
            )
            
            results.append(result)
            
            # Display results for this query
            print(f"\n  [D] Results for Query {i+1}:")
            # Format each metric properly, handling NaN values
            faith_val = f"{result['faithfulness']:.4f}" if not np.isnan(result['faithfulness']) else 'N/A'
            ans_rel_val = f"{result['answer_relevancy']:.4f}" if not np.isnan(result['answer_relevancy']) else 'N/A'
            ctx_prec_val = f"{result['context_precision']:.4f}" if not np.isnan(result['context_precision']) else 'N/A'
            ctx_rec_val = f"{result['context_recall']:.4f}" if not np.isnan(result['context_recall']) else 'N/A'
            
            print(f"      Faithfulness:       {faith_val}")
            print(f"      Answer Relevancy:   {ans_rel_val}")
            print(f"      Context Precision:  {ctx_prec_val}")
            print(f"      Context Recall:     {ctx_rec_val}")
            print(f"\n      ✓ Query {i+1} completed!")
            
            # Save intermediate results after each query
            df_temp = pd.DataFrame(results)
            df_temp.to_csv("ragas_evaluation_results_partial.csv", index=False)
            print(f"      ✓ Progress saved to ragas_evaluation_results_partial.csv")
            
        except Exception as e:
            print(f"\n      ✗ Error processing query {i+1}: {e}")
            print(f"      Continuing with next query...")
            import traceback
            traceback.print_exc()
            continue
    
    # Step 6: Final results
    print("\n" + "=" * 80)
    print("FINAL RAGAS EVALUATION RESULTS")
    print("=" * 80)
    
    if len(results) == 0:
        print("✗ No queries were successfully evaluated.")
        return
    
    df = pd.DataFrame(results)
    
    # Display aggregate metrics (excluding NaN)
    print("\n📊 Aggregate Metrics (excluding failed evaluations):")
    print("-" * 80)
    print(f"{'Metric':<25} {'Average Score':<15} {'Valid/Total':<15}")
    print("-" * 80)
    
    for metric in ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]:
        valid_count = df[metric].notna().sum()
        total_count = len(df)
        avg = df[metric].mean() if valid_count > 0 else np.nan
        avg_str = f"{avg:.4f}" if not np.isnan(avg) else 'N/A'
        print(f"{metric.replace('_', ' ').title():<25} {avg_str:<15} {valid_count}/{total_count}")
    
    # Save final results
    output_file = "ragas_evaluation_results.csv"
    df.to_csv(output_file, index=False)
    print(f"\n✓ Final results saved to: {output_file}")
    
    # Display sample results
    print("\n📋 Individual Query Results:")
    print("-" * 80)
    for i in range(min(5, len(df))):
        print(f"\nQuery {i+1}: {df.iloc[i]['question'][:60]}...")
        for metric in ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]:
            val = df.iloc[i][metric]
            val_str = f"{val:.4f}" if not np.isnan(val) else 'N/A'
            print(f"  {metric.replace('_', ' ').title():<20}: {val_str}")
    
    print("\n" + "=" * 80)
    print(f"✓ Evaluation complete! Processed {len(results)}/{len(queries)} queries.")
    print("=" * 80)

if __name__ == "__main__":
    main()
