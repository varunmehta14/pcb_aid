#!/usr/bin/env python3
"""
Test script for the PCB analyze endpoints.
This script tests both the synchronous and asynchronous analyze endpoints.
"""

import requests
import json
import time
import argparse
import sys
from typing import Dict, Optional, List, Any

# Base URL for API requests
BASE_URL = "http://localhost:8000"

def test_sync_analyze(board_id: str, query: str) -> None:
    """
    Test the synchronous analyze endpoint.
    
    Args:
        board_id: The board ID to analyze
        query: The query to send
    """
    print(f"\n=== Testing Synchronous Analyze - Query: '{query}' ===")
    
    try:
        # Send request to the analyze endpoint
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/board/{board_id}/analyze",
            json={"query": query},
            timeout=60  # 60 second timeout
        )
        elapsed = time.time() - start_time
        
        # Print response
        print(f"Status Code: {response.status_code}")
        print(f"Time Elapsed: {elapsed:.2f} seconds")
        
        if response.status_code == 200:
            result = response.json()
            print("Response:")
            print(json.dumps(result, indent=2))
            
            # Check for result field
            if "result" in result:
                print("✅ Result field found in response")
            else:
                print("❌ No result field in response")
        else:
            print(f"Error: {response.text}")
    
    except requests.exceptions.Timeout:
        print("⚠️ Request timed out (took more than 60 seconds)")
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Request failed: {str(e)}")
    except Exception as e:
        print(f"⚠️ Error: {str(e)}")

def test_async_analyze(board_id: str, query: str) -> None:
    """
    Test the asynchronous analyze endpoint.
    
    Args:
        board_id: The board ID to analyze
        query: The query to send
    """
    print(f"\n=== Testing Asynchronous Analyze - Query: '{query}' ===")
    
    try:
        # Start the async analyze task
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/board/{board_id}/analyze/async",
            json={"query": query}
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to start async task: {response.text}")
            return
        
        # Get the task ID
        task_data = response.json()
        task_id = task_data.get("task_id")
        
        if not task_id:
            print("❌ No task_id in response")
            return
            
        print(f"✅ Task started with ID: {task_id}")
        
        # Poll for task completion
        max_polls = 30  # Maximum number of polls (30 * 2 seconds = 60 seconds max)
        polls = 0
        
        while polls < max_polls:
            # Sleep for 2 seconds between polls
            time.sleep(2)
            polls += 1
            
            # Check task status
            status_response = requests.get(f"{BASE_URL}/board/analyze/task/{task_id}")
            
            if status_response.status_code != 200:
                print(f"❌ Failed to get task status: {status_response.text}")
                return
                
            status_data = status_response.json()
            status = status_data.get("status")
            elapsed_time = status_data.get("elapsed_time", 0)
            
            print(f"Task status: {status} (elapsed: {elapsed_time:.2f}s)")
            
            # If task is complete or failed, break out of the loop
            if status in ["completed", "error", "cancelled"]:
                break
                
        # Get final result
        final_response = requests.get(f"{BASE_URL}/board/analyze/task/{task_id}")
        final_data = final_response.json()
        total_elapsed = time.time() - start_time
        
        print(f"\nFinal Status: {final_data.get('status')}")
        print(f"Total Time Elapsed: {total_elapsed:.2f} seconds")
        
        if "result" in final_data:
            print("Result:")
            print(json.dumps(final_data["result"], indent=2))
        elif "error" in final_data:
            print(f"Error: {final_data['error']}")
    
    except Exception as e:
        print(f"⚠️ Error: {str(e)}")

def test_error_handling(board_id: str) -> None:
    """
    Test error handling in the analyze endpoints.
    
    Args:
        board_id: The board ID to use
    """
    print("\n=== Testing Error Handling ===")
    
    # Test with empty query
    print("\n--- Testing with empty query ---")
    response = requests.post(
        f"{BASE_URL}/board/{board_id}/analyze",
        json={"query": ""}
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Test with non-existent board ID
    print("\n--- Testing with non-existent board ID ---")
    response = requests.post(
        f"{BASE_URL}/board/non_existent_id/analyze",
        json={"query": "What are the trace lengths?"}
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Test cancellation of async task
    print("\n--- Testing task cancellation ---")
    response = requests.post(
        f"{BASE_URL}/board/{board_id}/analyze/async",
        json={"query": "What are all possible ways to redesign this PCB?"}
    )
    
    if response.status_code == 200:
        task_id = response.json().get("task_id")
        if task_id:
            print(f"Task started with ID: {task_id}")
            
            # Wait 2 seconds
            time.sleep(2)
            
            # Cancel the task
            cancel_response = requests.delete(f"{BASE_URL}/board/analyze/task/{task_id}")
            print(f"Cancel status code: {cancel_response.status_code}")
            print(f"Cancel response: {cancel_response.text}")
            
            # Check final status
            time.sleep(1)
            status_response = requests.get(f"{BASE_URL}/board/analyze/task/{task_id}")
            print(f"Final status: {status_response.text}")

def test_specific_traces(board_id: str) -> None:
    """
    Test specific traces with component designators and pad numbers.
    
    Args:
        board_id: The board ID to analyze
    """
    print("\n=== Testing Specific Trace Analysis ===")
    
    # Test with specific component and pad query
    specific_query = 'analyze the route from designator "U1", padnumber "11", to designator "R66", padnumber "1"'
    
    # Try both sync and async endpoints for comparison
    test_sync_analyze(board_id, specific_query)
    test_async_analyze(board_id, specific_query)

def run_comprehensive_tests(board_id: str = "sample_id") -> None:
    """
    Run a comprehensive suite of tests on both analyze endpoints.
    
    Args:
        board_id: The board ID to use
    """
    print(f"Running comprehensive tests on board ID: {board_id}")
    
    # Test various types of queries
    simple_queries = [
        "What are the trace lengths in this PCB?",
        "Analyze critical paths in this PCB",
        "What design issues exist in this PCB?"
    ]
    
    complex_queries = [
        "What are all the possible ways to redesign this PCB for better signal integrity?",
        "Analyze every trace and component in the PCB and recommend optimizations",
        "Find potential EMI issues and how they relate to trace routing"
    ]
    
    # Test simple queries with sync endpoint
    for query in simple_queries:
        test_sync_analyze(board_id, query)
    
    # Test complex queries with async endpoint
    for query in complex_queries:
        test_async_analyze(board_id, query)
    
    # Test error handling
    test_error_handling(board_id)
    
    # Test specific trace analysis
    test_specific_traces(board_id)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test script for PCB analyze endpoints")
    parser.add_argument("--board-id", default="sample_id", help="Board ID to use for testing")
    parser.add_argument("--query", help="Specific query to test")
    parser.add_argument("--async", action="store_true", help="Use async endpoint for testing")
    
    args = parser.parse_args()
    
    if args.query:
        # Test a specific query
        if getattr(args, "async"):
            test_async_analyze(args.board_id, args.query)
        else:
            test_sync_analyze(args.board_id, args.query)
    else:
        # Run comprehensive tests
        run_comprehensive_tests(args.board_id) 