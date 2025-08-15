# src/test_api.py
import requests
import json

def test_api():
    base_url = "http://localhost:8000"
    
    print("Testing Smart SQL Agent API...")
    print("-" * 40)
    
    try:
        # Test health endpoint
        print("1. Testing health endpoint...")
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            health = response.json()
            print(f"   Status: {health.get('status', 'unknown')}")
            print(f"   Uptime: {health.get('metrics', {}).get('uptime_seconds', 0)} seconds")
        else:
            print(f"   Health check failed: {response.status_code}")
            return
        
        # Test SQL generation
        print("\n2. Testing SQL generation...")
        sql_request = {
            "requirement": "Show top 5 customers by total revenue",
            "schema_info": "customers(id, name), orders(customer_id, amount)"
        }
        
        response = requests.post(f"{base_url}/sql/generate", json=sql_request)
        if response.status_code == 200:
            result = response.json()
            print(f"   Success: {result.get('success', False)}")
            print(f"   Method: {result.get('method', 'unknown')}")
            print(f"   Generation time: {result.get('generation_time', 0):.3f}s")
            print(f"   SQL preview: {result.get('sql', '')[:100]}...")
        else:
            print(f"   SQL generation failed: {response.status_code}")
        
        # Test metrics
        print("\n3. Testing metrics endpoint...")
        response = requests.get(f"{base_url}/metrics")
        if response.status_code == 200:
            metrics = response.json()
            print(f"   Total requests: {metrics.get('total_requests', 0)}")
            print(f"   Error rate: {metrics.get('error_rate_percent', 0):.1f}%")
        
        print("\nAPI test completed successfully!")
        
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to API server.")
        print("Make sure the API server is running:")
        print("python -m uvicorn api_server:app --reload --port 8000")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_api()