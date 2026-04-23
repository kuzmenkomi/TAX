import requests
import random

# Register user with random email
email = f'test{random.randint(1000, 9999)}@example.com'
print('1. Registering user...')
r = requests.post('http://localhost:8000/auth/register', 
                  data={'email': email, 'password': 'TestPass123'})
if r.status_code == 200:
    token = r.json()['access_token']
    print(f'   Token obtained: {token[:30]}...')
    
    print()
    print('2. Try /onboarding WITHOUT email verification...')
    r2 = requests.post(
        'http://localhost:8000/onboarding',
        headers={'Authorization': f'Bearer {token}'},
        json={'country_code': 'BR', 'tax_structure': 'individual', 'portfolio_size': '10k-50k'}
    )
    print(f'   Status: {r2.status_code}')
    if r2.status_code != 200:
        detail = r2.json().get('detail', 'Error')
        print(f'   BLOCKED! Message: {detail}')
    else:
        print('   ERROR: Should have been blocked!')
else:
    print(f'Error: {r.text}')
