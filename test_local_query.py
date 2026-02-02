#!/usr/bin/env python3
"""
Test SuiteQL query locally before deploying
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent / "python"))

from app.services.netsuite import NetSuiteClient
from app.config import settings

async def test_salesorder_query():
    """Test the sales order query"""
    
    print("=" * 80)
    print("🧪 TESTING SUITEQL QUERY LOCALLY")
    print("=" * 80)
    print()
    
    # Initialize NetSuite client
    print("📡 Connecting to NetSuite...")
    print(f"   Realm: {settings.NETSUITE_REALM}")
    print()
    
    try:
        client = NetSuiteClient(
            realm=settings.NETSUITE_REALM,
            consumer_key=settings.NETSUITE_CONSUMER_KEY,
            consumer_secret=settings.NETSUITE_CONSUMER_SECRET,
            token_key=settings.NETSUITE_TOKEN_KEY,
            token_secret=settings.NETSUITE_TOKEN_SECRET
        )
        
        # Build query
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
            ORDER BY t.trandate DESC
        """
        
        print("📋 Executing query...")
        print("-" * 80)
        print(query)
        print("-" * 80)
        print()
        
        # Execute query
        result = await client.execute_suiteql(query, limit=3, offset=0)
        
        print("✅ Query executed successfully!")
        print()
        print(f"📊 Results:")
        print(f"   Count: {result.get('count', 0)}")
        print(f"   Has More: {result.get('hasMore', False)}")
        print()
        
        items = result.get("items", [])
        
        if items:
            print("📝 Sample records:")
            print()
            
            for i, item in enumerate(items[:3], 1):
                print(f"Record {i}:")
                print("-" * 40)
                
                # Transform to Vietnamese
                transformed = {
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
                
                for key, value in transformed.items():
                    print(f"  {key:20s}: {value}")
                print()
        else:
            print("⚠️  No records found")
        
        print("=" * 80)
        print("✅ TEST COMPLETED SUCCESSFULLY!")
        print()
        
        # Show formatted response
        response = {
            "success": True,
            "user": 8,
            "count": len(items),
            "data": [
                {
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
                for item in items
            ]
        }
        
        print("📦 Formatted API Response:")
        print("-" * 80)
        import json
        print(json.dumps(response, indent=2, ensure_ascii=False))
        print()
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print("❌ ERROR!")
        print("-" * 80)
        print(f"Error: {str(e)}")
        print()
        print(f"Error Type: {type(e).__name__}")
        
        import traceback
        print()
        print("Full Traceback:")
        print(traceback.format_exc())
        print("=" * 80)
        
        return False

if __name__ == "__main__":
    success = asyncio.run(test_salesorder_query())
    sys.exit(0 if success else 1)
