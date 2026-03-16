"""
WHOOP Integration Service
OAuth authentication and data sync
"""
import os
import httpx
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urlencode
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# WHOOP API Configuration
WHOOP_BASE_URL = "https://api.prod.whoop.com"
WHOOP_AUTH_URL = f"{WHOOP_BASE_URL}/oauth/oauth2/auth"
WHOOP_TOKEN_URL = f"{WHOOP_BASE_URL}/oauth/oauth2/token"

# Load from environment
WHOOP_CLIENT_ID = os.getenv("WHOOP_CLIENT_ID", "")
WHOOP_CLIENT_SECRET = os.getenv("WHOOP_CLIENT_SECRET", "")
WHOOP_REDIRECT_URI = os.getenv("WHOOP_REDIRECT_URI", "http://localhost:8001/auth/whoop/callback")

# Required scopes
WHOOP_SCOPES = [
    "read:recovery",
    "read:cycles", 
    "read:workout",
    "read:sleep",
    "read:profile",
    "read:body_measurement"
]


class WhoopService:
    """WHOOP OAuth and API service"""
    
    def __init__(self, client_id: str = None, client_secret: str = None):
        self.client_id = client_id or WHOOP_CLIENT_ID
        self.client_secret = client_secret or WHOOP_CLIENT_SECRET
        self.redirect_uri = WHOOP_REDIRECT_URI
    
    def get_authorization_url(self, state: str = None) -> str:
        """Generate OAuth authorization URL"""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(WHOOP_SCOPES)
        }
        if state:
            params["state"] = state
        
        return f"{WHOOP_AUTH_URL}?{urlencode(params)}"
    
    async def exchange_code_for_token(self, authorization_code: str) -> dict:
        """Exchange authorization code for access token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                WHOOP_TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": authorization_code,
                    "grant_type": "authorization_code",
                    "redirect_uri": self.redirect_uri
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Token exchange failed: {response.text}")
    
    async def refresh_access_token(self, refresh_token: str) -> dict:
        """Refresh access token using refresh token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                WHOOP_TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token"
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Token refresh failed: {response.text}")
    
    async def get_user_profile(self, access_token: str) -> dict:
        """Get WHOOP user profile"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{WHOOP_BASE_URL}/api/v1/user/profile",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Profile fetch failed: {response.text}")
    
    async def get_body_measurements(self, access_token: str) -> dict:
        """Get WHOOP user body measurements"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{WHOOP_BASE_URL}/api/v1/user/body_measurement",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Measurements fetch failed: {response.text}")
    
    async def get_recovery_collection(self, access_token: str, limit: int = 10, start: str = None, end: str = None) -> dict:
        """Get recovery scores"""
        params = {"limit": limit}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
            
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{WHOOP_BASE_URL}/api/v1/recovery",
                headers={"Authorization": f"Bearer {access_token}"},
                params=params
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Recovery fetch failed: {response.text}")
    
    async def get_cycle_collection(self, access_token: str, limit: int = 10, start: str = None, end: str = None) -> dict:
        """Get daily cycles (strain data)"""
        params = {"limit": limit}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
            
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{WHOOP_BASE_URL}/api/v1/cycle",
                headers={"Authorization": f"Bearer {access_token}"},
                params=params
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Cycle fetch failed: {response.text}")
    
    async def get_sleep_collection(self, access_token: str, limit: int = 10, start: str = None, end: str = None) -> dict:
        """Get sleep data"""
        params = {"limit": limit}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
            
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{WHOOP_BASE_URL}/api/v1/sleep",
                headers={"Authorization": f"Bearer {access_token}"},
                params=params
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Sleep fetch failed: {response.text}")
    
    async def get_workout_collection(self, access_token: str, limit: int = 10, start: str = None, end: str = None) -> dict:
        """Get workout data"""
        params = {"limit": limit}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
            
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{WHOOP_BASE_URL}/api/v1/workout",
                headers={"Authorization": f"Bearer {access_token}"},
                params=params
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Workout fetch failed: {response.text}")


# Singleton instance
whoop_service = WhoopService()
