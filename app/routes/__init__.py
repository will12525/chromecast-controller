"""Flask blueprints for the chromecast controller app."""
from app.routes.shared import main_bp

# Import route modules so their @main_bp.route handlers register
from app.routes import cast_routes  # noqa: F401
from app.routes import editor_routes  # noqa: F401
from app.routes import library_routes  # noqa: F401
from app.routes import transfer_routes  # noqa: F401


def register_blueprints(app):
    app.register_blueprint(main_bp)
