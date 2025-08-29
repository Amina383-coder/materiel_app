from flask import Flask, render_template
from flask_cors import CORS
from config import Config
import logging
from flask_wtf import CSRFProtect

def create_app():
    """Factory function pour créer l'application Flask"""
    app = Flask(
    __name__,
    template_folder="../../templates",
    static_folder="../../static"
    )

    csrf = CSRFProtect(app)
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
    csrf.exempt(api_bp)
    csrf.exempt(main_bp)

    # Les routes de pages sont gérées par le blueprint main dans app.routes
    return app
