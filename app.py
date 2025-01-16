import os

from flask import Blueprint, Flask
from nothanks.api.api import api
from werkzeug.middleware.proxy_fix import ProxyFix

from nothanks.api import game

app = Flask(__name__)
app.config.SWAGGER_UI_DOC_EXPANSION = 'list'

def initialize_app(flask_app):
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    blueprint = Blueprint('api', __name__, url_prefix='/api')
    api.init_app(blueprint)
    flask_app.register_blueprint(blueprint)


if __name__ == "__main__":
    initialize_app(app)
    app.run(host='0.0.0.0', port=8000, debug=True)
