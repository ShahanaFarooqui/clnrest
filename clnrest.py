#!/usr/bin/env python3
# For --hidden-import gunicorn.glogging gunicorn.workers.sync
from gunicorn import glogging
from gunicorn.workers import sync

import os
import json5
from pathlib import Path
from flask import Flask, request, make_response
from flask_restx import Api, Namespace, Resource
from gunicorn.app.base import BaseApplication
from pyln.client import Plugin
from multiprocessing import Process
from utilities.generate_certs import generate_certs
from utilities.shared import call_rpc_method, verify_rune, process_help_response

CERTS_PATH, REST_PROTOCOL, REST_HOST, REST_PORT = "", "", "", ""
plugin = Plugin()

jobs = {}
plugin.add_option(name="rest_certs_path", default=os.getcwd(), description="Path for certificates (for https)", opt_type="string", deprecated=False)
plugin.add_option(name="rest_protocol", default="https", description="REST server protocol", opt_type="string", deprecated=False)
plugin.add_option(name="rest_host", default="127.0.0.1", description="REST server host", opt_type="string", deprecated=False)
plugin.add_option(name="rest_port", default=3010, description="REST server port to listen", opt_type="int", deprecated=False)

methods_list = []
rpcns = Namespace("RPCs")
payload_model = rpcns.model("Payload", {}, None, False)

def create_app():
    app = Flask(__name__)
    authorizations = {
        "rune": {"type": "apiKey","in": "header","name": "Rune"},
        "nodeid": {"type": "apiKey","in": "header","name": "Nodeid"}
    }
    api = Api(app, version="1.0", title="Core Lightning Rest", description="Core Lightning REST API Swagger", authorizations=authorizations, security=["rune", "nodeid"])
    api.add_namespace(rpcns, path="/v1")
    return app

@rpcns.route("/list-methods")
class ListMethodsResource(Resource):
    @rpcns.response(200, "Success")
    @rpcns.response(500, "Server error")
    def get(self):
        """Get the list of all valid rpc methods"""
        try:
            help_response = call_rpc_method(plugin, "help", [])
            html_content = process_help_response(help_response)
            response = make_response(html_content)
            response.headers["Content-Type"] = "text/html"
            return response

        except Exception as err:
            plugin.log(f"Error: {err}", "error")
            return json5.loads(str(err)), 500

@rpcns.route("/<rpc_method>")
class RpcMethodResource(Resource):
    @rpcns.doc(security=[{"rune": [], "nodeid": []}])
    @rpcns.doc(params={"rpc_method": (f"Name of the RPC method to be called")})
    @rpcns.expect(payload_model, validate=False)
    @rpcns.response(201, "Success")
    @rpcns.response(500, "Server error")
    def post(self, rpc_method):
        """Call any valid core lightning method (check list-methods response)"""
        try:
            is_valid_rune = verify_rune(plugin, request)
            
            if "error" in is_valid_rune:
                plugin.log(f"Error: {is_valid_rune}", "error")
                raise Exception(is_valid_rune)

        except Exception as err:
            # Fix Me: Remove after lightningd checkrune is available
            if not "unknown command" in str(err).lower():
                return json5.loads(str(err)), 403
        
        try:
            if request.is_json:
                payload = request.get_json()
            else:
                payload = request.form.to_dict()
            return call_rpc_method(plugin, rpc_method, payload), 201

        except Exception as err:
            plugin.log(f"Error: {err}", "error")
            return json5.loads(str(err)), 500

def set_config(options):
    global CERTS_PATH, REST_PROTOCOL, REST_HOST, REST_PORT
    CERTS_PATH = str(options["rest_certs_path"])
    REST_PROTOCOL = str(options["rest_protocol"])
    REST_HOST = str(options["rest_host"])
    REST_PORT = int(options["rest_port"])

def set_application_options(plugin):
    plugin.log(f"Server is starting at {REST_PROTOCOL}://{REST_HOST}:{REST_PORT}", "info")
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
            plugin.log(f"Certificate not found at {CERTS_PATH}. Generating a new certificate!", "info")
            generate_certs(plugin, CERTS_PATH)
        try:
            plugin.log(f"Certs Path: {CERTS_PATH}", "info")
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
    
def worker():
    options = set_application_options(plugin)
    app = create_app()
    CLNRestApplication(app, options).run()

def start_server(REST_PORT):
    if REST_PORT in jobs:
        return False, "server already running"

    p = Process(
        target=worker,
        args=[],
        name="server on port {}".format(REST_PORT),
    )
    p.daemon = True
    jobs[REST_PORT] = p
    p.start()
    return True

@plugin.init()
def init(options, configuration, plugin):
    set_config(options)
    start_server(REST_PORT)

plugin.run()
