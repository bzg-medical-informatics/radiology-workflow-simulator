from __future__ import annotations

from flask import Flask, redirect, request

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

    @app.get('/scan')
    def scan_get_compat():
        """Handle cached/legacy upload JS that navigates back to GET /scan."""
        return redirect('/modality')

    @app.after_request
    def add_interaction_scripts(response):
        """Load shared workflow navigation plus dashboard-only interaction fixes."""
        if response.mimetype != 'text/html' or response.is_streamed:
            return response

        html = response.get_data(as_text=True)
        if '</body>' not in html:
            return response

        script_tags = []
        if request.path == '/':
            dashboard_tag = '<script src="/static/dashboard-fixes.js"></script>'
            if dashboard_tag not in html:
                script_tags.append(dashboard_tag)

        workflow_tag = '<script src="/static/workflow-navigation.js"></script>'
        if workflow_tag not in html:
            script_tags.append(workflow_tag)

        if script_tags:
            response.set_data(html.replace('</body>', '\n'.join(script_tags) + '\n</body>', 1))
        return response

    return app
