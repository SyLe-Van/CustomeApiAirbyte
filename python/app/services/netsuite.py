import hmac
import hashlib
import base64
import time
import secrets
from urllib.parse import urlencode, quote
import httpx
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class NetSuiteClient:
    """NetSuite REST API client with OAuth 1.0a authentication"""

    def __init__(self, realm: str, consumer_key: str, consumer_secret: str, 
                 token_key: str, token_secret: str):
        if not all([realm, consumer_key, consumer_secret, token_key, token_secret]):
            raise ValueError("Missing required NetSuite credentials")

        self.realm = realm
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.token_key = token_key
        self.token_secret = token_secret

        self.base_url = f"https://{realm}.suitetalk.api.netsuite.com/services/rest/record/v1"
        self.suiteql_url = f"https://{realm}.suitetalk.api.netsuite.com/services/rest/query/v1/suiteql"

        logger.info(f"NetSuite client initialized for realm: {realm}")

    def _generate_oauth_signature(self, method: str, url: str, params: Dict[str, str]) -> str:
        """Generate OAuth 1.0a signature"""
        # Create signature base string
        sorted_params = sorted(params.items())
        param_string = "&".join([f"{quote(str(k), safe='')}={quote(str(v), safe='')}" for k, v in sorted_params])
        
        base_string = "&".join([
            method.upper(),
            quote(url, safe=''),
            quote(param_string, safe='')
        ])

        # Create signing key
        signing_key = f"{quote(self.consumer_secret, safe='')}&{quote(self.token_secret, safe='')}"

        # Generate signature
        signature = base64.b64encode(
            hmac.new(
                signing_key.encode('utf-8'),
                base_string.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode('utf-8')

        return signature

    def _get_oauth_headers(self, method: str, url: str, params: Dict[str, str] = None) -> Dict[str, str]:
        """Generate OAuth 1.0a authorization headers"""
        if params is None:
            params = {}

        oauth_params = {
            'oauth_consumer_key': self.consumer_key,
            'oauth_token': self.token_key,
            'oauth_signature_method': 'HMAC-SHA256',
            'oauth_timestamp': str(int(time.time())),
            'oauth_nonce': secrets.token_hex(16),
            'oauth_version': '1.0'
        }

        # Combine OAuth params with request params for signature
        all_params = {**params, **oauth_params}
        
        # Generate signature
        signature = self._generate_oauth_signature(method, url, all_params)
        oauth_params['oauth_signature'] = signature

        # Create Authorization header
        auth_header = 'OAuth realm="' + self.realm + '"'
        for key, value in sorted(oauth_params.items()):
            auth_header += f', {key}="{quote(str(value), safe="")}"'

        return {
            'Authorization': auth_header,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    async def _make_request(self, url: str, method: str = "GET", 
                           headers: Dict[str, str] = None, 
                           json_data: Dict = None, 
                           retries: int = 3) -> Dict[str, Any]:
        """Make HTTP request with retry logic"""
        for attempt in range(1, retries + 1):
            try:
                logger.debug(f"Making NetSuite request: {method} {url} (attempt {attempt})")

                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=headers,
                        json=json_data
                    )

                    # Handle rate limiting with exponential backoff
                    if response.status_code == 429:
                        if attempt < retries:
                            delay = 2 ** attempt  # 2s, 4s, 8s
                            logger.warning(f"Rate limited, retrying in {delay}s...")
                            await asyncio.sleep(delay)
                            continue

                    if response.status_code >= 400:
                        error_text = response.text
                        logger.error(f"NetSuite API error ({response.status_code}): {error_text}")
                        raise Exception(
                            f"NetSuite API error ({response.status_code}): {response.reason_phrase}. {error_text}"
                        )

                    return response.json()

            except httpx.TimeoutException:
                if attempt < retries:
                    delay = 2 ** attempt
                    logger.warning(f"Request timeout, retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    raise Exception("Request timeout after multiple retries")
            except Exception as e:
                if attempt == retries:
                    raise
                if "connection" in str(e).lower():
                    delay = 2 ** attempt
                    logger.warning(f"Connection error, retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    raise

    async def get_records(self, entity: str, params: Dict[str, Any] = None, expand_details: bool = True) -> Dict[str, Any]:
        """Get records from NetSuite REST API"""
        if params is None:
            params = {}

        url = f"{self.base_url}/{entity}"
        
        # Build query string
        query_params = {k: str(v) for k, v in params.items() if v is not None}
        if query_params:
            url += "?" + urlencode(query_params)

        headers = self._get_oauth_headers("GET", f"{self.base_url}/{entity}", query_params)
        
        data = await self._make_request(url, method="GET", headers=headers)

        items = data.get("items", [])
        
        # Automatically fetch full details for each record if expand_details is True
        if expand_details and items:
            logger.info(f"Fetching details for {len(items)} {entity} records...")
            detailed_items = []
            for item in items:
                try:
                    record_id = item.get("id")
                    if record_id:
                        full_record = await self.get_record(entity, record_id)
                        detailed_items.append(full_record)
                    else:
                        detailed_items.append(item)
                except Exception as e:
                    logger.warning(f"Failed to fetch details for {entity} ID {record_id}: {str(e)}")
                    detailed_items.append(item)
            items = detailed_items

        return {
            "entity": entity,
            "count": data.get("count", 0),
            "hasMore": data.get("hasMore", False),
            "items": items,
            "offset": params.get("offset", 0),
            "limit": params.get("limit", 1000),
            "totalResults": data.get("totalResults", data.get("count", 0))
        }

    async def execute_suiteql(self, query: str, limit: int = 1000, offset: int = 0) -> Dict[str, Any]:
        """Execute SuiteQL query"""
        url = f"{self.suiteql_url}?limit={limit}&offset={offset}"
        headers = self._get_oauth_headers("POST", self.suiteql_url, {"limit": str(limit), "offset": str(offset)})
        
        json_data = {"q": query}
        
        data = await self._make_request(url, method="POST", headers=headers, json_data=json_data)

        return {
            "count": data.get("count", 0),
            "hasMore": data.get("hasMore", False),
            "items": data.get("items", []),
            "offset": offset,
            "limit": limit,
            "totalResults": data.get("totalResults", data.get("count", 0))
        }

    async def get_record(self, entity: str, record_id: str) -> Dict[str, Any]:
        """Get a single record by ID"""
        url = f"{self.base_url}/{entity}/{record_id}"
        headers = self._get_oauth_headers("GET", url)
        
        return await self._make_request(url, method="GET", headers=headers)

    async def get_sublist(self, entity: str, record_id: str, sublist_name: str) -> Dict[str, Any]:
        """
        Get a sublist from a record (e.g., line items from a sales order)
        
        Args:
            entity: Entity type (e.g., 'salesorder')
            record_id: Record ID
            sublist_name: Sublist name (e.g., 'item')
            
        Returns:
            Sublist data
        """
        url = f"{self.base_url}/{entity}/{record_id}/{sublist_name}"
        headers = self._get_oauth_headers("GET", url)
        
        try:
            result = await self._make_request(url, method="GET", headers=headers)
            return result
        except Exception as e:
            logger.warning(f"Failed to fetch sublist {sublist_name} for {entity}/{record_id}: {str(e)}")
            return {"items": []}



# Import asyncio for sleep
import asyncio
