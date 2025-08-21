import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import aiohttp
from pydantic import BaseModel

from src.models.customer import Customer

logger = logging.getLogger(__name__)


class AuthResponse(BaseModel):
    """Response model for authentication endpoint."""
    AccessToken: str


class BulkRequest(BaseModel):
    """Request model for bulk banner show endpoint."""
    Data: List[Dict[str, str | int]]


class ShowAdsApiService:
    """Service for sending customer data to ShowAds API with authentication and bulk processing."""
    
    BULK_LIMIT = 1000
    BASE_URL = "https://golang-assignment-968918017632.europe-west3.run.app"
    
    def __init__(self, project_key: str, session: Optional[aiohttp.ClientSession] = None):
        self.project_key = project_key
        self._session = session
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        
    async def __aenter__(self):
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()
            
    @property
    def session(self) -> aiohttp.ClientSession:
        """Get the HTTP session, creating one if needed."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session

    async def send_customers(self, customers: List[Customer]) -> None:
        """Send all customers to ShowAds API using bulk requests."""
        if not customers:
            logger.warning("No customers to send")
            return

        chunks = self._chunk_customers(customers)
        logger.info(f"Sending {len(customers)} customers in {len(chunks)} chunks")

        tasks = [asyncio.create_task(self._send_bulk_chunk(chunk)) for chunk in chunks]
        await asyncio.gather(*tasks)

        logger.info(f"Successfully sent all {len(customers)} customers")

    async def get_token(self) -> str:
        """Get a valid access token, refreshing if necessary."""
        if (self._access_token is None or
            self._token_expires_at is None or
            datetime.now() >= self._token_expires_at):
            await self._authenticate()
        return self._access_token or ""

    async def _authenticate(self) -> str:
        """Authenticate with the ShowAds API and return access token."""
        auth_data = {"ProjectKey": self.project_key}
        
        async with self.session.post(f"{self.BASE_URL}/auth", json=auth_data) as response:
            if response.status == 200:
                auth_response = AuthResponse(**await response.json())
                self._access_token = auth_response.AccessToken
                self._token_expires_at = datetime.now() + timedelta(hours=23)
                logger.info("Successfully authenticated with ShowAds API")
                return self._access_token
            else:
                response.raise_for_status()

    
    async def _send_bulk_chunk(self, customers: List[Customer]) -> None:
        """Send a chunk of customers to the bulk endpoint."""
        if not customers:
            return
            
        token = await self.get_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        data = [
            {"VisitorCookie": customer.Cookie, "BannerId": customer.Banner_id}
            for customer in customers
        ]
        
        bulk_request = BulkRequest(Data=data)
        
        async with self.session.post(
            f"{self.BASE_URL}/banners/show/bulk", 
            json=bulk_request.model_dump(),
            headers=headers
        ) as response:
            if response.status == 200:
                logger.info(f"Successfully sent {len(customers)} customers to ShowAds API")
            else:
                logger.error(f"Failed to send customers. Status: {response.status}")
                response.raise_for_status()
    
    def _chunk_customers(self, customers: List[Customer]) -> List[List[Customer]]:
        """Split customers list into chunks of BULK_LIMIT size."""
        return [
            customers[i:i + self.BULK_LIMIT] 
            for i in range(0, len(customers), self.BULK_LIMIT)
        ]
    
