# For --hidden-import gunicorn.glogging gunicorn.workers.sync
from gunicorn import glogging
from gunicorn.workers import sync

from pathlib import Path
from flask import Flask
from gunicorn.app.base import BaseApplication
from flask_restx import Api
from .rpc import rpcns
from .generate_certs import generate_certs

def create_app():
    authorizations = {
        "rune": {"type": "apiKey","in": "header","name": "Rune"},
        "nodeid": {"type": "apiKey","in": "header","name": "Nodeid"}
    }
    app = Flask(__name__)
    api = Api(app, version="1.0", title="Core Lightning Rest", description="Core Lightning REST API Swagger", authorizations=authorizations, security=["rune", "nodeid"])
    api.add_namespace(rpcns, path="/v1")
    return app

def set_application_options():
    from utilities.shared import CERTS_PATH, REST_PROTOCOL, REST_HOST, REST_PORT, logger
    logger.log(f"Server is starting at {REST_PROTOCOL}://{REST_HOST}:{REST_PORT}", "info")
    
    if REST_PROTOCOL == "http":
        options = {
            "bind": f"{REST_HOST}:{REST_PORT}",
            "workers": 1,
            "timeout": 60,
        }
    else:
        cert_file = Path(f"{CERTS_PATH}/client.pem")
        key_file = Path(f"{CERTS_PATH}/client-key.pem")
        if not cert_file.is_file() or not key_file.is_file():
            logger.log(f"Certificate not found at {CERTS_PATH}. Generating a new certificate!", "info")
            generate_certs(CERTS_PATH)
        try:
            logger.log(f"Certs Path: {CERTS_PATH}", "info")
        except Exception as err:
            raise Exception(f"{err}: Certificates do not exist at {CERTS_PATH}")

        options = {
            "bind": f"{REST_HOST}:{REST_PORT}",
            "workers": 1,
            "timeout": 60,
            "certfile": f"{CERTS_PATH}/client.pem",
            "keyfile": f"{CERTS_PATH}/client-key.pem",
        }
    return options

class CLNRestApplication(BaseApplication):
    def __init__(self, app, options=None):
        self.application = app
        self.options = options or {}
        super().__init__()

    def load_config(self):
        config = {key: value for key, value in self.options.items()
                  if key in self.cfg.settings and value is not None}
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application