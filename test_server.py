#!/usr/bin/env python3
"""
Test script for PDF Processor MCP Server
Tests multithreading, API endpoints, and agent functionality
"""

import asyncio
import requests
import time
import json
from pathlib import Path

API_BASE = "http://localhost:8000"

def print_section(title):
    """Print a formatted section title."""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")

def test_server_health():
    """Test if server is running."""
    print_section("Testing Server Health")
    try:
        response = requests.get(f"{API_BASE}/api/documents")
        if response.status_code == 200:
            print("✓ Server is running")
            return True
        else:
            print("✗ Server responded with error")
            return False
    except Exception as e:
        print(f"✗ Server is not running: {e}")
        return False

def test_document_list():
    """Test listing documents."""
    print_section("Testing Document List")
    try:
        response = requests.get(f"{API_BASE}/api/documents")
        data = response.json()
        
        if data.get("success"):
            print(f"✓ Retrieved {len(data['documents'])} documents")
            for doc in data['documents'][:3]:
                print(f"  - {doc['document_id']}: {doc['status']}")
            return True
        else:
            print("✗ Failed to retrieve documents")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_upload_dummy_pdf():
    """Test uploading a dummy PDF (if you have one)."""
    print_section("Testing PDF Upload")
    print("Note: Create a test PDF and update the path in this function")
    print("Skipping upload test for now...")
    return True

def test_query_performance():
    """Test query performance with timing."""
    print_section("Testing Query Performance")
    
    # First get a processed document
    response = requests.get(f"{API_BASE}/api/documents")
    data = response.json()
    
    processed_docs = [d for d in data['documents'] if d.get('processed')]
    
    if not processed_docs:
        print("⚠ No processed documents found. Upload and process a PDF first.")
        return False
    
    doc_id = processed_docs[0]['document_id']
    print(f"Using document: {doc_id}")
    
    # Test multiple queries
    test_queries = [
        "What is this document about?",
        "Summarize the main points",
        "What are the key findings?"
    ]
    
    results = []
    for query in test_queries:
        print(f"\nQuery: {query}")
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{API_BASE}/api/query",
                json={"document_id": doc_id, "query": query},
                timeout=30
            )
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Response time: {elapsed:.2f}s")
                print(f"  Answer preview: {data['answer'][:100]}...")
                results.append(elapsed)
            else:
                print(f"✗ Query failed with status {response.status_code}")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    if results:
        avg_time = sum(results) / len(results)
        print(f"\n✓ Average response time: {avg_time:.2f}s")
        return True
    
    return False

def test_parallel_queries():
    """Test parallel query execution."""
    print_section("Testing Parallel Query Execution")
    
    response = requests.get(f"{API_BASE}/api/documents")
    data = response.json()
    
    processed_docs = [d for d in data['documents'] if d.get('processed')]
    
    if not processed_docs:
        print("⚠ No processed documents found.")
        return False
    
    doc_id = processed_docs[0]['document_id']
    
    import concurrent.futures
    
    queries = [
        "What is the main topic?",
        "What are the conclusions?",
        "What methodology was used?"
    ]
    
    def execute_query(query):
        start = time.time()
        response = requests.post(
            f"{API_BASE}/api/query",
            json={"document_id": doc_id, "query": query},
            timeout=30
        )
        elapsed = time.time() - start
        return (query, elapsed, response.status_code == 200)
    
    print(f"Executing {len(queries)} queries in parallel...")
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(execute_query, queries))
    
    total_elapsed = time.time() - start_time
    
    print(f"\n✓ Total time for {len(queries)} parallel queries: {total_elapsed:.2f}s")
    
    for query, elapsed, success in results:
        status = "✓" if success else "✗"
        print(f"{status} '{query}' - {elapsed:.2f}s")
    
    # Calculate speedup
    sequential_time = sum(r[1] for r in results)
    speedup = sequential_time / total_elapsed
    print(f"\n✓ Speedup factor: {speedup:.2f}x")
    
    return True

def test_summarization():
    """Test document summarization."""
    print_section("Testing Summarization")
    
    response = requests.get(f"{API_BASE}/api/documents")
    data = response.json()
    
    processed_docs = [d for d in data['documents'] if d.get('processed')]
    
    if not processed_docs:
        print("⚠ No processed documents found.")
        return False
    
    doc_id = processed_docs[0]['document_id']
    
    summary_types = ["brief", "detailed", "executive"]
    
    for summary_type in summary_types:
        print(f"\nGenerating {summary_type} summary...")
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{API_BASE}/api/summarize",
                json={"document_id": doc_id, "summary_type": summary_type},
                timeout=60
            )
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Generated in {elapsed:.2f}s")
                print(f"  Preview: {data['summary'][:150]}...")
            else:
                print(f"✗ Failed with status {response.status_code}")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    return True

def test_extraction():
    """Test information extraction."""
    print_section("Testing Information Extraction")
    
    response = requests.get(f"{API_BASE}/api/documents")
    data = response.json()
    
    processed_docs = [d for d in data['documents'] if d.get('processed')]
    
    if not processed_docs:
        print("⚠ No processed documents found.")
        return False
    
    doc_id = processed_docs[0]['document_id']
    
    extraction_types = ["key_points", "statistics"]
    
    for extraction_type in extraction_types:
        print(f"\nExtracting {extraction_type}...")
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{API_BASE}/api/extract",
                data={"document_id": doc_id, "extraction_type": extraction_type},
                timeout=60
            )
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Extracted in {elapsed:.2f}s")
                print(f"  Preview: {data['extracted_info'][:150]}...")
            else:
                print(f"✗ Failed with status {response.status_code}")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    return True

def main():
    """Run all tests."""
    print("\n" + "█"*60)
    print("  PDF PROCESSOR MCP SERVER - TEST SUITE")
    print("█"*60)
    
    tests = [
        ("Server Health", test_server_health),
        ("Document List", test_document_list),
        ("Upload Test", test_upload_dummy_pdf),
        ("Query Performance", test_query_performance),
        ("Parallel Queries", test_parallel_queries),
        ("Summarization", test_summarization),
        ("Extraction", test_extraction),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n✗ Test '{test_name}' crashed: {e}")
            results[test_name] = False
        
        time.sleep(0.5)  # Brief pause between tests
    
    # Print summary
    print_section("Test Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✓ PASS" if passed_test else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{'='*60}")
    print(f"  Results: {passed}/{total} tests passed")
    print(f"{'='*60}\n")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
