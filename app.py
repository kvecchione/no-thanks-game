import os

from flask import Blueprint, Flask
from flask_restplus import Api
from nothanks.api.api import api

from nothanks.api import game

app = Flask(__name__)
app.config.SWAGGER_UI_DOC_EXPANSION = 'list'

def initialize_app(flask_app):
    blueprint = Blueprint('api', __name__, url_prefix='/api')
    api.init_app(blueprint)
    flask_app.register_blueprint(blueprint)


if __name__ == "__main__":
    initialize_app(app)
    app.run(host='0.0.0.0', port=5000, debug=True)
