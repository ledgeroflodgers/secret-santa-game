#!/usr/bin/env python3
"""
Manual test script for gift management API endpoints.
This script demonstrates the gift management functionality.
"""
import requests
import json
import time

BASE_URL = 'http://localhost:8080'

def test_gift_management():
    """Test the gift management API endpoints manually."""
    print("=== Gift Management API Test ===\n")
    
    # Test 1: Add a gift
    print("1. Adding a new gift...")
    response = requests.post(f'{BASE_URL}/api/gifts', 
                           json={'name': 'Test Gift 1'})
    if response.status_code == 201:
        gift1 = response.json()
        print(f"✓ Gift added successfully: {gift1}")
        gift1_id = gift1['id']
    else:
        print(f"✗ Failed to add gift: {response.status_code} - {response.text}")
        return
    
    # Test 2: Add another gift with owner
    print("\n2. Adding a gift with initial owner...")
    response = requests.post(f'{BASE_URL}/api/gifts',
                           json={'name': 'Test Gift 2', 'owner_id': 1})
    if response.status_code == 201:
        gift2 = response.json()
        print(f"✓ Gift with owner added: {gift2}")
        gift2_id = gift2['id']
    else:
        print(f"✗ Failed to add gift with owner: {response.status_code} - {response.text}")
        return
    
    # Test 3: Get all gifts
    print("\n3. Retrieving all gifts...")
    response = requests.get(f'{BASE_URL}/api/gifts')
    if response.status_code == 200:
        gifts = response.json()
        print(f"✓ Retrieved {len(gifts['gifts'])} gifts:")
        for gift in gifts['gifts']:
            print(f"  - {gift['name']} (ID: {gift['id']}, Steals: {gift['steal_count']}, Locked: {gift['is_locked']})")
    else:
        print(f"✗ Failed to retrieve gifts: {response.status_code} - {response.text}")
        return
    
    # Test 4: Steal gift 1 (first steal)
    print(f"\n4. Stealing gift 1 (ID: {gift1_id})...")
    response = requests.put(f'{BASE_URL}/api/gifts/{gift1_id}/steal',
                          json={'new_owner_id': 2})
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Steal result: {result['message']}")
        print(f"  Gift state: Owner={result['gift']['current_owner']}, Steals={result['gift']['steal_count']}, Locked={result['gift']['is_locked']}")
    else:
        print(f"✗ Failed to steal gift: {response.status_code} - {response.text}")
        return
    
    # Test 5: Steal gift 1 again (second steal)
    print(f"\n5. Stealing gift 1 again...")
    response = requests.put(f'{BASE_URL}/api/gifts/{gift1_id}/steal',
                          json={'new_owner_id': 3})
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Steal result: {result['message']}")
        print(f"  Gift state: Owner={result['gift']['current_owner']}, Steals={result['gift']['steal_count']}, Locked={result['gift']['is_locked']}")
        print(f"  Steal history: {result['gift']['steal_history']}")
    else:
        print(f"✗ Failed to steal gift: {response.status_code} - {response.text}")
        return
    
    # Test 6: Steal gift 1 third time (should lock it)
    print(f"\n6. Stealing gift 1 for the third time (should lock it)...")
    response = requests.put(f'{BASE_URL}/api/gifts/{gift1_id}/steal',
                          json={'new_owner_id': 4})
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Steal result: {result['message']}")
        print(f"  Gift state: Owner={result['gift']['current_owner']}, Steals={result['gift']['steal_count']}, Locked={result['gift']['is_locked']}")
        print(f"  Steal history: {result['gift']['steal_history']}")
    else:
        print(f"✗ Failed to steal gift: {response.status_code} - {response.text}")
        return
    
    # Test 7: Try to steal locked gift (should fail)
    print(f"\n7. Attempting to steal locked gift...")
    response = requests.put(f'{BASE_URL}/api/gifts/{gift1_id}/steal',
                          json={'new_owner_id': 5})
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Steal attempt result: {result['message']}")
        print(f"  Success: {result['success']}")
        print(f"  Gift state: Owner={result['gift']['current_owner']}, Steals={result['gift']['steal_count']}, Locked={result['gift']['is_locked']}")
    else:
        print(f"✗ Failed to attempt steal: {response.status_code} - {response.text}")
        return
    
    # Test 8: Final state check
    print("\n8. Final state check...")
    response = requests.get(f'{BASE_URL}/api/gifts')
    if response.status_code == 200:
        gifts = response.json()
        print(f"✓ Final gift states:")
        for gift in gifts['gifts']:
            print(f"  - {gift['name']}: Owner={gift['current_owner']}, Steals={gift['steal_count']}, Locked={gift['is_locked']}, History={gift['steal_history']}")
    else:
        print(f"✗ Failed to retrieve final state: {response.status_code} - {response.text}")
    
    print("\n=== Test Complete ===")

if __name__ == '__main__':
    try:
        test_gift_management()
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to server. Make sure the Flask app is running on http://localhost:8080")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")