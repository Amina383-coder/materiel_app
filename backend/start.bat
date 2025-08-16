@echo off
echo ========================================
echo   Gestion Matériel IT - Backend Python
echo ========================================
echo.

echo Installation des dependances...
pip install -r requirements.txt

echo.
echo Initialisation de la base de donnees...
python init_db.py

echo.
echo Demarrage du serveur Flask...
echo L'application sera accessible sur: http://localhost:5000
echo.
echo Appuyez sur Ctrl+C pour arreter le serveur
echo.

python run.py

pause
