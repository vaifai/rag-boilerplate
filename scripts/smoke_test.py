#!/usr/bin/env python3
"""
Smoke Test Script for RAG Playground

This script performs a sanity check of the entire RAG pipeline:
1. Creates a temporary test index via /api/index/create
2. Creates a small CSV subset and ingests via /api/ingest/start
3. Runs test queries via /api/search/query
4. Cleans up the test index

Usage:
    python scripts/smoke_test.py
"""

import sys
import os
import time
import pandas as pd
import requests
import argparse
from pathlib import Path


# ANSI color codes for pretty output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_step(message):
    """Print a step message"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}▶ {message}{Colors.END}")


def print_success(message):
    """Print a success message"""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")


def print_error(message):
    """Print an error message"""
    print(f"{Colors.RED}✗ {message}{Colors.END}")


def print_warning(message):
    """Print a warning message"""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")


def check_api_health(base_url):
    """Check if the API is running"""
    print_step("Checking API health")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"API is running at {base_url} (env: {data.get('env', 'unknown')})")
            return True
        else:
            print_error(f"API returned status code {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to API at {base_url}")
        print_warning("Make sure the FastAPI server is running: uvicorn app.__main__:app --reload")
        return False
    except Exception as e:
        print_error(f"Health check failed: {str(e)}")
        return False


def create_test_index(base_url, index_name, dimension=256):
    """Create a test index via API"""
    print_step(f"Creating test index: {index_name}")

    try:
        response = requests.post(
            f"{base_url}/api/index/create",
            json={
                "index_name": index_name,
                "embedding_dim": dimension
            },
            timeout=30
        )

        if response.status_code == 200:
            print_success(f"Index {index_name} created successfully")
            return True
        elif response.status_code == 400 and "already exists" in response.text:
            print_warning(f"Index {index_name} already exists")
            # Try to delete and recreate
            delete_test_index(base_url, index_name)
            return create_test_index(base_url, index_name, dimension)
        else:
            print_error(f"Failed to create index: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print_error(f"Error creating index: {str(e)}")
        return False


def prepare_test_csv(csv_path, num_rows=10):
    """Create a small test CSV file"""
    print_step(f"Preparing test CSV with {num_rows} rows from {csv_path}")

    # Read original CSV
    df = pd.read_csv(csv_path, nrows=num_rows)
    print_success(f"Loaded {len(df)} rows from source CSV")

    # Create test CSV in current directory
    test_csv_path = "smoke_test_data.csv"
    df.to_csv(test_csv_path, index=False)
    print_success(f"Created test CSV: {test_csv_path}")

    return test_csv_path, len(df)


def ingest_test_data(base_url, index_name, csv_path):
    """Ingest test data via /api/ingest/start"""
    print_step(f"Starting ingestion from {csv_path}")

    try:
        response = requests.post(
            f"{base_url}/api/ingest/start",
            json={
                "csv_path": csv_path,
                "index_name": index_name,
                "doc_id_col": "id",
                "title_col": "title",
                "category_col": "category",
                "text_col": "text"
            },
            timeout=20
        )

        if response.status_code == 200:
            result = response.json()
            print_success(f"Ingestion started: {result.get('message', 'OK')}")
            return True
        else:
            print_error(f"Failed to start ingestion: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print_error(f"Error starting ingestion: {str(e)}")
        return False


def wait_for_ingestion(base_url, index_name, expected_min_docs=1, max_wait=60):
    """Poll the index to check if documents have been ingested"""
    print_step(f"Waiting for ingestion to complete (max {max_wait}s)...")

    from opensearchpy import OpenSearch
    client = OpenSearch(
        hosts=["http://localhost:9200"],
        use_ssl=False,
        verify_certs=False
    )

    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            # Check document count in index
            client.indices.refresh(index=index_name)
            count_response = client.count(index=index_name)
            doc_count = count_response['count']

            if doc_count >= expected_min_docs:
                print_success(f"Ingestion complete! {doc_count} documents indexed")
                return doc_count

            # Wait a bit before checking again
            time.sleep(2)
            print(f"  {Colors.BLUE}⏳ Waiting... ({doc_count} docs so far){Colors.END}", end='\r')

        except Exception as e:
            print_warning(f"Error checking index: {str(e)}")
            time.sleep(2)

    print_error(f"Timeout waiting for ingestion after {max_wait}s")
    return 0


def run_test_queries(base_url, index_name):
    """Run test queries via API and verify results"""
    print_step("Running test queries")

    test_queries = [
        ("What are unit testing strategies?", "programming"),
        ("Tell me about AI privacy", "technology"),
        ("How to earn passive income?", "finance"),
        ("Explain batching strategies", None),  # No category filter
    ]

    results = []

    for i, (query, category) in enumerate(test_queries, 1):
        print(f"\n  Query {i}: '{query}'" + (f" [category: {category}]" if category else ""))

        try:
            # Prepare request payload
            payload = {
                "index_name": index_name,
                "query": query,
                "top_k": 3
            }
            # if category:
            #     payload["category"] = category

            # Call search API
            response = requests.post(
                f"{base_url}/api/search/query",
                json=payload,
                timeout=60  # Longer timeout for LLM generation
            )

            if response.status_code != 200:
                print_error(f"    API returned status {response.status_code}: {response.text}")
                results.append(False)
                continue

            result = response.json()

            # Verify search results (API returns 'contexts' not 'results')
            search_results = result.get('contexts', [])
            if not search_results:
                print_error(f"    No search results returned")
                results.append(False)
                continue

            print_success(f"    Found {len(search_results)} results")
            top_result = search_results[0]
            print(f"    Top result: '{top_result.get('title', 'N/A')}' (score: {top_result.get('score', 0):.3f})")

            # Verify RAG answer
            answer = result.get('answer', '')
            if not answer:
                print_error(f"    No answer generated")
                results.append(False)
                continue

            print_success(f"    Generated answer ({len(answer)} chars)")

            results.append(True)

        except requests.exceptions.Timeout:
            print_error(f"    Query timed out (LLM generation may be slow)")
            results.append(False)
        except Exception as e:
            print_error(f"    Query failed: {str(e)}")
            results.append(False)

    return results


def delete_test_index(base_url, index_name):
    """Delete the test index via OpenSearch directly (no API endpoint for delete)"""
    print_step(f"Cleaning up test index: {index_name}")

    try:
        # We need to use OpenSearch client directly for deletion
        # since there's no delete endpoint in the API
        from opensearchpy import OpenSearch
        client = OpenSearch(
            hosts=["http://localhost:9200"],
            use_ssl=False,
            verify_certs=False
        )

        if client.indices.exists(index=index_name):
            client.indices.delete(index=index_name)
            print_success(f"Index {index_name} deleted")
        else:
            print_warning(f"Index {index_name} does not exist")
    except Exception as e:
        print_warning(f"Could not delete index: {str(e)}")


def main():
    """Main smoke test function"""
    # Parse arguments
    parser = argparse.ArgumentParser(description='RAG Playground Smoke Test')
    parser.add_argument('--base-url', default='http://localhost:8000',
                        help='Base URL of the FastAPI application (default: http://localhost:8000)')
    parser.add_argument('--csv-path', default='dev_dataset_100.csv',
                        help='Path to the CSV dataset (default: dev_dataset_100.csv)')
    parser.add_argument('--num-rows', type=int, default=10,
                        help='Number of rows to ingest (default: 10)')
    args = parser.parse_args()

    print(f"\n{Colors.BOLD}{'='*60}")
    print(f"  RAG Playground - Smoke Test")
    print(f"{'='*60}{Colors.END}\n")

    # Configuration
    base_url = args.base_url
    test_index = f"smoke-test-{int(time.time())}"
    csv_path = args.csv_path
    num_rows = args.num_rows

    print(f"  API URL: {base_url}")
    print(f"  Test Index: {test_index}")
    print(f"  Dataset: {csv_path}")
    print(f"  Rows to ingest: {num_rows}\n")

    # Check if CSV exists
    if not os.path.exists(csv_path):
        print_error(f"Dataset not found: {csv_path}")
        print_warning("Please ensure the CSV file exists")
        return 1

    test_csv_path = None

    try:
        # Step 1: Check API health
        if not check_api_health(base_url):
            return 1

        # Step 2: Create test index
        if not create_test_index(base_url, test_index):
            return 1

        # Step 3: Prepare test CSV
        test_csv_path, num_rows_prepared = prepare_test_csv(csv_path, num_rows)

        # Step 4: Ingest test data
        if not ingest_test_data(base_url, test_index, test_csv_path):
            print_error("Failed to start ingestion")
            delete_test_index(base_url, test_index)
            return 1

        # Step 5: Wait for ingestion to complete
        num_indexed = wait_for_ingestion(base_url, test_index, expected_min_docs=1, max_wait=120)
        if num_indexed == 0:
            print_error("No documents were indexed")
            delete_test_index(base_url, test_index)
            return 1

        # Step 6: Run test queries
        query_results = run_test_queries(base_url, test_index)

        # Step 7: Cleanup
        delete_test_index(base_url, test_index)

        # Summary
        print(f"\n{Colors.BOLD}{'='*60}")
        print(f"  Test Summary")
        print(f"{'='*60}{Colors.END}\n")

        passed = sum(query_results)
        total = len(query_results)

        print(f"  Rows prepared: {num_rows_prepared}")
        print(f"  Documents indexed: {num_indexed}")
        print(f"  Queries tested: {total}")
        print(f"  Queries passed: {passed}")
        print(f"  Success rate: {passed/total*100:.1f}%\n")

        if passed == total:
            print_success("All smoke tests passed! ✨")
            return 0
        else:
            print_warning(f"{total - passed} test(s) failed")
            return 1

    except KeyboardInterrupt:
        print_warning("\n\nTest interrupted by user")
        try:
            delete_test_index(base_url, test_index)
            if test_csv_path and os.path.exists(test_csv_path):
                os.unlink(test_csv_path)
        except:
            pass
        return 1
    except Exception as e:
        print_error(f"Smoke test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

        # Try to cleanup on error
        try:
            delete_test_index(base_url, test_index)
            if test_csv_path and os.path.exists(test_csv_path):
                os.unlink(test_csv_path)
        except:
            pass

        return 1
    finally:
        # Always cleanup test CSV
        if test_csv_path and os.path.exists(test_csv_path):
            try:
                os.unlink(test_csv_path)
                print_success(f"Cleaned up test CSV: {test_csv_path}")
            except:
                pass


if __name__ == "__main__":
    sys.exit(main())

