@echo off
REM One-command setup for AI Finance Manager (Windows)
REM Usage: double-click setup.bat, or run it from a Command Prompt

echo ==================================================
echo  AI Finance Manager - Automated Setup
echo ==================================================

IF NOT EXIST venv (
    echo [1/6] Creating virtual environment...
    python -m venv venv
) ELSE (
    echo [1/6] Virtual environment already exists, skipping.
)

call venv\Scripts\activate

echo [2/6] Installing dependencies (this may take a minute)...
python -m pip install --upgrade pip -q
pip install -r requirements.txt -q

echo [3/6] Creating database tables...
python manage.py makemigrations
python manage.py migrate

echo [4/6] Loading demo data (user: demo / password: demo12345)...
python manage.py seed_demo_data

echo [5/6] Training AI models (fraud detection + bankruptcy prediction)...
python ai_models\train_fraud_model.py
python ai_models\train_bankruptcy_model.py

echo [6/6] Setup complete!
echo.
echo ==================================================
echo  Starting the development server...
echo  Open http://127.0.0.1:8000/ in your browser
echo  Login: demo / demo12345
echo  (Press CTRL+C to stop the server)
echo ==================================================
python manage.py runserver

pause
