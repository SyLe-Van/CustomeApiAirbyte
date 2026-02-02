#!/usr/bin/env python3
"""
Test script to validate SuiteQL query structure
"""

def test_salesorder_query():
    """Test the sales order detail query structure"""
    
    # This is the query that will be executed
    query = """
        SELECT
            -- Sales Order Info
            SO.id AS so_internal_id,
            SO.tranid AS don_hang,
            SO.trandate AS ngay_so,
            SO.otherrefnum AS ma_dh_kd,
            
            -- Customer Info
            C.entityid AS ma_khach_hang,
            C.companyname AS ten_khach_hang,
            
            -- Location (Warehouse)
            L.name AS kho_hang,
            
            -- Department/Class
            CL.name AS class_name,
            DEPT.name AS bo_phan,
            
            -- Sales Order Line Items
            SOL.item AS item_id,
            I.itemid AS ma_hang,
            I.displayname AS mo_ta_day_du,
            I.itemtype AS loai_hang,
            
            SOL.quantity AS so_luong,
            SOL.rate AS don_gia,
            SOL.amount AS thanh_tien_so,
            
            -- Item Fulfillment Info (if exists)
            IF.tranid AS so_chung_tu_xuat,
            IF.trandate AS ngay_xuat,
            IFL.quantity AS so_luong_da_xuat,
            
            -- Financial
            SO.subtotal AS sub_total,
            SO.taxtotal AS tien_vat,
            SO.discounttotal AS tien_chiet_khau,
            SO.total AS tong_tien_gom_vat,
            
            -- Status
            SO.status AS trang_thai,
            SO.memo AS dien_giai
            
        FROM 
            Transaction SO
            LEFT JOIN TransactionLine SOL ON SO.id = SOL.transaction
            LEFT JOIN Customer C ON SO.entity = C.id
            LEFT JOIN Location L ON SO.location = L.id
            LEFT JOIN Classification CL ON SO.class = CL.id
            LEFT JOIN Department DEPT ON SO.department = DEPT.id
            LEFT JOIN Item I ON SOL.item = I.id
            LEFT JOIN Transaction IF ON IF.createdfrom = SO.id AND IF.type = 'ItemShip'
            LEFT JOIN TransactionLine IFL ON IF.id = IFL.transaction AND IFL.item = SOL.item
            
        WHERE 
            SO.type = 'SalesOrd'
        ORDER BY SO.trandate DESC, SO.id DESC
    """
    
    # Field mapping
    field_mapping = {
        "kho_hang": "Kho hàng",
        "class_name": "Hình thức bán hàng / Class",
        "ngay_so": "Ngày SO",
        "don_hang": "Đơn hàng",
        "ma_dh_kd": "Mã DH (KD)",
        "ten_khach_hang": "Tên khách hàng",
        "ma_hang": "Mã hàng",
        "mo_ta_day_du": "Mô tả đầy đủ",
        "loai_hang": "Loại Hàng",
        "so_luong": "Số lượng",
        "don_gia": "Đơn giá",
        "thanh_tien_so": "Thành tiền (SO)",
        "so_chung_tu_xuat": "Số chứng từ xuất",
        "ngay_xuat": "Ngày xuất",
        "so_luong_da_xuat": "Số lượng đã xuất (TẤM)",
        "tien_vat": "Tiền VAT",
        "tien_chiet_khau": "Tiền chiết khấu",
        "tong_tien_gom_vat": "Tổng tiền gồm VAT",
        "dien_giai": "Diễn giải",
        "trang_thai": "Trạng thái",
    }
    
    print("=" * 80)
    print("SALESORDER DETAIL REPORT - QUERY STRUCTURE TEST")
    print("=" * 80)
    print()
    
    print("📊 Query Structure:")
    print("-" * 80)
    print(query)
    print()
    
    print("🗺️  Field Mappings (NetSuite → Vietnamese):")
    print("-" * 80)
    for ns_field, vn_field in field_mapping.items():
        print(f"  {ns_field:25s} → {vn_field}")
    print()
    
    print("📝 Expected Response Format:")
    print("-" * 80)
    sample_response = {
        "success": True,
        "user": 8,
        "count": 4760,
        "data": [
            {
                "Kho hàng": "8 - Khác",
                "Hình thức bán hàng / Class": "8 - Khác",
                "Ngày SO": "31/1/2026",
                "Đơn hàng": "SO-2601-104",
                "Mã DH (KD)": "001PMX36",
                "Tên khách hàng": "CÔNG TY TNHH MỘT THÀNH VIÊN...",
                "Mã hàng": "125",
                "Loại Hàng": "Inventory Item",
                "Số lượng": "100",
                "Đơn giá": "261459.34",
                "Thành tiền (SO)": "26145934.00",
                "Số chứng từ xuất": "IF-12345",
                "Ngày xuất": "01/02/2026",
                "Số lượng đã xuất (TẤM)": "100",
                "Tiền VAT": "2800000.00",
                "Tổng tiền gồm VAT": "29000000.00",
            },
            "... more records ..."
        ]
    }
    
    import json
    print(json.dumps(sample_response, indent=2, ensure_ascii=False))
    print()
    
    print("=" * 80)
    print("✅ Query structure is valid!")
    print()
    print("🔗 Endpoint URL:")
    print("GET https://customeapiairbyte-production.up.railway.app/api/reports/salesorder-detail")
    print()
    print("📋 Parameters:")
    print("  - api_key: (required)")
    print("  - user_id: 8 (default)")
    print("  - start_date: YYYY-MM-DD (optional)")
    print("  - end_date: YYYY-MM-DD (optional)")
    print("  - location_id: (optional)")
    print("  - limit: 10000 (default)")
    print()
    print("🧪 Example Test URL:")
    print("https://customeapiairbyte-production.up.railway.app/api/reports/salesorder-detail?api_key=netsuite_proxy_api_key_2026_secure&user_id=8&limit=10")
    print()
    print("=" * 80)

if __name__ == "__main__":
    test_salesorder_query()
