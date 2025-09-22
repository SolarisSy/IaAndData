@echo off
echo "======================================="
echo "Iniciando Servidor Backend (FastAPI)..."
echo "======================================="
start "Backend" cmd /k ".\backend\venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000"

echo "========================================"
echo "Iniciando Servidor Frontend (Next.js)..."
echo "========================================"
start "Frontend" cmd /k "cd frontend && npm run dev"

echo "Servidores estao iniciando em novas janelas..."
