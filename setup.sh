#!/usr/bin/env bash
# One-command setup for AI Finance Manager (Mac/Linux)
# Usage: chmod +x setup.sh && ./setup.sh

set -e

echo "=================================================="
echo " AI Finance Manager - Automated Setup"
echo "=================================================="

# 1. Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "[1/6] Creating virtual environment..."
    python3 -m venv venv
else
    echo "[1/6] Virtual environment already exists, skipping."
fi

# 2. Activate it
source venv/bin/activate

# 3. Install requirements
echo "[2/6] Installing dependencies (this may take a minute)..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

# 4. Migrations
echo "[3/6] Creating database tables..."
python manage.py makemigrations
python manage.py migrate

# 5. Seed demo data
echo "[4/6] Loading demo data (user: demo / password: demo12345)..."
python manage.py seed_demo_data

# 6. Train AI models
echo "[5/6] Training AI models (fraud detection + bankruptcy prediction)..."
python ai_models/train_fraud_model.py
python ai_models/train_bankruptcy_model.py

echo "[6/6] Setup complete!"
echo ""
echo "=================================================="
echo " Starting the development server..."
echo " Open http://127.0.0.1:8000/ in your browser"
echo " Login: demo / demo12345"
echo " (Press CTRL+C to stop the server)"
echo "=================================================="
python manage.py runserver
