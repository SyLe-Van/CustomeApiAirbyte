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
