# 📋 DANH SÁCH FIELDS CẦN THIẾT

## Fields Bạn Cần vs NetSuite Fields

| Vietnamese Name | NetSuite Field | Source Table | Notes |
|----------------|---------------|--------------|-------|
| **Sales Order Header** ||||
| Kho hàng | location.name | Transaction | ✅ Available |
| Hình thức bán hàng | class.name | Transaction | ✅ Available (Classification) |
| Class | class.name | Transaction | ✅ Same as above |
| Ngày SO | trandate | Transaction | ✅ Available |
| Đơn hàng SO | tranid | Transaction | ✅ Available |
| Mã DH (KD) | otherrefnum | Transaction | ✅ Custom ref number |
| Tên khách hàng | entity.companyname | Customer | ✅ Available via JOIN |
| Diễn giải | memo | Transaction | ✅ Available |
| Tiền VAT | taxtotal | Transaction | ✅ Available |
| Tổng tiền gồm VAT | total | Transaction | ✅ Available |
||||
| **Line Item Fields** ||||
| Mã hàng | item.itemid | Item | ⚠️ Need JOIN to Item |
| Mô tả đầy đủ | item. displayname | Item | ⚠️ Need JOIN to Item |
| Loại hàng | item.itemtype | Item | ⚠️ Need JOIN to Item |
| Số lượng | quantity | TransactionLine | ✅ Available |
| Đơn giá | rate | TransactionLine | ✅ Available |  
| Thành tiền (SO) | amount | TransactionLine | ✅ Available |
| ĐVT | units | TransactionLine | ⚠️ May need custom field |
||||
| **Custom Fields (Item)** ||||
| Mã thương mại | custitem_xxx | Item | ❓ Need actual field name |
| Tone màu | custitem_xxx | Item | ❓ Need actual field name |
| Chất lượng | custitem_xxx | Item | ❓ Need actual field name |
| Quy cách | custitem_xxx | Item | ❓ Need actual field name |
| Hệ số | custitem_xxx | Item | ❓ Need actual field name |
||||
| **Item Fulfillment Fields** ||||
| Số chứng từ xuất | tranid | Transaction (ItemShip) | ⚠️ Need LEFT JOIN to IF |
| Ngày xuất | trandate | Transaction (ItemShip) | ⚠️ Need LEFT JOIN to IF |
| Số lượng đã xuất (TẤM) | quantity | TransactionLine (IF) | ⚠️ Need LEFT JOIN |
| Số lượng đã xuất (m2) | custcol_xxx | TransactionLine (IF) | ❓ Need actual field name |
| Biển số xe | custbody_xxx | Transaction (IF) | ❓ Need actual field name |
| Số Lot | custcol_xxx | TransactionLine | ❓ Need actual field name |
| Nghiệp vụ xuất | custcol_xxx | TransactionLine (IF) | ❓ Need actual field name |
| Thành tiền (lxuất) | amount | TransactionLine (IF) | ⚠️ Need calculation |
||||
| **Custom Fields (Line Level)** ||||
| Tone màu (ITF) | custcol_xxx | TransactionLine (IF) | ❓ Need actual field name |
| Hệ số CT | custcol_xxx | TransactionLine | ❓ Need actual field name |
| SL xuất CT m2 | custcol_xxx | TransactionLine (IF) | ❓ Need actual field name |

---

## 🔍 Vấn Đề Chính

### 1. **Custom Field Names Không Rõ**
Các fields custom như:
- `Mã thương mại`
- `Tone màu`
- `Biển số xe`
- `Số Lot`
- etc.

Cần biết **tên field thực tế** trong NetSuite (ví dụ: `custitem_btm_tone_mau`)

### 2. **Data Từ Nhiều Nguồn**
- Sales Order (header)
- Sales Order Lines (items)
- Item Master (product info)
- Item Fulfillment (phiếu xuất)
- Item Fulfillment Lines

Cần **JOIN 4-5 tables** → SuiteQL query sẽ rất phức tạp

---

## 💡 Giải Pháp

### Option 1: Dùng NetSuite Saved Search (KHUYẾN NGHỊ ⭐)
1. Tạo Saved Search trong NetSuite UI
2. Add tất cả columns bạn cần
3. Export hoặc schedule email report
4. Hoặc access via SuiteAnalytics Connect

**Ưu điểm:**
- ✅ UI-driven, không cần code
- ✅ Có đủ tất cả fields
- ✅ NetSuite tự optimize query
- ✅ Có thể filter, sort dễ dàng

### Option 2: SuiteQL Query Hoàn Chỉnh
Tôi cần bạn cung cấp:
1. **Tên chính xác** của custom fields (check trong NetSuite → Customization → Fields)
2. Confirm xem có quyền access các bảng không

### Option 3: Multiple API Calls + Merge
1. Call `/salesorder` → Lấy SO data
2. Call `/itemfulfillment` → Lấy IF data  
3. Call `/item` → Lấy item details
4. Merge data ở code

---

## 🎯 Next Steps

### Bước 1: Xác Định Custom Field Names
Vào NetSuite → Customization → Lists, Records, & Fields → Item Fields
Tìm các fields:
- Mã thương mại
- Tone màu
- Chất lượng
- Quy cách

Copy **Field ID** (ví dụ: `custitem_btm_ma_thuong_mai`)

### Bước 2: Xác Định Transaction Line Custom Fields
Vào Customization → Transaction Body Fields / Transaction Line Fields
Tìm:
- Biển số xe
- Số Lot
- Tone màu (ITF)
- Hệ số CT

### Bước 3: Build Query
Sau khi có field names, tôi sẽ viết SuiteQL query chính xác.

---

## ❓ Câu Hỏi Cho Bạn

1. Bạn có quyền access NetSuite UI để check custom field names không?
2. Bạn muốn tôi hướng dẫn tạo Saved Search (đơn giản hơn)?
3. Hay bạn muốn tiếp tục với SuiteQL approach (phức tạp hơn, cần field names)?

**Tôi khuyến nghị Option 1 (Saved Search) nếu bạn cần data ngay!**
