import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Configuration Base de données MySQL
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    # Tolérer les valeurs d'exemple comme mot de passe vide
    if DB_PASSWORD in ('votre_mot_de_passe_mysql', 'your_mysql_password', 'votre-mot-de-passe', 'changeme'):
        DB_PASSWORD = ''
    DB_NAME = os.getenv('DB_NAME', 'materiel_it_db')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    
    # Configuration Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Configuration uploads
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
