from flask import Flask
from flask_cors import CORS
from config import Config
import logging

def create_app():
    """Factory function pour créer l'application Flask"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Configuration CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Configuration logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Enregistrement des blueprints
    from app.routes import main_bp, api_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app
