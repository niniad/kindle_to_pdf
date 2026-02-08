import requests
import ssl
import certifi
import os
import sys

print(f"Python: {sys.version}")
print(f"Requests: {requests.__version__}")
try:
    import urllib3
    print(f"urllib3: {urllib3.__version__}")
except ImportError:
    print("urllib3: Not installed")
print(f"OpenSSL: {ssl.OPENSSL_VERSION}")
print(f"Certifi: {certifi.where()}")

print("\nEnvironment Variables:")
for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'SSL_CERT_FILE', 'REQUESTS_CA_BUNDLE']:
    print(f"{key}: {os.environ.get(key)}")

print("\nTesting connection to oauth2.googleapis.com...")
try:
    response = requests.get('https://oauth2.googleapis.com', timeout=10)
    print(f"Status Code: {response.status_code}")
    print("Success!")
except Exception as e:
    print(f"Error: {e}")

print("\nTesting connection to www.google.com...")
try:
    response = requests.get('https://www.google.com', timeout=10)
    print(f"Status Code: {response.status_code}")
    print("Success!")
except Exception as e:
    print(f"Error: {e}")

print("\nTesting connection to www.google.com with verify=False...")
try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    response = requests.get('https://www.google.com', timeout=10, verify=False)
    print(f"Status Code: {response.status_code}")
    print("Success (Insecure)!")
except Exception as e:
    print(f"Error: {e}")
