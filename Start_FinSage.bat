@echo off
echo ==============================================
echo       Starting FinSage Copilot POC
echo ==============================================

echo Starting FinSage Backend (FastAPI)...
cd "C:\Users\RADHIKA SANKAR\.gemini\antigravity\scratch\finsage\backend"
start "FinSage Backend" cmd /k "title FinSage Backend && uvicorn main:app --port 8000"

echo Starting FinSage Frontend (React/Vite)...
cd "C:\Users\RADHIKA SANKAR\.gemini\antigravity\scratch\finsage\frontend"
start "FinSage Frontend" cmd /k "title FinSage Frontend && npm run dev"

echo Waiting for servers to initialize...
timeout /t 5 /nobreak >nul

echo Opening FinSage in your default browser...
start http://localhost:5173
start http://localhost:5174
