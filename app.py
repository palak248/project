import logging

from flask import Flask, jsonify, render_template

from admin.routes import admin
from auth.routes import auth
from auth.service import csrf_token
from config import Config
from student.routes import student
from teacher.routes import teacher


def create_app(config_class=Config):
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(config_class)

    @app.context_processor
    def inject_csrf_token():
        return {"csrf_token": csrf_token}

    _configure_logging(app)
    app.register_blueprint(auth)
    app.register_blueprint(admin)
    app.register_blueprint(student)
    app.register_blueprint(teacher)

    @app.get("/")
    def home():
        return render_template("index.html")

    @app.get("/health")
    def health():
        return jsonify(
            status="ok",
            database_configured=app.config["MYSQL_CONFIGURED"],
        )

    @app.errorhandler(404)
    def not_found(error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        app.logger.exception("Unhandled application error", exc_info=error)
        return render_template("500.html"), 500

    app.logger.info("Flask application initialized")
    return app


def _configure_logging(app):
    if not app.logger.handlers:
        logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)


app = create_app()


if __name__ == "__main__":
    app.run()