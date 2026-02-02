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


def custom_format_response(
    data: Dict[str, Any], 
    user_id: int = None,
    field_mapping: Dict[str, str] = None,
    include_fields: List[str] = None
) -> Dict[str, Any]:
    """
    Format response with custom structure and Vietnamese field names.
    Returns: {success, user, count, data: [...]}
    
    Args:
        data: Raw NetSuite response
        user_id: Optional user ID
        field_mapping: Custom field name mapping (NetSuite field -> Display name)
        include_fields: List of NetSuite fields to include (None = all fields)
        
    Returns:
        Custom formatted response
    """
    items = data.get("items", [])
    
    # Default field mapping for Sales Orders (tiếng Việt)
    default_mapping = {
        # Basic info
        "id": "Mã Đơn hàng",
        "tranId": "Đơn hàng",
        "tranDate": "Ngày SO",
        "entity": "Mã khách hàng",
        "entityName": "Tên khách hàng",
        
        # Sales info
        "salesRep": "Nhân viên bán hàng",
        "department": "Bộ phận",
        "location": "Kho hàng",
        "salesType": "Hình thức bán hàng",
        
        # Financial
        "amount": "Thành tiền (SO)",
        "total": "Tổng tiền gồm VAT",
        "subTotal": "Số Lớt",
        "taxRate": "Tiền VAT",
        "discountRate": "Chiết khấu",
        "discountAmount": "Tiền chiết khấu",
        
        # Status
        "status": "Trạng thái",
        "orderType": "Loại đơn hàng",
        "creditHold": "Hold tín dụng",
        
        # Dates
        "shipDate": "Ngày ITF",
        "expectedShipDate": "Ngày dự kiến giao",
        "createdDate": "Ngày tạo",
        "lastModifiedDate": "Ngày cập nhật",
        
        # Other
        "memo": "Ghi chú",
        "terms": "Điều khoản thanh toán",
        "shipMethod": "Phương thức vận chuyển",
        "otherRefNum": "Số tham chiếu",
    }
    
    # Use provided mapping or default
    mapping = field_mapping if field_mapping else default_mapping
    
    # Transform items
    transformed_items = []
    for item in items:
        transformed_item = {}
        
        # If include_fields specified, only include those
        fields_to_process = include_fields if include_fields else item.keys()
        
        for field in fields_to_process:
            if field in item:
                # Use mapped name if available, otherwise use original
                display_name = mapping.get(field, field)
                value = item[field]
                
                # Extract nested values if needed
                if isinstance(value, dict):
                    # For entity/reference objects, try to get refName or id
                    if "refName" in value:
                        transformed_item[display_name] = value["refName"]
                    elif "id" in value:
                        transformed_item[display_name] = value["id"]
                    else:
                        transformed_item[display_name] = value
                else:
                    transformed_item[display_name] = value
        
        transformed_items.append(transformed_item)
    
    return {
        "success": True,
        "user": user_id if user_id else 0,
        "count": len(transformed_items),
        "data": transformed_items
    }


def extract_simple_fields(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract simple/flat fields from a NetSuite record.
    Converts nested objects to their simple representations.
    
    Args:
        record: NetSuite record
        
    Returns:
        Flattened record with simple values
    """
    simple_record = {}
    
    for key, value in record.items():
        if isinstance(value, dict):
            # Handle reference objects (entity, department, etc.)
            if "refName" in value:
                simple_record[key] = value["refName"]
            elif "id" in value:
                simple_record[key] = value["id"]
            elif "name" in value:
                simple_record[key] = value["name"]
            else:
                # Keep as is for complex nested objects
                simple_record[key] = value
        elif isinstance(value, list):
            # Keep lists as is (like line items)
            simple_record[key] = value
        else:
            # Simple values
            simple_record[key] = value
    
    return simple_record
