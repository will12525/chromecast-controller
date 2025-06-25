from flask import Flask
from flask_minify import minify
from app.database.db_access import DBType
from app.database.db_getter import DBHandler
from app.routes import register_blueprints


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "your_secret_key"  # Replace with a strong key
    minify(app=app, html=True, js=True, cssless=True)
    app.jinja_env.lstrip_blocks = True
    app.jinja_env.trim_blocks = True
    # Initialize database
    db_handler = DBHandler()
    db_handler.open()
    db_handler.create_db()
    db_handler.close()

    # Register blueprints
    register_blueprints(app)

    return app
