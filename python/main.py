from fastapi import FastAPI, Request, HTTPException, Depends, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
import logging
import time
from datetime import datetime

from app.config import settings
from app.services.netsuite import NetSuiteClient
from app.utils.cache import CacheManager
from app.utils.security import verify_api_key
from app.utils.formatter import (
    flatten_netsuite_response,
    transform_for_database,
    format_response_for_airbyte,
    custom_format_response
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Initialize cache and rate limiter
cache = CacheManager()
limiter = Limiter(key_func=get_remote_address)

# Startup time for uptime calculation
start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    logger.info("🚀 Starting NetSuite Proxy API")
    logger.info(f"📊 Environment: {settings.ENVIRONMENT}")
    logger.info(f"🔒 API Key Auth: {'Enabled' if settings.API_KEY else 'Disabled'}")
    yield
    logger.info("Shutting down NetSuite Proxy API")


# Initialize FastAPI app
app = FastAPI(
    title="NetSuite Proxy API",
    description="Production-ready NetSuite OAuth1 Proxy API for Airbyte integration",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time_req = time.time()
    
    response = await call_next(request)
    
    duration = (time.time() - start_time_req) * 1000  # Convert to ms
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Duration: {duration:.2f}ms - "
        f"IP: {request.client.host}"
    )
    
    return response


# Health check endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring"""
    uptime = int(time.time() - start_time)
    return {
        "status": "ok",
        "uptime": f"{uptime}s",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "service": "netsuite-proxy-api",
        "version": "1.0.0",
        "checks": {
            "netsuite": {
                "configured": all([
                    settings.NETSUITE_REALM,
                    settings.NETSUITE_CONSUMER_KEY,
                    settings.NETSUITE_CONSUMER_SECRET,
                    settings.NETSUITE_TOKEN_KEY,
                    settings.NETSUITE_TOKEN_SECRET
                ])
            },
            "auth": {
                "enabled": bool(settings.API_KEY)
            }
        }
    }


@app.get("/health/ready", tags=["Health"])
async def readiness_check():
    """Readiness check for Kubernetes"""
    ready = all([
        settings.NETSUITE_REALM,
        settings.NETSUITE_CONSUMER_KEY,
        settings.NETSUITE_CONSUMER_SECRET,
        settings.NETSUITE_TOKEN_KEY,
        settings.NETSUITE_TOKEN_SECRET
    ])
    
    if ready:
        return {"status": "ready"}
    else:
        raise HTTPException(
            status_code=503,
            detail={"status": "not ready", "reason": "Missing NetSuite credentials"}
        )


@app.get("/health/live", tags=["Health"])
async def liveness_check():
    """Liveness check for Kubernetes"""
    return {"status": "alive"}


# NetSuite endpoints
@app.get("/api/netsuite/{entity}", tags=["NetSuite"])
@limiter.limit(f"{settings.RATE_LIMIT_MAX}/15minutes")
async def get_netsuite_records(
    request: Request,
    entity: str = Path(..., description="NetSuite entity type (customer, invoice, etc.)"),
    limit: int = Query(1000, description="Number of records to fetch"),
    offset: int = Query(0, description="Offset for pagination"),
    q: str = Query(None, description="SUITEQL filter query"),
    fields: str = Query(None, description="Comma-separated list of fields"),
    expandSubresources: str = Query(None, description="Expand subresources"),
    expand: bool = Query(True, description="Fetch full details for each record (default: true)"),
    no_cache: bool = Query(False, description="Skip cache"),
    api_key: str = Depends(verify_api_key)
):
    """
    Fetch records from NetSuite
    
    - **entity**: NetSuite entity type (customer, invoice, salesorder, etc.)
    - **limit**: Number of records to fetch (default: 1000)
    - **offset**: Offset for pagination (default: 0)
    - **q**: SUITEQL filter query
    - **fields**: Comma-separated list of fields to return
    - **expandSubresources**: Whether to expand subresources
    - **expand**: Automatically fetch full details for each record (default: true)
    - **no_cache**: Skip cache
    """
    try:
        # Validate entity
        if not entity or len(entity) < 2:
            raise HTTPException(status_code=400, detail="Invalid entity name")

        # Build cache key
        cache_key = f"netsuite:{entity}:{limit}:{offset}:{q or ''}:{fields or ''}:{expand}"

        # Check cache
        if not no_cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.info(f"Returning cached data for entity: {entity}")
                return {
                    **cached_data,
                    "cached": True,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }

        # Initialize NetSuite client
        netsuite_client = NetSuiteClient(
            realm=settings.NETSUITE_REALM,
            consumer_key=settings.NETSUITE_CONSUMER_KEY,
            consumer_secret=settings.NETSUITE_CONSUMER_SECRET,
            token_key=settings.NETSUITE_TOKEN_KEY,
            token_secret=settings.NETSUITE_TOKEN_SECRET
        )

        # Build query params
        query_params = {"limit": limit, "offset": offset}
        if q:
            query_params["q"] = q
        if fields:
            query_params["fields"] = fields
        if expandSubresources:
            query_params["expandSubresources"] = expandSubresources

        # Fetch data from NetSuite
        logger.info(f"Fetching data from NetSuite - Entity: {entity}, Params: {query_params}, Expand: {expand}")
        data = await netsuite_client.get_records(entity, query_params, expand_details=expand)

        # Cache the result (5 minutes TTL)
        cache.set(cache_key, data, ttl=300)

        return {
            **data,
            "cached": False,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching NetSuite data: {str(e)}", exc_info=True)
        
        # Handle specific error types
        error_msg = str(e).lower()
        if "401" in error_msg or "authentication" in error_msg:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "Authentication Failed",
                    "message": "NetSuite authentication failed. Check credentials.",
                    "details": str(e) if settings.ENVIRONMENT == "development" else None
                }
            )
        
        if "404" in error_msg:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Not Found",
                    "message": f"Entity '{entity}' not found in NetSuite",
                    "details": str(e) if settings.ENVIRONMENT == "development" else None
                }
            )
        
        if "429" in error_msg or "rate limit" in error_msg:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate Limit Exceeded",
                    "message": "NetSuite rate limit exceeded. Please try again later.",
                    "details": str(e) if settings.ENVIRONMENT == "development" else None
                }
            )
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "message": "Failed to fetch data from NetSuite",
                "details": str(e) if settings.ENVIRONMENT == "development" else None
            }
        )


# FORMATTED ENDPOINTS FOR DATABASE-FRIENDLY RESPONSES
@app.get("/api/netsuite/{entity}/formatted", tags=["NetSuite - Formatted"])
@limiter.limit(f"{settings.RATE_LIMIT_MAX}/15minutes")
async def get_netsuite_records_formatted(
    request: Request,
    entity: str = Path(..., description="NetSuite entity type (customer, invoice, etc.)"),
    limit: int = Query(1000, description="Number of records to fetch"),
    offset: int = Query(0, description="Offset for pagination"),
    q: str = Query(None, description="SUITEQL filter query"),
    fields: str = Query(None, description="Comma-separated list of fields"),
    expandSubresources: str = Query(None, description="Expand subresources"),
    expand: bool = Query(True, description="Fetch full details for each record (default: true)"),
    no_cache: bool = Query(False, description="Skip cache"),
    format_type: str = Query("database", description="Format type: 'database', 'flat', or 'airbyte'"),
    api_key: str = Depends(verify_api_key)
):
    """
    Fetch records from NetSuite with formatted response (database-friendly).
    
    This endpoint returns only the data you need without extra metadata.
    
    **Format Types:**
    - `database`: Returns only the items array - perfect for direct database insertion
    - `flat`: Returns items with minimal metadata (entity, count)
    - `airbyte`: Returns records in Airbyte-compatible format
    
    **Other Parameters:**
    - **entity**: NetSuite entity type (customer, invoice, salesorder, etc.)
    - **limit**: Number of records to fetch (default: 1000)
    - **offset**: Offset for pagination (default: 0)
    - **q**: SUITEQL filter query
    - **fields**: Comma-separated list of fields to return
    - **expand**: Automatically fetch full details for each record (default: true)
    """
    try:
        # Validate entity
        if not entity or len(entity) < 2:
            raise HTTPException(status_code=400, detail="Invalid entity name")

        # Build cache key
        cache_key = f"netsuite_formatted:{entity}:{limit}:{offset}:{q or ''}:{fields or ''}:{expand}:{format_type}"

        # Check cache
        if not no_cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.info(f"Returning cached formatted data for entity: {entity}")
                return cached_data

        # Initialize NetSuite client
        netsuite_client = NetSuiteClient(
            realm=settings.NETSUITE_REALM,
            consumer_key=settings.NETSUITE_CONSUMER_KEY,
            consumer_secret=settings.NETSUITE_CONSUMER_SECRET,
            token_key=settings.NETSUITE_TOKEN_KEY,
            token_secret=settings.NETSUITE_TOKEN_SECRET
        )

        # Build query params
        query_params = {"limit": limit, "offset": offset}
        if q:
            query_params["q"] = q
        if fields:
            query_params["fields"] = fields
        if expandSubresources:
            query_params["expandSubresources"] = expandSubresources

        # Fetch data from NetSuite
        logger.info(f"Fetching formatted data from NetSuite - Entity: {entity}, Format: {format_type}")
        data = await netsuite_client.get_records(entity, query_params, expand_details=expand)

        # Apply formatting based on format_type
        if format_type == "database":
            # Return only the items array for direct database insertion
            formatted_data = transform_for_database(data)
        elif format_type == "flat":
            # Return items with minimal metadata
            formatted_data = flatten_netsuite_response(data, include_metadata=True)
        elif format_type == "airbyte":
            # Return Airbyte-compatible format
            formatted_data = format_response_for_airbyte(data)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid format_type '{format_type}'. Use 'database', 'flat', or 'airbyte'"
            )

        # Cache the result (5 minutes TTL)
        cache.set(cache_key, formatted_data, ttl=300)

        return formatted_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching formatted NetSuite data: {str(e)}", exc_info=True)
        
        # Handle specific error types
        error_msg = str(e).lower()
        if "401" in error_msg or "authentication" in error_msg:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "Authentication Failed",
                    "message": "NetSuite authentication failed. Check credentials.",
                    "details": str(e) if settings.ENVIRONMENT == "development" else None
                }
            )
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "message": "Failed to fetch formatted data from NetSuite",
                "details": str(e) if settings.ENVIRONMENT == "development" else None
            }
        )


@app.get("/api/netsuite/{entity}/database", tags=["NetSuite - Formatted"])
@limiter.limit(f"{settings.RATE_LIMIT_MAX}/15minutes")
async def get_netsuite_for_database(
    request: Request,
    entity: str = Path(..., description="NetSuite entity type"),
    limit: int = Query(1000, description="Number of records to fetch"),
    offset: int = Query(0, description="Offset for pagination"),
    q: str = Query(None, description="SUITEQL filter query"),
    fields: str = Query(None, description="Comma-separated list of fields"),
    expand: bool = Query(True, description="Fetch full details for each record"),
    no_cache: bool = Query(False, description="Skip cache"),
    api_key: str = Depends(verify_api_key)
):
    """
    Get NetSuite records formatted for direct database insertion.
    
    Returns ONLY the items array without any wrapper metadata.
    Perfect for importing directly into your database.
    """
    # Reuse the formatted endpoint with database format
    return await get_netsuite_records_formatted(
        request=request,
        entity=entity,
        limit=limit,
        offset=offset,
        q=q,
        fields=fields,
        expandSubresources=None,
        expand=expand,
        no_cache=no_cache,
        format_type="database",
        api_key=api_key
    )


@app.get("/api/netsuite/{entity}/airbyte", tags=["NetSuite - Formatted"])
@limiter.limit(f"{settings.RATE_LIMIT_MAX}/15minutes")
async def get_netsuite_for_airbyte(
    request: Request,
    entity: str = Path(..., description="NetSuite entity type"),
    limit: int = Query(1000, description="Number of records to fetch"),
    offset: int = Query(0, description="Offset for pagination"),
    q: str = Query(None, description="SUITEQL filter query"),
    fields: str = Query(None, description="Comma-separated list of fields"),
    expand: bool = Query(True, description="Fetch full details for each record"),
    no_cache: bool = Query(False, description="Skip cache"),
    api_key: str = Depends(verify_api_key)
):
    """
    Get NetSuite records formatted for Airbyte integration.
    
    Returns records in a structure that Airbyte can easily parse,
    with pagination information included.
    """
    # Reuse the formatted endpoint with airbyte format
    return await get_netsuite_records_formatted(
        request=request,
        entity=entity,
        limit=limit,
        offset=offset,
        q=q,
        fields=fields,
        expandSubresources=None,
        expand=expand,
        no_cache=no_cache,
        format_type="airbyte",
        api_key=api_key
    )


@app.get("/api/netsuite/{entity}/custom", tags=["NetSuite - Custom"])
@limiter.limit(f"{settings.RATE_LIMIT_MAX}/15minutes")
async def get_netsuite_custom_format(
    request: Request,
    entity: str = Path(..., description="NetSuite entity type"),
    limit: int = Query(10000, description="Number of records to fetch (default: 10000 for all)"),
    offset: int = Query(0, description="Offset for pagination"),
    user_id: int = Query(0, description="User ID for tracking"),
    fields: str = Query(None, description="Comma-separated list of fields to include"),
    q: str = Query(None, description="SUITEQL filter query"),
    expand: bool = Query(True, description="Fetch full details for each record"),
    no_cache: bool = Query(False, description="Skip cache"),
    api_key: str = Depends(verify_api_key)
):
    """
    Get NetSuite records with custom Vietnamese format.
    
    Returns structure: {success: true, user: X, count: Y, data: [...]}
    
    **Response Format:**
    ```json
    {
        "success": true,
        "user": 8,
        "count": 4760,
        "data": [
            {
                "Mã Đơn hàng": "001PMX36",
                "Đơn hàng": "SO-2601-104",
                "Ngày SO": "31/1/2026",
                "Kho hàng": "8 - Khác",
                "Hình thức bán hàng": "8 - Khác",
                "Mã khách hàng": "1718 - CUS2HCM8MY...",
                "Tên khách hàng": "CÔNG TY TNHH...",
                "Thành tiền (SO)": "26145934.00",
                ...
            }
        ]
    }
    ```
    
    **Parameters:**
    - **entity**: NetSuite entity type (customer, salesorder, invoice, etc.)
    - **limit**: Number of records (default: 10000 to get all data)
    - **offset**: Pagination offset
    - **user_id**: Your user ID for tracking
    - **fields**: Comma-separated fields to include (optional, default: all)
    - **expand**: Fetch full details (default: true)
    - **no_cache**: Skip cache
    """
    try:
        # Validate entity
        if not entity or len(entity) < 2:
            raise HTTPException(status_code=400, detail="Invalid entity name")

        # Build cache key
        cache_key = f"netsuite_custom:{entity}:{limit}:{offset}:{user_id}:{fields or ''}:{expand}"

        # Check cache
        if not no_cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.info(f"Returning cached custom format data for entity: {entity}")
                return cached_data

        # Initialize NetSuite client
        netsuite_client = NetSuiteClient(
            realm=settings.NETSUITE_REALM,
            consumer_key=settings.NETSUITE_CONSUMER_KEY,
            consumer_secret=settings.NETSUITE_CONSUMER_SECRET,
            token_key=settings.NETSUITE_TOKEN_KEY,
            token_secret=settings.NETSUITE_TOKEN_SECRET
        )

        # Build query params
        query_params = {"limit": limit, "offset": offset}
        if q:
            query_params["q"] = q
        if fields:
            query_params["fields"] = fields

        # Fetch data from NetSuite
        logger.info(f"Fetching custom format data from NetSuite - Entity: {entity}, User: {user_id}")
        data = await netsuite_client.get_records(entity, query_params, expand_details=expand)

        # Parse include_fields if provided
        include_fields_list = None
        if fields:
            include_fields_list = [f.strip() for f in fields.split(",")]

        # Apply custom formatting
        formatted_data = custom_format_response(
            data=data,
            user_id=user_id,
            include_fields=include_fields_list
        )

        # Cache the result (5 minutes TTL)
        cache.set(cache_key, formatted_data, ttl=300)

        return formatted_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching custom format NetSuite data: {str(e)}", exc_info=True)
        
        # Return error in same format
        return {
            "success": False,
            "user": user_id,
            "count": 0,
            "data": [],
            "error": str(e) if settings.ENVIRONMENT == "development" else "Failed to fetch data"
        }


@app.get("/api/reports/salesorder-lines", tags=["Reports - Custom"])
@limiter.limit(f"{settings.RATE_LIMIT_MAX}/15minutes")
async def get_salesorder_lines_report(
    request: Request,
    user_id: int = Query(8, description="User ID"),
    start_date: str = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(1000, description="Number of sales orders to fetch"),
    offset: int = Query(0, description="Offset for pagination"),
    no_cache: bool = Query(False, description="Skip cache"),
    api_key: str = Depends(verify_api_key)
):
    """
    Lấy chi tiết dòng (line items) của Sales Orders với các fields chuẩn.
    
    Mỗi line item sẽ là một record riêng biệt với đầy đủ thông tin từ:
    - Sales Order header (Đơn hàng, Ngày, Khách hàng, Kho...)
    - Line item details (Mã hàng, Số lượng, Đơn giá...)
    
    **Standard Fields (có sẵn):**
    - Kho hàng, Hình thức bán hàng, Class
    - Ngày SO, Đơn hàng SO, Mã DH (KD)
    - Tên khách hàng
    - Mã hàng, Số lượng, Đơn giá, Thành tiền (SO)
    - Tiền VAT, Tổng tiền gồm VAT
    - Diễn giải
    
    **Sẽ thêm sau (custom fields):**
    - Mô tả đầy đủ, Loại hàng, Mã thương mại, Tone màu
    - ĐVT, Quy cách, Chất lượng, Hệ số
    - Số chứng từ xuất, Ngày xuất, Biển số xe, Số lượng đã xuất
    """
    try:
        # Build cache key
        cache_key = f"report:so_lines:{user_id}:{start_date}:{end_date}:{limit}:{offset}"
        
        # Check cache
        if not no_cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.info(f"Returning cached sales order lines report")
                return cached_data

        # Initialize NetSuite client
        netsuite_client = NetSuiteClient(
            realm=settings.NETSUITE_REALM,
            consumer_key=settings.NETSUITE_CONSUMER_KEY,
            consumer_secret=settings.NETSUITE_CONSUMER_SECRET,
            token_key=settings.NETSUITE_TOKEN_KEY,
            token_secret=settings.NETSUITE_TOKEN_SECRET
        )

        # Build query params for sales orders
        query_params = {"limit": limit, "offset": offset}
        
        # Add date filters to query
        if start_date and end_date:
            query_params["q"] = f"tranDate BETWEEN '{start_date}' AND '{end_date}'"
        elif start_date:
            query_params["q"] = f"tranDate >= '{start_date}'"
        elif end_date:
            query_params["q"] = f"tranDate <= '{end_date}'"

        logger.info(f"Fetching sales orders - User: {user_id}, Limit: {limit}")
        
        # Fetch sales orders with full details
        data = await netsuite_client.get_records("salesorder", query_params, expand_details=True)
        
        items = data.get("items", [])
        flattened_lines = []
        
        # Flatten each sales order's line items
        for so in items:
            # Extract header info
            so_header = {
                "so_id": so.get("id", ""),
                "tranid": so.get("tranId", ""),
                "trandate": so.get("tranDate", ""),
                "otherrefnum": so.get("otherRefNum", ""),
                "entity_name": so.get("entity", {}).get("refName", ""),
                "location_name": so.get("location", {}).get("refName", ""),
                "class_name": so.get("class", {}).get("refName", ""),
                "department": so.get("department", {}).get("refName", ""),
                "status": so.get("status", {}).get("refName", "") if isinstance(so.get("status"), dict) else so.get("status", ""),
                "total": so.get("total", ""),
                "subtotal": so.get("subtotal", ""),
                "taxtotal": so.get("taxTotal", ""),
                "memo": so.get("memo", ""),
            }
            
            # Get line items (item sublist)
            line_items = so.get("item", {})
            if isinstance(line_items, dict):
                line_items_list = line_items.get("items", [])
            else:
                line_items_list = []
            
            # If no line items found, create one record with header data only
            if not line_items_list:
                record = {
                    "Đơn hàng": so_header["tranid"],
                    "Ngày SO": so_header["trandate"],
                    "Mã DH (KD)": so_header["otherrefnum"],
                    "Tên khách hàng": so_header["entity_name"],
                    "Kho hàng": so_header["location_name"],
                    "Hình thức bán hàng": so_header["class_name"],
                    "Class": so_header["class_name"],
                    "Bộ phận": so_header["department"],
                    "Trạng thái": so_header["status"],
                    "Mã hàng": "",
                    "Mô tả đầy đủ": "",
                    "Loại hàng": "",
                    "Số lượng": "",
                    "Đơn giá": "",
                    "Thành tiền (SO)": "",
                    "ĐVT": "",
                    "Tiền VAT": so_header["taxtotal"],
                    "Tổng tiền gồm VAT": so_header["total"],
                    "Diễn giải": so_header["memo"],
                }
                flattened_lines.append(record)
            else:
                # Create one record per line item
                for line in line_items_list:
                    # Extract item info
                    item_ref = line.get("item", {})
                    item_name = item_ref.get("refName", "") if isinstance(item_ref, dict) else ""
                    
                    record = {
                        "Đơn hàng": so_header["tranid"],
                        "Ngày SO": so_header["trandate"],
                        "Mã DH (KD)": so_header["otherrefnum"],
                        "Tên khách hàng": so_header["entity_name"],
                        "Kho hàng": so_header["location_name"],
                        "Hình thức bán hàng": so_header["class_name"],
                        "Class": so_header["class_name"],
                        "Bộ phận": so_header["department"],
                        "Trạng thái": so_header["status"],
                        
                        # Line item details
                        "Mã hàng": item_name,  # This is item refName (ID-Name format)
                        "Mô tả đầy đủ": line.get("description", ""),
                        "Loại hàng": "",  # Will add later with item master lookup
                        "Số lượng": line.get("quantity", ""),
                        "Đơn giá": line.get("rate", ""),
                        "Thành tiền (SO)": line.get("amount", ""),
                        "ĐVT": line.get("units", {}).get("refName", "") if isinstance(line.get("units"), dict) else "",
                        
                        # Financial (from header, repeated for each line)
                        "Tiền VAT": so_header["taxtotal"],
                        "Tổng tiền gồm VAT": so_header["total"],
                        "Diễn giải": so_header["memo"],
                        
                        # Placeholder for custom fields (to be added later)
                        "Mã thương mại": "",
                        "Tone màu": "",
                        "Tone màu (ITF)": "",
                        "Chất lượng": "",
                        "Quy cách": "",
                        "Hệ số": "",
                        "Hệ số CT": "",
                        
                        # Placeholder for fulfillment fields (to be added later)
                        "Số chứng từ xuất": "",
                        "Ngày xuất": "",
                        "Biển số xe": "",
                        "Số lượng đã xuất (TẤM)": "",
                        "Số lượng đã xuất (m2)": "",
                        "SL xuất CT m2": "",
                        "Số Lot": "",
                        "Nghiệp vụ xuất": "",
                        "Thành tiền (lxuất)": "",
                    }
                    
                    flattened_lines.append(record)
        
        result = {
            "success": True,
            "user": user_id,
            "count": len(flattened_lines),
            "data": flattened_lines
        }
        
        # Cache for 5 minutes
        cache.set(cache_key, result, ttl=300)
        
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing sales order lines report: {str(e)}", exc_info=True)
        return {
            "success": False,
            "user": user_id,
            "count": 0,
            "data": [],
            "error": str(e) if settings.ENVIRONMENT == "development" else "Failed to generate report"
        }


@app.get("/api/reports/salesorder-detail", tags=["Reports - Custom"])
@limiter.limit(f"{settings.RATE_LIMIT_MAX}/15minutes")
async def get_salesorder_detail_report(
    request: Request,
    user_id: int = Query(8, description="User ID"),
    start_date: str = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(None, description="End date (YYYY-MM-DD)"),
    location_id: str = Query(None, description="Location/Warehouse ID filter"),
    limit: int = Query(10000, description="Number of records"),
    offset: int = Query(0, description="Offset for pagination"),
    no_cache: bool = Query(False, description="Skip cache"),
    api_key: str = Depends(verify_api_key)
):
    """
    Báo cáo chi tiết đơn hàng (JOIN Sales Order + Item Fulfillment + Items).
    
    Trả về data đã JOIN từ nhiều bảng với các cột:
    - Thông tin đơn hàng (SO)
    - Thông tin khách hàng
    - Thông tin sản phẩm
    - Thông tin xuất kho (Item Fulfillment)
    - Các custom fields
    
    **Response Format:**
    ```json
    {
        "success": true,
        "user": 8,
        "count": 4760,
        "data": [
            {
                "Kho hàng": "8 - Khác",
                "Hình thức bán hàng": "8 - Khác",
                "Ngày SO": "31/1/2026",
                "Đơn hàng": "SO-2601-104",
                "Mã DH (KD)": "001PMX36",
                "Tên khách hàng": "CÔNG TY TNHH...",
                "Mã hàng": "125",
                "Loại Hàng": "Inventory Item",
                "Số lượng": "100",
                "Đơn giá": "261459.34",
                "Thành tiền (SO)": "26145934.00",
                ...
            }
        ]
    }
    ```
    """
    try:
        # Build cache key
        cache_key = f"report:so_detail:{user_id}:{start_date}:{end_date}:{location_id}:{limit}:{offset}"
        
        # Check cache
        if not no_cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.info(f"Returning cached sales order report")
                return cached_data

        # Initialize NetSuite client
        netsuite_client = NetSuiteClient(
            realm=settings.NETSUITE_REALM,
            consumer_key=settings.NETSUITE_CONSUMER_KEY,
            consumer_secret=settings.NETSUITE_CONSUMER_SECRET,
            token_key=settings.NETSUITE_TOKEN_KEY,
            token_secret=settings.NETSUITE_TOKEN_SECRET
        )

        # Build SuiteQL query to JOIN multiple tables
        # Note: NetSuite SuiteQL uses specific table names
        query = """
            SELECT
                t.id,
                t.tranid,
                t.trandate,
                t.otherrefnum,
                c.entityid,
                c.companyname,
                l.name as location_name,
                tl.item,
                tl.quantity,
                tl.rate,
                tl.amount
            FROM 
                Transaction t
                INNER JOIN TransactionLine tl ON t.id = tl.transaction
                LEFT JOIN Customer c ON t.entity = c.id
                LEFT JOIN Location l ON t.location = l.id
            WHERE 
                t.type = 'SalesOrd'
        """
        
        # Add date filter if provided
        if start_date:
            query += f" AND SO.trandate >= TO_DATE('{start_date}', 'YYYY-MM-DD')"
        if end_date:
            query += f" AND SO.trandate <= TO_DATE('{end_date}', 'YYYY-MM-DD')"
        if location_id:
            query += f" AND SO.location = {location_id}"
            
        query += f" ORDER BY SO.trandate DESC, SO.id DESC"

        logger.info(f"Executing SalesOrder detail report - User: {user_id}, Date range: {start_date} to {end_date}")
        
        # Execute SuiteQL query
        suiteql_result = await netsuite_client.execute_suiteql(query, limit=limit, offset=offset)
        
        # Transform to Vietnamese field names
        items = suiteql_result.get("items", [])
        transformed_items = []
        
        for item in items:
            transformed_item = {
                "ID": item.get("id", ""),
                "Đơn hàng": item.get("tranid", ""),
                "Ngày SO": item.get("trandate", ""),
                "Mã DH (KD)": item.get("otherrefnum", ""),
                "Mã khách hàng": item.get("entityid", ""),
                "Tên khách hàng": item.get("companyname", ""),
                "Kho hàng": item.get("location_name", ""),
                "Mã Item": item.get("item", ""),
                "Số lượng": item.get("quantity", ""),
                "Đơn giá": item.get("rate", ""),
                "Thành tiền (SO)": item.get("amount", ""),
            }
            transformed_items.append(transformed_item)
        
        result = {
            "success": True,
            "user": user_id,
            "count": len(transformed_items),
            "data": transformed_items
        }
        
        # Cache for 5 minutes
        cache.set(cache_key, result, ttl=300)
        
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing sales order report: {str(e)}", exc_info=True)
        return {
            "success": False,
            "user": user_id,
            "count": 0,
            "data": [],
            "error": str(e) if settings.ENVIRONMENT == "development" else "Failed to generate report"
        }



@app.post("/api/netsuite/{entity}/query", tags=["NetSuite"])
@limiter.limit(f"{settings.RATE_LIMIT_MAX}/15minutes")
async def execute_suiteql_query(
    request: Request,
    entity: str = Path(..., description="NetSuite entity type"),
    query: dict = None,
    api_key: str = Depends(verify_api_key)
):
    """
    Execute custom SuiteQL query
    
    Request body:
    - **query**: SuiteQL query string
    - **limit**: Number of records (default: 1000)
    - **offset**: Offset for pagination (default: 0)
    """
    try:
        if not query or "query" not in query:
            raise HTTPException(status_code=400, detail="Query is required")

        netsuite_client = NetSuiteClient(
            realm=settings.NETSUITE_REALM,
            consumer_key=settings.NETSUITE_CONSUMER_KEY,
            consumer_secret=settings.NETSUITE_CONSUMER_SECRET,
            token_key=settings.NETSUITE_TOKEN_KEY,
            token_secret=settings.NETSUITE_TOKEN_SECRET
        )

        limit = query.get("limit", 1000)
        offset = query.get("offset", 0)
        
        logger.info(f"Executing SuiteQL query: {query['query']}")
        data = await netsuite_client.execute_suiteql(query["query"], limit, offset)

        return {
            **data,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing SuiteQL query: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "message": "Failed to execute query",
                "details": str(e) if settings.ENVIRONMENT == "development" else None
            }
        )


@app.delete("/api/netsuite/cache", tags=["NetSuite"])
async def clear_cache(
    api_key: str = Depends(verify_api_key)
):
    """Clear cache"""
    stats = cache.get_stats()
    cache.clear()
    logger.info("Cache cleared")
    return {
        "message": "Cache cleared successfully",
        "previousStats": stats
    }


# 404 handler
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "The requested endpoint does not exist"
        }
    )


# Generic error handler
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An error occurred" if settings.ENVIRONMENT == "production" else str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development"
    )
