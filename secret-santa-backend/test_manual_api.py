#!/usr/bin/env python3
"""
Manual test script for the participant registration API endpoints.
"""
import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "http://localhost:5000"

def test_health():
    """Test health endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        print(f"Health check: {response.status_code} - {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_register_participant(name):
    """Test participant registration."""
    try:
        response = requests.post(
            f"{BASE_URL}/api/participants",
            json={"name": name},
            headers={"Content-Type": "application/json"}
        )
        print(f"Register {name}: {response.status_code} - {response.json()}")
        return response.status_code == 201
    except Exception as e:
        print(f"Registration failed for {name}: {e}")
        return False

def test_get_participants():
    """Test getting all participants."""
    try:
        response = requests.get(f"{BASE_URL}/api/participants")
        data = response.json()
        print(f"Get participants: {response.status_code} - Found {len(data.get('participants', []))} participants")
        return response.status_code == 200
    except Exception as e:
        print(f"Get participants failed: {e}")
        return False

def test_get_participant_count():
    """Test getting participant count."""
    try:
        response = requests.get(f"{BASE_URL}/api/participants/count")
        data = response.json()
        print(f"Get count: {response.status_code} - Count: {data.get('count')}/{data.get('max_participants')}")
        return response.status_code == 200
    except Exception as e:
        print(f"Get count failed: {e}")
        return False

def test_concurrent_registration():
    """Test concurrent registration."""
    print("\nTesting concurrent registration...")
    
    def register_user(i):
        return test_register_participant(f"ConcurrentUser_{i}")
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(register_user, i) for i in range(5)]
        results = [future.result() for future in futures]
    
    success_count = sum(results)
    print(f"Concurrent registration: {success_count}/5 successful")
    return success_count > 0

def main():
    """Run manual API tests."""
    print("Starting manual API tests...")
    
    # Test health endpoint
    if not test_health():
        print("Server not responding. Make sure to start the Flask app first:")
        print("python app.py")
        return
    
    print("\n--- Basic API Tests ---")
    
    # Test initial state
    test_get_participants()
    test_get_participant_count()
    
    # Test registration
    test_register_participant("Alice")
    test_register_participant("Bob")
    test_register_participant("Charlie")
    
    # Test getting data after registration
    test_get_participants()
    test_get_participant_count()
    
    # Test error cases
    print("\n--- Error Case Tests ---")
    
    # Empty name
    try:
        response = requests.post(
            f"{BASE_URL}/api/participants",
            json={"name": ""},
            headers={"Content-Type": "application/json"}
        )
        print(f"Empty name test: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Empty name test failed: {e}")
    
    # Missing name
    try:
        response = requests.post(
            f"{BASE_URL}/api/participants",
            json={},
            headers={"Content-Type": "application/json"}
        )
        print(f"Missing name test: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Missing name test failed: {e}")
    
    # Test concurrent registration
    test_concurrent_registration()
    
    # Final state
    print("\n--- Final State ---")
    test_get_participants()
    test_get_participant_count()
    
    print("\nManual API tests completed!")

if __name__ == "__main__":
    main()