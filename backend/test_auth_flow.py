import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_auth():
    print("Testing Registration...")
    reg_data = {
        "email": "test_persistence@example.com",
        "password": "Password123!"
    }
    try:
        r = requests.post(f"{BASE_URL}/auth/register", json=reg_data)
        print(f"Registration Status: {r.status_code}")
        print(f"Registration Response: {r.text}")
        
        if r.status_code == 200:
            token = r.json().get("access_token")
            print("Successfully registered.")
            
            print("\nTesting Login...")
            login_data = reg_data
            r = requests.post(f"{BASE_URL}/auth/login", json=login_data)
            print(f"Login Status: {r.status_code}")
            print(f"Login Response: {r.text}")
            
            if r.status_code == 200:
                print("Successfully logged in.")
                
                print("\nTesting /auth/me...")
                headers = {"Authorization": f"Bearer {token}"}
                r = requests.get(f"{BASE_URL}/auth/me", headers=headers)
                print(f"Auth Me Status: {r.status_code}")
                print(f"Auth Me Response: {r.text}")
            else:
                print("Login failed.")
        else:
            print("Registration failed.")
            
    except Exception as e:
        print(f"Error during test: {e}")

if __name__ == "__main__":
    test_auth()
