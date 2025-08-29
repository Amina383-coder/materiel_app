from app import create_app
from database.database import db
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = create_app()

@app.teardown_appcontext
def close_database(error):
    """Fermer la connexion à la base de données à la fin de chaque requête"""
    db.disconnect()

if __name__ == '__main__':
    # Initialiser la base de données au démarrage
    try:
        if db.connect():
            logging.info("Base de données initialisée avec succès")
        else:
            logging.error("Échec de l'initialisation de la base de données")
    except Exception as e:
        logging.error(f"Erreur lors de l'initialisation de la base de données: {e}")
    
    app.run(
        host='localhost',
        port=5000,
        debug=True
    )
