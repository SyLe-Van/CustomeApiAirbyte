"""
Data formatting utilities for transforming NetSuite responses
"""
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


def flatten_netsuite_response(data: Dict[str, Any], include_metadata: bool = False) -> Dict[str, Any]:
    """
    Flatten NetSuite response to extract only the items data.
    
    Args:
        data: Raw NetSuite response
        include_metadata: Whether to include basic metadata (count, entity)
        
    Returns:
        Flattened response with items array
    """
    items = data.get("items", [])
    
    if include_metadata:
        return {
            "entity": data.get("entity"),
            "count": len(items),
            "data": items
        }
    
    return {
        "data": items
    }


def transform_for_database(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Transform NetSuite response into database-friendly format.
    Returns only the items array, removing all wrapper metadata.
    
    Args:
        data: Raw NetSuite response
        
    Returns:
        List of records ready for database insertion
    """
    items = data.get("items", [])
    
    # Return the items array directly for easy database insertion
    return items


def clean_record(record: Dict[str, Any], exclude_fields: List[str] = None) -> Dict[str, Any]:
    """
    Clean a single record by removing specified fields.
    
    Args:
        record: Single record to clean
        exclude_fields: List of field names to exclude
        
    Returns:
        Cleaned record
    """
    if exclude_fields is None:
        exclude_fields = []
    
    return {k: v for k, v in record.items() if k not in exclude_fields}


def format_response_for_airbyte(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format response specifically for Airbyte integration.
    This returns a simple structure that Airbyte can easily parse.
    
    Args:
        data: Raw NetSuite response
        
    Returns:
        Airbyte-friendly response with records array
    """
    items = data.get("items", [])
    has_more = data.get("hasMore", False)
    offset = data.get("offset", 0)
    limit = data.get("limit", 1000)
    
    # Airbyte expects a simple structure
    return {
        "records": items,
        "pagination": {
            "has_more": has_more,
            "next_offset": offset + limit if has_more else None,
            "count": len(items)
        }
    }
