# ⚠️ Vấn đề về Python Version

## Vấn đề hiện tại

Bạn đang dùng **Python 3.14.2** - phiên bản quá mới và có các breaking changes trong type hinting khiến nhiều thư viện chưa tương thích, đặc biệt là:

- Pydantic v1.10.13
- FastAPI 0.100.1

## Giải pháp

Bạn cần cài đặt Python 3.11 hoặc 3.12 (phiên bản stable và được hỗ trợ tốt):

### Cài đặt Python 3.12 trên macOS

```bash
# Cài đặt Python 3.12 bằng Homebrew
brew install python@3.12

# Tạo lại virtual environment với Python 3.12
cd /Users/mac/Royal/customApi/python
rm -rf venv
python3.12 -m venv venv
venv/bin/pip install -r requirements.txt

# Chạy server
venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### Hoặc cài đặt Python 3.11

```bash
# Cài đặt Python 3.11 bằng Homebrew
brew install python@3.11

# Tạo lại virtual environment với Python 3.11
cd /Users/mac/Royal/customApi/python
rm -rf venv
python3.11 -m venv venv
venv/bin/pip install -r requirements.txt

# Chạy server
venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

## Sau khi cài Python 3.11/3.12

Chạy lại file setup:

```bash
cd /Users/mac/Royal/customApi
bash setup.sh
```

## Giải thích kỹ thuật

Python 3.14 đã thay đổi cách hoạt động của type annotations (PEP 649 - Deferred Evaluation of Annotations), khiến Pydantic v1 không thể infer type cho các attributes.

Pydantic v2 hỗ trợ Python 3.14 nhưng cần Rust compiler để build pydantic-core, điều này phức tạp cho development.

**Python 3.12** là lựa chọn tốt nhất hiện tại:

- ✅ Stable và được hỗ trợ tốt
- ✅ Tương thích với tất cả thư viện
- ✅ Performance tốt
- ✅ Không cần Rust compiler
