import os

from flask import Blueprint, Flask

from nothanks import settings
from nothanks.api import game


app = Flask(__name__)
api = Api(version='1.0', title='No Thanks! API', description='An API for the No Thanks! game')


def initialize_app(flask_app):
    blueprint = Blueprint('api', __name__, url_prefix='/api')
    api.init_app(blueprint)
    flask_app.register_blueprint(blueprint)


if __name__ == "__main__":
    initialize_app(app)
    app.run(host='0.0.0.0', port=5000, debug=True)
