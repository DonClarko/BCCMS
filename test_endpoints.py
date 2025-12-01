import requests

# Test if the endpoints are accessible
base_url = 'http://127.0.0.1:5000'

print("Testing endpoints...")
print("\n1. Testing /officials/list endpoint:")
try:
    response = requests.get(f'{base_url}/officials/list')
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Officials: {data}")
    else:
        print(f"   Response: {response.text}")
except Exception as e:
    print(f"   Error: {e}")

print("\n2. Testing /residents/list endpoint:")
try:
    response = requests.get(f'{base_url}/residents/list')
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Residents: {data}")
    else:
        print(f"   Response: {response.text}")
except Exception as e:
    print(f"   Error: {e}")

print("\nNote: If you get 401/302 errors, that's expected - you need to be logged in.")
print("The endpoints are working if you get those status codes, not 404 or 500.")
