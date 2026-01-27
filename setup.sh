#!/bin/bash

# NetSuite Proxy API - Quick Start Script

set -e

echo "🚀 NetSuite Proxy API - Quick Start"
echo "======================================"
echo ""
echo "Choose setup method:"
echo "1) Local Python setup"
echo "2) Docker setup"
read -p "Enter choice [1-2]: " choice

case $choice in
  1)
    echo ""
    echo "🐍 Setting up Python environment..."
    cd python
    
    # File .env đã được tạo sẵn, không cần edit
    if [ ! -f .env ]; then
      echo "Creating .env file..."
      cp .env.example .env
    fi
    
    # Create virtual environment
    if [ ! -d venv ]; then
      echo "Creating virtual environment..."
      python3 -m venv venv
    fi
    
    # Activate and install
    echo "Installing dependencies..."
    source venv/bin/activate
    pip install -r requirements.txt
    
    echo ""
    echo "✅ Setup complete!"
    echo ""
    echo "To start the server:"
    echo "  cd python"
    echo "  source venv/bin/activate"
    echo "  python main.py"
    echo ""
    echo "Or with uvicorn:"
    echo "  uvicorn main:app --reload"
    echo ""
    echo "API will be available at: http://localhost:8000"
    echo "API Key: netsuite_proxy_api_key_2026_secure"
    ;;
    
  2)
    echo ""
    echo "🐳 Setting up Docker..."
    
    # File .env đã tạo sẵn
    if [ ! -f python/.env ]; then
      echo "Creating python/.env..."
      cp python/.env.example python/.env
    fi
    
    # Build and start
    echo "Building and starting container..."
    docker-compose up -d --build
    
    echo ""
    echo "✅ Setup complete!"
    echo ""
    echo "API is running at: http://localhost:8000"
    echo "API Key: netsuite_proxy_api_key_2026_secure"
    echo ""
    echo "To view logs:"
    echo "  docker-compose logs -f"
    echo ""
    echo "To stop:"
    echo "  docker-compose down"
    ;;
    
  *)
    echo "Invalid choice"
    exit 1
    ;;
esac

echo ""
echo "📚 Documentation:"
echo "  - README.md - General documentation"
echo "  - docs/AIRBYTE_SETUP.md - Airbyte integration guide"
echo "  - docs/API_EXAMPLES.md - API usage examples"
echo ""
echo "🔍 Next steps:"
echo "  1. Test the API: curl http://localhost:8000/health"
echo "  2. Configure Airbyte using docs/AIRBYTE_SETUP.md"
echo "  3. Start syncing data!"
echo ""
