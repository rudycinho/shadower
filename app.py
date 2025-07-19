from flask import Flask
from config import Config
from src.utils.file_utils import clean_temp_folder
from src.routes.main_routes import main_bp  # Nuevo blueprint
from src.routes.media_routes import media_bp
from src.routes.tts_routes import tts_bp
from src.routes.upload_routes import upload_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    Config.init_app(app)
    
    clean_temp_folder(app.config['UPLOAD_FOLDER'], app.config['PROCESSED_FOLDER'])
    
    # Registrar blueprints
    app.register_blueprint(main_bp)  # Ruta principal sin prefijo
    app.register_blueprint(media_bp, url_prefix='/api')
    app.register_blueprint(tts_bp, url_prefix='/api')
    app.register_blueprint(upload_bp, url_prefix='/api')
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)