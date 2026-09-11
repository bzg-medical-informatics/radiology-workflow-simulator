from __future__ import annotations

from flask import Flask, request

try:
    from simlib import storage
    from simlib.config import FLASK_SECRET_KEY, MAX_CONTENT_LENGTH
except ModuleNotFoundError:
    from .simlib import storage
    from .simlib.config import FLASK_SECRET_KEY, MAX_CONTENT_LENGTH

try:
    from blueprint import bp
except ImportError:
    from .blueprint import bp


def create_app() -> Flask:
    # Import routes/hooks for side effects (registering on blueprint)
    # Keep imports inside factory to avoid circular imports.
    try:
        import hooks  # noqa: F401
        import routes_admin  # noqa: F401
        import routes_home  # noqa: F401
        import routes_kis  # noqa: F401
        import routes_lis  # noqa: F401
        import routes_modality  # noqa: F401
        import routes_pacs  # noqa: F401
        import routes_session  # noqa: F401
        import routes_workstation  # noqa: F401
    except ImportError:
        from . import hooks  # noqa: F401
        from . import routes_admin  # noqa: F401
        from . import routes_home  # noqa: F401
        from . import routes_kis  # noqa: F401
        from . import routes_lis  # noqa: F401
        from . import routes_modality  # noqa: F401
        from . import routes_pacs  # noqa: F401
        from . import routes_session  # noqa: F401
        from . import routes_workstation  # noqa: F401

    app = Flask(__name__)
    app.secret_key = FLASK_SECRET_KEY
    app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

    # Auto-generate SuS session codes if requested.
    storage.maybe_auto_generate_sessions()

    app.register_blueprint(bp)

    @app.after_request
    def add_dashboard_fix_script(response):
        """Load small dashboard-only interaction fixes on the home page."""
        if request.path == '/' and response.mimetype == 'text/html' and not response.is_streamed:
            html = response.get_data(as_text=True)
            script_tag = '<script src="/static/dashboard-fixes.js"></script>'
            if script_tag not in html and '</body>' in html:
                response.set_data(html.replace('</body>', f'{script_tag}\n</body>', 1))
        return response

    return app
