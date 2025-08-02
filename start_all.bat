@echo off
echo Demarrage Risk Monitor...
echo./n

timeout /t 1 /nobreak > nul

echo Generation des donnees de test...
python backend/populate_db.py

timeout /t 1 /nobreak > nul

echo. /n/n

echo  Services disponibles :
echo   - API FastAPI: http://localhost:8000
echo   - Dashboard Streamlit: http://localhost:8501
echo.
echo  Appuyez sur Ctrl+C pour arrêter les services
echo.

:: Démarrer API en arrière-plan
start "API FastAPI" cmd /c "cd backend && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

:: Attendre 3 secondes pour que l'API démarre
timeout /t 3 /nobreak > nul

:: Démarrer Streamlit en arrière-plan
start "Streamlit Dashboard" cmd /c "streamlit run frontend/app.py --server.port 8501"

echo ✅ Services démarrés !
pause