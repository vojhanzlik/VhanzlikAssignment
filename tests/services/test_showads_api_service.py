"""Tests for ShowAds API service integration, retry logic and error handling."""
import logging
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock
import pytest
from aiohttp import ClientResponseError

from src.models.customer import Customer
from src.services.showads_api_service import ShowAdsApiService


class AsyncContextManagerMock:
    def __init__(self, mock_response):
        self.mock_response = mock_response
    
    async def __aenter__(self):
        return self.mock_response
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None


@pytest.fixture
def sample_customers():
    """Create sample customers for testing."""
    return [
        Customer.model_construct(Name="John Doe", Age=25, Cookie="cookie1", Banner_id=1),
        Customer.model_construct(Name="Jane Smith", Age=30, Cookie="cookie2", Banner_id=2),
        Customer.model_construct(Name="Bob Johnson", Age=35, Cookie="cookie3", Banner_id=3),
    ]


@pytest.fixture
def large_customer_list():
    """Create a large list of customers to test chunking."""
    return [
        # omit validation
        Customer.model_construct(Name=f"Name", Age=25, Cookie=f"cookie", Banner_id=1)
        for _ in range(2500)
    ]


class TestShowAdsApiService:
    """Test cases for ShowAdsApiService."""
    
    @pytest.mark.asyncio
    async def test_authentication_success(self):
        """Test successful authentication """
        mock_session = Mock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"AccessToken": "test_token"})
        mock_session.post = Mock(return_value=AsyncContextManagerMock(mock_response))
        
        service = ShowAdsApiService("test_project", session=mock_session)
        token = await service.get_token()
        
        assert token == "test_token"
        assert service._access_token == "test_token"
        assert service._token_expires_at is not None
        mock_session.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_authentication_failure(self):
        """Test authentication failure"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status = 400
        mock_response.raise_for_status = Mock(side_effect=ClientResponseError(
            request_info=Mock(), history=Mock()
        ))
        mock_session.post = Mock(return_value=AsyncContextManagerMock(mock_response))
        
        service = ShowAdsApiService("test_project", session=mock_session)
        
        with pytest.raises(ClientResponseError):
            await service.get_token()
    
    @pytest.mark.asyncio
    async def test_get_token_when_token_exists(self):
        """Test getting token when token already exists and is valid."""
        service = ShowAdsApiService("test_project")
        service._access_token = "existing_token"
        service._token_expires_at = datetime.now() + timedelta(hours=1)
        
        token = await service.get_token()
        assert token == "existing_token"
    
    @pytest.mark.asyncio
    async def test_get_token_when_token_expired(self):
        """Test getting valid token when token is expired."""
        mock_session = Mock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"AccessToken": "new_token"})
        mock_session.post = Mock(return_value=AsyncContextManagerMock(mock_response))
        
        service = ShowAdsApiService("test_project", session=mock_session)
        service._access_token = "old_token"
        service._token_expires_at = datetime.now() - timedelta(hours=1)
        
        token = await service.get_token()
        assert token == "new_token"
    
    def test_chunk_customers(self, large_customer_list):
        """Test customer chunking functionality."""
        service = ShowAdsApiService("test_project")
        chunks = service._chunk_customers(large_customer_list)
        
        assert len(chunks) == 3
        assert len(chunks[0]) == 1000
        assert len(chunks[1]) == 1000
        assert len(chunks[2]) == 500
    
    def test_chunk_customers_list_smaller_than_bulk_limit(self, sample_customers):
        """Test chunking with list smaller than bulk limit."""
        service = ShowAdsApiService("test_project")
        chunks = service._chunk_customers(sample_customers)
        
        assert len(chunks) == 1
        assert len(chunks[0]) == 3
    
    def test_chunk_customers_empty_list(self):
        """Test chunking with empty list."""
        service = ShowAdsApiService("test_project")
        chunks = service._chunk_customers([])
        
        assert len(chunks) == 0
    
    @pytest.mark.asyncio
    async def test_send_bulk_chunk_success(self, sample_customers):
        """Test successful bulk chunk sending."""
        mock_session = Mock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_session.post = Mock(return_value=AsyncContextManagerMock(mock_response))
        
        service = ShowAdsApiService("test_project", session=mock_session)
        service._access_token = "test_token"
        service._token_expires_at = datetime.now() + timedelta(hours=1)
        
        await service._send_bulk_chunk(sample_customers)
        
        mock_session.post.assert_called_once()
        call_args = mock_session.post.call_args
        assert "/banners/show/bulk" in call_args[0][0]
        assert call_args[1]["headers"]["Authorization"] == "Bearer test_token"
    
    @pytest.mark.asyncio
    async def test_send_bulk_chunk_failure(self, sample_customers, caplog):
        """Test bulk chunk sending failure."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status = 500
        mock_response.raise_for_status = Mock(side_effect=ClientResponseError(
            request_info=Mock(), history=Mock()
        ))
        mock_session.post = Mock(return_value=AsyncContextManagerMock(mock_response))
        
        service = ShowAdsApiService("test_project", session=mock_session)
        service._access_token = "test_token"
        service._token_expires_at = datetime.now() + timedelta(hours=1)

        caplog.set_level(logging.ERROR)

        await service._send_bulk_chunk(sample_customers)

        assert any(
            "Failed to send" in message
            for message in caplog.messages
        )
    
    @pytest.mark.asyncio
    async def test_send_bulk_chunk_empty_list(self):
        """Test sending empty chunk."""
        mock_session = Mock()
        service = ShowAdsApiService("test_project", session=mock_session)
        
        await service._send_bulk_chunk([])
        
        mock_session.post.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_send_customers_success(self, large_customer_list):
        """Test sending customers with multiple chunks."""
        mock_session = Mock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"AccessToken": "test_token"})
        mock_session.post = Mock(return_value=AsyncContextManagerMock(mock_response))
        
        service = ShowAdsApiService("test_project", session=mock_session)
        
        await service.send_customers(large_customer_list)
        
        # Should call auth once + 3 bulk calls
        assert mock_session.post.call_count == 4
    
    @pytest.mark.asyncio
    async def test_send_customers_empty_list(self):
        """Test sending empty customer list."""
        service = ShowAdsApiService("test_project")
        
        await service.send_customers([])

    @pytest.mark.asyncio
    async def test_retry_on_429_status(self):
        """Test retry logic on 429 Too Many Requests."""
        mock_session = Mock()
        # First two requests return 429, third succeeds
        responses = [
            Mock(status=429, raise_for_status=Mock(side_effect=ClientResponseError(
                request_info=Mock(), history=Mock(), status=429
            ))),
            Mock(status=429, raise_for_status=Mock(side_effect=ClientResponseError(
                request_info=Mock(), history=Mock(), status=429
            ))), 
            Mock(status=200, json=AsyncMock(return_value={"AccessToken": "test_token"}))
        ]
        mock_session.post = Mock(side_effect=[AsyncContextManagerMock(r) for r in responses])
        
        service = ShowAdsApiService("test_project", session=mock_session)
        token = await service.get_token()
        
        assert token == "test_token"
        assert mock_session.post.call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_on_500_error(self):
        """Test retry logic on 500 error."""
        mock_session = Mock()
        # First request returns 500, second succeeds
        responses = [
            Mock(status=500, raise_for_status=Mock(side_effect=ClientResponseError(
                request_info=Mock(), history=Mock(), status=500
            ))),
            Mock(status=200, json=AsyncMock(return_value={"AccessToken": "test_token"}))
        ]
        mock_session.post = Mock(side_effect=[AsyncContextManagerMock(r) for r in responses])
        
        service = ShowAdsApiService("test_project", session=mock_session)
        token = await service.get_token()
        
        assert token == "test_token"
        assert mock_session.post.call_count == 2
    
    @pytest.mark.asyncio
    async def test_bulk_retry_on_401_clears_token(self, sample_customers):
        """Test that 401 error clears token and retries with success."""
        mock_session = Mock()
        # First request returns 401, second succeeds after auth
        bulk_responses = [
            Mock(status=401, raise_for_status=Mock(side_effect=ClientResponseError(
                request_info=Mock(), history=Mock(), status=401
            ))),
            Mock(status=200)
        ]
        auth_response = Mock(status=200, json=AsyncMock(return_value={"AccessToken": "new_token"}))
        
        mock_session.post = Mock(side_effect=[
            AsyncContextManagerMock(bulk_responses[0]),  # First bulk call fails
            AsyncContextManagerMock(auth_response),      # Auth call succeeds
            AsyncContextManagerMock(bulk_responses[1])   # Second bulk call succeeds
        ])
        
        service = ShowAdsApiService("test_project", session=mock_session)
        service._access_token = "expired_token"
        service._token_expires_at = datetime.now() + timedelta(hours=1)
        
        await service._send_bulk_chunk(sample_customers)
        
        assert mock_session.post.call_count == 3
        assert service._access_token == "new_token"
    
    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """Test that max retries limit is respected."""
        mock_session = Mock()
        # All requests return 429
        mock_response = Mock(status=429, raise_for_status=Mock(side_effect=ClientResponseError(
            request_info=Mock(), history=Mock(), status=429
        )))
        mock_session.post = Mock(return_value=AsyncContextManagerMock(mock_response))
        
        service = ShowAdsApiService("test_project", session=mock_session)
        
        with pytest.raises(ClientResponseError):
            await service.get_token()
        
        assert mock_session.post.call_count == service.MAX_ATTEMPTS

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test using service as context manager."""
        async with ShowAdsApiService("test_project") as service:
            assert service._session is not None
