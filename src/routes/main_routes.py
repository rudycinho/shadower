from flask import Blueprint, render_template
from src.services.media_manager import MediaManager
from config import Config

main_bp = Blueprint('main', __name__)
media_manager = MediaManager(Config.UPLOAD_FOLDER, Config.PROCESSED_FOLDER)

@main_bp.route('/')
def index():
    media_files = media_manager.get_media_files()
    return render_template('player.html', media_files=media_files)