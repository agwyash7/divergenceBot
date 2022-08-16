from flask import Flask, app, request, abort
from flask_basicauth import BasicAuth
from flask_mongoengine import MongoEngine
from flask_restful import Api

from api.routes import create_routes

default_config = {
    'MONGODB_SETTINGS': {
        'db': 'livebot',
        'host': '198.211.110.141',
        'port': 2727,
        'username': 'yashLiveBot',
        'password': 'MongoChachaLiveBot$123'
    }
}


def get_flask_app(config: dict = None) -> app.Flask:
    flask_app = Flask(__name__)

    # configure app
    config = default_config if config is None else config
    flask_app.config.update(config)

    api = Api(app=flask_app)
    create_routes(api=api)

    # init mongoengine
    db = MongoEngine(app=flask_app)
    return flask_app


app = get_flask_app()

app.config['BASIC_AUTH_USERNAME'] = 'YashSecretUsername'
app.config['BASIC_AUTH_PASSWORD'] = 'YashSecretPasswordOcean123'
app.config['BASIC_AUTH_FORCE'] = True

basic_auth = BasicAuth(app)


# @app.before_request
# def limit_remote_addr():
#     trusted_ip = ('198.211.110.141', '103.42.89.204', '127.0.0.1')
#     remote = request.remote_addr
#
#     if remote not in trusted_ip:
#         abort(403)


app.run(host="0.0.0.0")
