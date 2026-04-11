import os
from flask import Flask
from flask_minify import Minify

from app.routes import register_blueprints
from app.utils.backend_handler import BackEndHandler


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "your_secret_key"

    # 1. Handle background tasks
    # We check if we are in the main process to avoid starting threads twice 
    # during debug reloading
    # if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
    #     bh = BackEndHandler()
    #     bh.start()
    #     print("--- Backend Handler Started ---")

    Minify(app=app, html=True, js=True, cssless=True)
    app.jinja_env.lstrip_blocks = True
    app.jinja_env.trim_blocks = True

    # Register blueprints
    register_blueprints(app)

    return app
