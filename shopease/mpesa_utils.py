import requests
import json
import base64
from datetime import datetime
from requests.auth import HTTPBasicAuth
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class MpesaClient:
    """M-Pesa API client"""
    
    def __init__(self):
        self.business_shortcode = settings.MPESA_EXPRESS_SHORTCODE
        self.passkey = settings.MPESA_PASSKEY
        self.consumer_key = settings.MPESA_CONSUMER_KEY
        self.consumer_secret = settings.MPESA_CONSUMER_SECRET
        self.access_token = self._get_access_token()

    def _get_access_token(self):
        """Get OAuth access token from Safaricom"""
        try:
            # Log the credentials being used (mask sensitive data)
            logger.info(f"Getting access token for shortcode: {self.business_shortcode}")
            
            credentials = base64.b64encode(
                f"{self.consumer_key}:{self.consumer_secret}".encode()
            ).decode("utf-8")

            headers = {
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/json"
            }
            
            url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
            response = requests.get(url, headers=headers)
            
            # Log the response
            logger.info(f"Access token response status: {response.status_code}")
            
            if response.status_code == 200:
                token = response.json().get("access_token")
                logger.info("Successfully obtained access token")
                return token
            else:
                logger.error(f"Failed to get access token. Response: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting access token: {str(e)}")
            return None

    def _generate_password(self, timestamp):
        """Generate M-Pesa API password"""
        data_to_encode = f"{self.business_shortcode}{self.passkey}{timestamp}"
        encoded = base64.b64encode(data_to_encode.encode())
        return encoded.decode('utf-8')

    def stk_push(self, phone_number, amount, reference):
        """Initiate STK push"""
        if not self.access_token:
            logger.error("No access token available")
            return {"success": False, "message": "Failed to connect to M-Pesa"}

        try:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            password = base64.b64encode(
                f"{self.business_shortcode}{self.passkey}{timestamp}".encode()
            ).decode("utf-8")

            payload = {
                "BusinessShortCode": self.business_shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": int(amount),
                "PartyA": phone_number,
                "PartyB": self.business_shortcode,
                "PhoneNumber": phone_number,
                "CallBackURL": settings.MPESA_CALLBACK_URL,
                "AccountReference": reference,
                "TransactionDesc": f"Payment for {reference}"
            }

            # Log the request payload (mask sensitive data)
            logger.info(f"STK push request for phone: {phone_number}, amount: {amount}")

            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }

            url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
            response = requests.post(url, json=payload, headers=headers)
            
            # Log the response
            logger.info(f"STK push response status: {response.status_code}")
            logger.info(f"STK push response: {response.text}")

            if response.status_code == 200:
                result = response.json()
                if "ResponseCode" in result and result["ResponseCode"] == "0":
                    return {
                        "success": True,
                        "message": "Payment initiated successfully",
                        "checkout_request_id": result.get("CheckoutRequestID")
                    }
                    
            return {
                "success": False,
                "message": "Failed to initiate payment"
            }

        except Exception as e:
            logger.error(f"Error in STK push: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to connect to M-Pesa: {str(e)}"
            }

    def query_payment_status(self, checkout_request_id):
        """Query the status of an STK push transaction"""
        if not self.access_token:
            return {
                'success': False,
                'message': 'Failed to get access token'
            }

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = self._generate_password(timestamp)

        payload = {
            "BusinessShortCode": self.business_shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "CheckoutRequestID": checkout_request_id
        }

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        try:
            url = "https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query"
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            result_code = result.get('ResultCode')
            
            if result_code == '0':
                return {
                    'success': True,
                    'message': 'Payment completed successfully'
                }
            else:
                return {
                    'success': False,
                    'message': result.get('ResultDesc', 'Payment verification failed')
                }
                
        except Exception as e:
            logger.error(f"Error verifying transaction: {str(e)}")
            return {
                'success': False,
                'message': 'Failed to verify payment status'
            }

    def _format_phone_number(self, phone_number):
        """Convert phone number to required format (254XXXXXXXXX)"""
        # Remove any spaces or special characters
        phone_number = ''.join(filter(str.isdigit, str(phone_number)))
        
        # Handle different formats
        if phone_number.startswith('0'):  # 0712345678
            phone_number = '254' + phone_number[1:]
        elif phone_number.startswith('+'):  # +254712345678
            phone_number = phone_number[1:]
        elif not phone_number.startswith('254'):  # 712345678
            phone_number = '254' + phone_number
            
        return phone_number

# Create a singleton instance
mpesa_client = MpesaClient()