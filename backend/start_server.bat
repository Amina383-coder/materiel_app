@echo off
echo ========================================
echo   Demarrage du serveur Materiel IT
echo ========================================
echo.

REM Activer l'environnement virtuel
call venv\Scripts\activate.bat

REM Démarrer le serveur
python run.py

pause
