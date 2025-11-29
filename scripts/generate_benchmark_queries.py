#!/usr/bin/env python3
"""
Generate benchmark queries from the dataset for accuracy testing.

This script analyzes the benchmark_dataset_2000.csv and creates 50 queries
with their expected top 10 results based on semantic similarity.
"""

import pandas as pd
import json
from collections import defaultdict

def generate_benchmark_queries(csv_path, output_path):
    """Generate benchmark queries with expected results"""
    
    # Read the dataset
    df = pd.read_csv(csv_path)
    
    # Define 50 diverse queries covering all categories
    queries = [
        # Programming queries (9)
        {"query": "What are design patterns in software development?", "category": "programming", "keywords": ["design patterns", "overview"]},
        {"query": "How to write clean Python code?", "category": "programming", "keywords": ["clean python", "writing"]},
        {"query": "Explain unit testing strategies", "category": "programming", "keywords": ["unit testing", "strategies"]},
        {"query": "What is continuous integration?", "category": "programming", "keywords": ["continuous integration"]},
        {"query": "How to debug code effectively?", "category": "programming", "keywords": ["debugging", "techniques"]},
        {"query": "Explain data structures and algorithms", "category": "programming", "keywords": ["data structures", "algorithms"]},
        {"query": "What are REST API best practices?", "category": "programming", "keywords": ["rest api", "best practices"]},
        {"query": "How does async programming work in Python?", "category": "programming", "keywords": ["async programming", "python"]},
        {"query": "What is Docker and how to use it?", "category": "programming", "keywords": ["docker", "basics"]},
        
        # Technology queries (8)
        {"query": "What is retrieval augmented generation?", "category": "technology", "keywords": ["retrieval augmented generation", "rag"]},
        {"query": "How do transformers work in AI?", "category": "technology", "keywords": ["transformers", "work"]},
        {"query": "Explain vector search and embeddings", "category": "technology", "keywords": ["vector search", "introduction"]},
        {"query": "What are embeddings in machine learning?", "category": "technology", "keywords": ["embeddings", "101"]},
        {"query": "How to scale LLM inference?", "category": "technology", "keywords": ["scaling llm", "inference"]},
        {"query": "Dense vs sparse retrieval methods", "category": "technology", "keywords": ["dense", "sparse", "retrieval"]},
        {"query": "What is fine-tuning vs prompt engineering?", "category": "technology", "keywords": ["fine-tuning", "prompt engineering"]},
        {"query": "How to evaluate LLMs?", "category": "technology", "keywords": ["evaluation", "llm"]},
        
        # Finance queries (10)
        {"query": "How to create passive income?", "category": "finance", "keywords": ["passive income", "ideas"]},
        {"query": "What is budgeting and how to start?", "category": "finance", "keywords": ["budgeting", "101"]},
        {"query": "Explain mutual funds for beginners", "category": "finance", "keywords": ["mutual funds", "understanding"]},
        {"query": "How to set financial goals?", "category": "finance", "keywords": ["financial goal", "setting"]},
        {"query": "What are emergency funds?", "category": "finance", "keywords": ["emergency funds"]},
        {"query": "How does the stock market work?", "category": "finance", "keywords": ["stock market", "basics"]},
        {"query": "Explain credit scores", "category": "finance", "keywords": ["credit score", "explained"]},
        {"query": "Tax tips for freelancers", "category": "finance", "keywords": ["taxes", "freelancers"]},
        {"query": "How to start investing?", "category": "finance", "keywords": ["investing", "beginners"]},
        {"query": "What is retirement planning?", "category": "finance", "keywords": ["retirement planning"]},
        
        # Cooking queries (8)
        {"query": "How to make perfect dosa batter?", "category": "cooking", "keywords": ["perfect dosa", "batter"]},
        {"query": "What are spice blends and their uses?", "category": "cooking", "keywords": ["spice blends", "uses"]},
        {"query": "How to make sourdough starter?", "category": "cooking", "keywords": ["sourdough starter", "beginners"]},
        {"query": "Explain fermentation basics", "category": "cooking", "keywords": ["fermentation", "basics"]},
        {"query": "How to brew chai tea?", "category": "cooking", "keywords": ["brew chai", "how to"]},
        {"query": "Indian street food classics", "category": "cooking", "keywords": ["indian street food", "classics"]},
        {"query": "How to make paneer at home?", "category": "cooking", "keywords": ["making paneer", "home"]},
        {"query": "Healthy smoothie recipes", "category": "cooking", "keywords": ["healthy smoothie", "recipes"]},

        # Health queries (8)
        {"query": "What are yoga poses for beginners?", "category": "health", "keywords": ["yoga poses", "beginners"]},
        {"query": "Explain macros in nutrition", "category": "health", "keywords": ["understanding macros", "macros"]},
        {"query": "Home workout routines for fitness", "category": "health", "keywords": ["home workout", "routines"]},
        {"query": "What are hydration tips?", "category": "health", "keywords": ["hydration tips"]},
        {"query": "Nutrition basics for beginners", "category": "health", "keywords": ["nutrition basics"]},
        {"query": "How to manage work stress?", "category": "health", "keywords": ["managing work stress", "stress"]},
        {"query": "What is mindfulness meditation?", "category": "health", "keywords": ["mindfulness", "meditation"]},
        {"query": "Sleep hygiene tips", "category": "health", "keywords": ["sleep hygiene"]},

        # Travel queries (7)
        {"query": "Planning a weekend in Goa", "category": "travel", "keywords": ["weekend", "goa"]},
        {"query": "How to pack light for long trips?", "category": "travel", "keywords": ["packing light", "long trips"]},
        {"query": "Train travel tips in India", "category": "travel", "keywords": ["train travel", "india"]},
        {"query": "Backpacking in the Himalayas guide", "category": "travel", "keywords": ["backpacking", "himalayas"]},
        {"query": "How to plan a road trip?", "category": "travel", "keywords": ["planning", "road trip"]},
        {"query": "Cultural etiquette when traveling", "category": "travel", "keywords": ["cultural etiquette", "guide"]},
        {"query": "Budget travel tips", "category": "travel", "keywords": ["budget travel"]},
    ]

    benchmark_data = []

    for query_info in queries:
        query_text = query_info["query"]
        category = query_info["category"]
        keywords = query_info["keywords"]

        # Filter by category
        category_df = df[df['category'] == category].copy()

        # Score documents based on keyword matching
        def score_document(row):
            title_lower = row['title'].lower()
            text_lower = row['text'].lower()
            score = 0

            for keyword in keywords:
                keyword_lower = keyword.lower()
                # Exact title match gets highest score
                if keyword_lower in title_lower:
                    score += 10
                # Text match gets lower score
                if keyword_lower in text_lower:
                    score += 1

            return score

        category_df['relevance_score'] = category_df.apply(score_document, axis=1)

        # Get top 10 results
        top_results = category_df.nlargest(10, 'relevance_score')

        # Create expected results list
        expected_results = []
        for idx, row in top_results.iterrows():
            expected_results.append({
                "doc_id": row['id'],
                "title": row['title'],
                "category": row['category'],
                "relevance_score": int(row['relevance_score'])
            })

        benchmark_data.append({
            "query": query_text,
            "category": category,
            "expected_top_10": expected_results
        })

    # Save to JSON
    with open(output_path, 'w') as f:
        json.dump(benchmark_data, f, indent=2)

    print(f"✓ Generated {len(benchmark_data)} benchmark queries")
    print(f"✓ Saved to {output_path}")

    # Print summary
    category_counts = defaultdict(int)
    for item in benchmark_data:
        category_counts[item['category']] += 1

    print("\nQueries per category:")
    for cat, count in sorted(category_counts.items()):
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    generate_benchmark_queries(
        csv_path="benchmark_dataset_2000.csv",
        output_path="benchmark_queries.json"
    )

