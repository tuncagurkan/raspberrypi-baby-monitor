#!/usr/bin/env python3
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IPRegistrationService:
    """Service to register device IP address with the backend API"""

    def __init__(self, config):
        self.config = config
        self.api_base_url = config.API_BASE_URL
        self.device_id = config.DEVICE_ID
        self.auth_key = config.DEVICE_AUTH_KEY
        self.access_token = None

    def get_public_ip(self):
        """Fetch the public IP address of this device"""
        try:
            response = requests.get('https://api.ipify.org?format=json', timeout=5)
            response.raise_for_status()
            ip = response.json()['ip']
            logger.info(f"✓ Public IP detected: {ip}")
            return ip
        except Exception as e:
            logger.error(f"✗ Failed to get public IP: {e}")
            return None

    def authenticate(self):
        """Authenticate with the backend API to get access token"""
        try:
            auth_url = f"{self.api_base_url}/api/device/auth"
            payload = {
                "deviceId": self.device_id,
                "authKey": self.auth_key
            }

            logger.info(f"Authenticating device: {self.device_id}")
            response = requests.post(
                auth_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            response.raise_for_status()

            response_data = response.json()
            data = response_data.get('data', {})
            self.access_token = data.get('accessToken')

            if self.access_token:
                logger.info(f"✓ Authentication successful")
                return True
            else:
                logger.error("✗ No token received from authentication")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"✗ Authentication failed: {e}")
            return False

    def register_ip(self, ip_address):
        """Register the device IP address with the backend"""
        if not self.access_token:
            logger.error("✗ Cannot register IP: No access token available")
            return False

        try:
            update_ip_url = f"{self.api_base_url}/api/update_ip"
            payload = {
                "deviceId": self.device_id,
                "ip": ip_address
            }

            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.access_token}'
            }

            logger.info(f"Registering IP {ip_address} for device {self.device_id}")
            response = requests.post(
                update_ip_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()

            logger.info(f"✓ IP address registered successfully")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"✗ IP registration failed: {e}")
            return False

    def initialize(self):
        """
        Complete initialization flow:
        1. Get public IP
        2. Authenticate with backend
        3. Register IP address
        """
        logger.info("🔄 Starting IP registration initialization...")

        # Step 1: Get public IP
        public_ip = self.get_public_ip()
        if not public_ip:
            logger.error("✗ IP registration failed: Could not determine public IP")
            return False

        # Step 2: Authenticate
        if not self.authenticate():
            logger.error("✗ IP registration failed: Authentication failed")
            return False

        # Step 3: Register IP
        if not self.register_ip(public_ip):
            logger.error("✗ IP registration failed: Registration failed")
            return False

        logger.info("✓ IP registration completed successfully")
        return True
