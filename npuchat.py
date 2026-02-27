import os

from flasgger import Swagger
from flask import Flask, request, send_from_directory

from blueprints.chats import chats_bp
from blueprints.search import search_bp
from blueprints.templates import templates_bp
from config import Config
from jsonapi import jsonapi_error_response
from models import db
from services import TemplateService


def create_app():
    app = Flask(__name__)
    config = Config()
    app.config.from_object(config)

    db.init_app(app)

    with app.app_context():
        db.create_all()
        TemplateService.load_templates()

    app.config['SWAGGER'] = {
        'title': 'NPU-Chat API',
        'version': '1.0.0',
        'description': 'JSON:API compliant chat API for NPU-Chat',
        'consumes': ['application/vnd.api+json'],
        'produces': ['application/vnd.api+json'],
    }
    Swagger(app)

    app.register_blueprint(chats_bp, url_prefix='/api')
    app.register_blueprint(templates_bp, url_prefix='/api')
    app.register_blueprint(search_bp, url_prefix='/api')

    @app.after_request
    def set_jsonapi_content_type(response):
        if request.path.startswith('/api/'):
            response.headers['Content-Type'] = 'application/vnd.api+json'
        return response

    @app.errorhandler(400)
    def bad_request(e):
        return jsonapi_error_response(400, 'Bad Request', str(e))

    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith('/api/'):
            return jsonapi_error_response(404, 'Not Found')
        return '', 404

    @app.errorhandler(422)
    def unprocessable(e):
        return jsonapi_error_response(422, 'Unprocessable Entity', str(e))

    @app.errorhandler(500)
    def server_error(e):
        return jsonapi_error_response(500, 'Internal Server Error')

    @app.route('/')
    def index():
        return send_from_directory('static/dist', 'index.html')

    @app.route('/assets/<path:filename>')
    def assets(filename):
        return send_from_directory('static/dist/assets', filename)

    @app.route('/<path:filename>')
    def static_files(filename):
        if os.path.exists(os.path.join(app.root_path, 'static', 'dist', filename)):
            return send_from_directory('static/dist', filename)
        return '', 404

    return app

if __name__ == '__main__':
    app = create_app()
    config = Config()
    app.run(host=config.BINDING_ADDRESS, port=config.BINDING_PORT, debug=False)
