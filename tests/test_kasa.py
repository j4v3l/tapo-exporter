import logging
import requests
import base64
import hashlib
import time
import uuid
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def generate_klap_key():
    return base64.b64encode(get_random_bytes(16)).decode()

def main():
    host = "192.168.0.52"
    username = "javel.palmer@gmail.com"
    password = "Javelpalmer12~"
    
    logging.info(f"Testing device at: {host}")
    logging.info("Attempting to connect to device...")
    
    try:
        # Generate KLAP handshake
        klap_key = generate_klap_key()
        device_id = str(uuid.uuid4())
        
        handshake_data = {
            "method": "handshake",
            "params": {
                "protocol": "KLAP",
                "key": klap_key,
                "deviceId": device_id
            }
        }
        
        logging.info("Attempting KLAP handshake...")
        response = requests.post(
            f"http://{host}/app",
            json=handshake_data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Tapo/2.8.21"
            },
            timeout=5
        )
        logging.info(f"Handshake response: {response.text}")
        
        if response.status_code != 200:
            raise Exception(f"HTTP error: {response.status_code}")
            
        response_data = response.json()
        if "error_code" in response_data:
            raise Exception(f"Device error: {response_data['error_code']}")
            
        # Generate login request
        login_data = {
            "method": "login_device",
            "params": {
                "username": base64.b64encode(username.encode()).decode(),
                "password": base64.b64encode(password.encode()).decode(),
                "deviceId": device_id
            }
        }
        
        logging.info("Attempting login...")
        response = requests.post(
            f"http://{host}/app",
            json=login_data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Tapo/2.8.21"
            },
            timeout=5
        )
        logging.info(f"Login response: {response.text}")
        
        if response.status_code != 200:
            raise Exception(f"HTTP error: {response.status_code}")
            
        response_data = response.json()
        if "error_code" in response_data:
            raise Exception(f"Device error: {response_data['error_code']}")
            
        # Get device info
        device_info_data = {
            "method": "get_device_info",
            "params": {}
        }
        
        logging.info("Getting device info...")
        response = requests.post(
            f"http://{host}/app",
            json=device_info_data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Tapo/2.8.21"
            },
            timeout=5
        )
        logging.info(f"Device info response: {response.text}")
        
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        logging.error("Detailed error information:")
        raise

if __name__ == "__main__":
    main()