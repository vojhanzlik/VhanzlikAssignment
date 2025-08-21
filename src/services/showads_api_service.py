import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import aiohttp
from pydantic import BaseModel

from src.models.api_models import AuthResponse, BulkRequest
from src.models.customer import Customer

logger = logging.getLogger(__name__)



class ShowAdsApiService:
    """Service for sending customer data to ShowAds API with authentication and bulk processing."""

    # TODO: make these a part of the main config
    # max number of records sendable to the api's bulk route
    BULK_LIMIT = 1000
    # api url
    BASE_URL = "https://golang-assignment-968918017632.europe-west3.run.app"
    # max number of attempts for a single api call
    MAX_ATTEMPTS = 3
    # delay before retrying a previously failed api call in seconds
    RETRY_BASE_DELAY = 1.0
    
    def __init__(self, project_key: str, session: Optional[aiohttp.ClientSession] = None):
        self.project_key = project_key
        self._session = session
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        
    async def __aenter__(self):
        self._session = self.session
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

    async def _authenticate(self) -> Optional[str]:
        """Authenticate with the ShowAds API and return access token."""
        auth_data = {"ProjectKey": self.project_key}
        
        for attempt in range(1, self.MAX_ATTEMPTS + 1):
            try:
                async with self.session.post(f"{self.BASE_URL}/auth", json=auth_data) as response:
                    if response.status == 200:
                        auth_response = AuthResponse(**await response.json())
                        self._access_token = auth_response.AccessToken
                        self._token_expires_at = datetime.now() + timedelta(hours=23)
                        logger.info("Successfully authenticated")
                        return self._access_token

                    elif response.status in (429, 500):
                        if attempt < self.MAX_ATTEMPTS:
                            delay = self._calculate_delay(attempt)
                            logger.warning(f"Auth request failed with status {response.status}, retrying in {delay:.1f}s (attempt {attempt}/{self.MAX_ATTEMPTS})")
                            await asyncio.sleep(delay)
                            continue
                    response.raise_for_status()
            except aiohttp.ClientError as e:
                if attempt < self.MAX_ATTEMPTS:
                    delay = self._calculate_delay(attempt)
                    logger.warning(f"Auth request failed with error: {e}, retrying in {delay:.1f}s (attempt {attempt}/{self.MAX_ATTEMPTS})")
                    await asyncio.sleep(delay)
                    continue
                raise
        return None

    async def _send_bulk_chunk(self, customers: List[Customer]) -> None:
        """Send a chunk of customers to the bulk endpoint."""
        if not customers:
            return
        
        for attempt in range(1, self.MAX_ATTEMPTS + 1):
            try:
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
                        return
                    elif response.status == 401:
                        self._access_token = None
                        self._token_expires_at = None
                        if attempt < self.MAX_ATTEMPTS:
                            logger.warning(f"Received 401 Unauthorized, clearing token and retrying (attempt {attempt}/{self.MAX_ATTEMPTS})")
                            continue
                    elif response.status in (429, 500):
                        # Retry on rate limit or server error
                        if attempt < self.MAX_ATTEMPTS:
                            delay = self._calculate_delay(attempt)
                            logger.warning(f"Bulk request failed with status {response.status}, retrying in {delay:.1f}s (attempt {attempt}/{self.MAX_ATTEMPTS})")
                            await asyncio.sleep(delay)
                            continue
                    
                    logger.error(f"Failed to send customers. Status: {response.status}")
                    response.raise_for_status()
                    
            except aiohttp.ClientError as e:
                if attempt < self.MAX_ATTEMPTS:
                    delay = self._calculate_delay(attempt)
                    logger.warning(f"Bulk request failed with error: {e}, retrying in {delay:.1f}s (attempt {attempt}/{self.MAX_ATTEMPTS})")
                    await asyncio.sleep(delay)
                    continue
                raise
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay that goes up with the attempt number."""
        return self.RETRY_BASE_DELAY * (2 * attempt)
    
    def _chunk_customers(self, customers: List[Customer]) -> List[List[Customer]]:
        """Split customers list into chunks of BULK_LIMIT size."""
        return [
            customers[i:i + self.BULK_LIMIT] 
            for i in range(0, len(customers), self.BULK_LIMIT)
        ]
    
