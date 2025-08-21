"""ShowAds API client service with retry logic and bulk processing capabilities."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Callable

import aiohttp

from src.models.api_models import AuthResponse, BulkRequest, BaseRequestBody, AuthRequest
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
    MAX_ATTEMPTS = 5
    # delay before retrying a previously failed api call in seconds
    RETRY_BASE_DELAY = 1.0
    
    def __init__(self, project_key: str, session: Optional[aiohttp.ClientSession] = None):
        self.project_key = project_key
        self._session = session
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

        self._auth_lock = asyncio.Lock()

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
            async with self._auth_lock:  # <--- only one coroutine enters
                if (self._access_token is None or
                        self._token_expires_at is None or
                        datetime.now() >= self._token_expires_at):
                    await self._authenticate()
        return self._access_token

    async def bulk_request(self, request: BulkRequest) -> None:
        """Make request to the /banners/show/bulk endpoint."""
        token = await self.get_token()
        headers = {"Authorization": f"Bearer {token}"}

        async with self.session.post(
                f"{self.BASE_URL}/banners/show/bulk",
                json=request.model_dump(),
                headers=headers
        ) as response:
            if response.status == 200:
                logger.info(f"Successfully sent {len(request.Data)} customers to ShowAds API")
                return
            elif response.status == 401:
                self._access_token = None
                self._token_expires_at = None
                logger.warning("Received 401, clearing token")
                response.raise_for_status()

            response.raise_for_status()

    async def auth_request(self, request: AuthRequest) -> str | None:
        """Make request to the /auth endpoint."""
        async with self.session.post(f"{self.BASE_URL}/auth", json=request.model_dump()) as response:
            if response.status == 200:
                auth_response = AuthResponse(**await response.json())
                self._access_token = auth_response.AccessToken
                self._token_expires_at = datetime.now() + timedelta(hours=23)
                logger.info("Successfully authenticated")
                return self._access_token

            response.raise_for_status()
            return None

    async def _authenticate(self) -> Optional[str]:
        """Authenticate with the ShowAds API and return access token."""
        auth_data = AuthRequest(ProjectKey=self.project_key)

        return await self._retry_request(self.auth_request, auth_data,  "Auth")

    async def _send_bulk_chunk(self, customers: List[Customer]) -> None:
        """Send a chunk of customers to the bulk endpoint."""
        if not customers:
            return

        # TODO: this could likely be made into a model as well
        data = [
            {"VisitorCookie": customer.Cookie, "BannerId": customer.Banner_id}
            for customer in customers
        ]
        bulk_request = BulkRequest(Data=data)

        await self._retry_request(self.bulk_request, bulk_request, "Bulk")
    
    async def _retry_request(self, request_func: Callable, request_body: BaseRequestBody, operation_name: str):
        """Retry logic for API requests."""
        for attempt in range(1, self.MAX_ATTEMPTS + 1):
            try:
                return await request_func(request_body)
            except aiohttp.ClientResponseError as e:
                if e.status in (401, 429, 500) and attempt < self.MAX_ATTEMPTS:
                    if e.status == 401:
                        logger.warning(f"{operation_name} request failed with 401, retrying (attempt {attempt}/{self.MAX_ATTEMPTS})")
                    else:
                        delay = self._calculate_delay(attempt)
                        logger.warning(f"{operation_name} request failed with status {e.status}, retrying in {delay:.1f}s (attempt {attempt}/{self.MAX_ATTEMPTS})")
                        await asyncio.sleep(delay)
                    continue
                raise
            except aiohttp.ClientError as e:
                if attempt < self.MAX_ATTEMPTS:
                    delay = self._calculate_delay(attempt)
                    logger.warning(f"{operation_name} request failed with error: {e}, retrying in {delay:.1f}s (attempt {attempt}/{self.MAX_ATTEMPTS})")
                    await asyncio.sleep(delay)
                    continue
                raise
        return None

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay that goes up with the attempt number."""
        return self.RETRY_BASE_DELAY * (2 * attempt)
    
    def _chunk_customers(self, customers: List[Customer]) -> List[List[Customer]]:
        """Split customers list into chunks of BULK_LIMIT size."""
        return [
            customers[i:i + self.BULK_LIMIT] 
            for i in range(0, len(customers), self.BULK_LIMIT)
        ]
    
