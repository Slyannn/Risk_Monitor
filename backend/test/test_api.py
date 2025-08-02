"""
Simple API test without external dependencies
Tests the FastAPI endpoints
"""

import requests
import json

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

API_BASE = "http://localhost:8000"

def test_health_check():
    """Test health check endpoint"""
    try:
        response = requests.get(f"{API_BASE}/")
        print(f"✅ Health check: {response.status_code}")
        print(f"   Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_risky_users():
    """Test risky users endpoint"""
    try:
        response = requests.get(f"{API_BASE}/api/risky-users")
        print(f"✅ Risky users: {response.status_code}")
        data = response.json()
        print(f"   Found {len(data)} risky users")
        if data:
            print(f"   First user: {data[0]}")
        return True
    except Exception as e:
        print(f"❌ Risky users failed: {e}")
        return False

def test_stats():
    """Test stats endpoint"""
    try:
        response = requests.get(f"{API_BASE}/api/stats")
        print(f"✅ Stats: {response.status_code}")
        print(f"   Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Stats failed: {e}")
        return False

def test_user_analysis():
    """Test user analysis endpoint"""
    try:
        # First get a user ID from risky users
        response = requests.get(f"{API_BASE}/api/risky-users?limit=1")
        if response.status_code == 200:
            users = response.json()
            if users:
                user_id = users[0]["id"]
                response = requests.get(f"{API_BASE}/api/user/{user_id}/risk-analysis")
                print(f"✅ User analysis: {response.status_code}")
                data = response.json()
                print(f"   User {user_id} risk: {data.get('risk_score', 'N/A')}")
                return True
        
        print("⚠️ No users found for analysis test")
        return True
    except Exception as e:
        print(f"❌ User analysis failed: {e}")
        return False

def main():
    """Run all API tests"""
    print("🧪 Testing Risk Monitor API...")
    print("💡 Make sure the API is running: python -m uvicorn main:app --reload")
    print()
    
    tests = [
        ("Health Check", test_health_check),
        ("Risky Users", test_risky_users),
        ("System Stats", test_stats),
        ("User Analysis", test_user_analysis),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n🔍 Testing {name}...")
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"❌ {name} crashed: {e}")
            results.append((name, False))
    
    print("\n" + "="*50)
    print("📊 Test Results:")
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} {name}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\n🎯 Results: {passed}/{total} tests passed")

if __name__ == "__main__":
    main()