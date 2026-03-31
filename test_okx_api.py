#!/usr/bin/env python3
import hmac
import base64
from datetime import datetime, timezone
import requests
import json

# Load API config
with open('configs/okx_api_config.json', 'r') as f:
    config = json.load(f)

api_key = config['api_key']
secret_key = config['secret_key']
passphrase = config['passphrase']
base_url = config['base_url']

print(f"Testing API Key: {api_key[:20]}...")
print(f"Base URL: {base_url}")
print()

# Test 1: Get account balance
path = '/api/v5/account/balance'
timestamp = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
message = timestamp + 'GET' + path

mac = hmac.new(
    bytes(secret_key, encoding='utf8'),
    bytes(message, encoding='utf-8'),
    digestmod='sha256'
)
signature = base64.b64encode(mac.digest()).decode()

headers = {
    'OK-ACCESS-KEY': api_key,
    'OK-ACCESS-SIGN': signature,
    'OK-ACCESS-TIMESTAMP': timestamp,
    'OK-ACCESS-PASSPHRASE': passphrase,
    'Content-Type': 'application/json'
}

print("=" * 60)
print("Test 1: Get Account Balance")
print("=" * 60)

try:
    response = requests.get(base_url + path, headers=headers, timeout=10)
    result = response.json()
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Code: {result.get('code')}")
    print(f"Response Message: {result.get('msg')}")
    
    if result.get('code') == '0':
        print("✅ API Key is VALID!")
        if result.get('data'):
            print(f"Account Data: {json.dumps(result['data'][0], indent=2, ensure_ascii=False)}")
    else:
        print(f"❌ API Key ERROR!")
        print(f"Full Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
except Exception as e:
    print(f"❌ Request failed: {str(e)}")

print()
print("=" * 60)
print("Test 2: Get Account Configuration")
print("=" * 60)

# Test 2: Get account config
path2 = '/api/v5/account/config'
timestamp2 = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
message2 = timestamp2 + 'GET' + path2

mac2 = hmac.new(
    bytes(secret_key, encoding='utf8'),
    bytes(message2, encoding='utf-8'),
    digestmod='sha256'
)
signature2 = base64.b64encode(mac2.digest()).decode()

headers2 = {
    'OK-ACCESS-KEY': api_key,
    'OK-ACCESS-SIGN': signature2,
    'OK-ACCESS-TIMESTAMP': timestamp2,
    'OK-ACCESS-PASSPHRASE': passphrase,
    'Content-Type': 'application/json'
}

try:
    response2 = requests.get(base_url + path2, headers=headers2, timeout=10)
    result2 = response2.json()
    
    print(f"Status Code: {response2.status_code}")
    print(f"Response Code: {result2.get('code')}")
    print(f"Response Message: {result2.get('msg')}")
    
    if result2.get('code') == '0':
        print("✅ Account Config OK!")
        if result2.get('data'):
            print(f"Config: {json.dumps(result2['data'][0], indent=2, ensure_ascii=False)}")
    else:
        print(f"❌ Config ERROR!")
        print(f"Full Response: {json.dumps(result2, indent=2, ensure_ascii=False)}")
        
except Exception as e:
    print(f"❌ Request failed: {str(e)}")

print()
print("=" * 60)
print("API Key Details:")
print("=" * 60)
print(f"API Key: {api_key}")
print(f"Passphrase: {passphrase}")
print(f"Secret Key: {secret_key[:10]}...{secret_key[-10:]}")
