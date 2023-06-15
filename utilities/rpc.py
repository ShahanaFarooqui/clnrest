import socket
from flask import request, make_response
from flask_restx import Resource, Namespace
import json
import json5
from .shared import call_rpc_method
from .auth import rune_auth

methods_list = []
cln_socket = socket.socket(socket.AF_UNIX)

rpcns = Namespace("RPCs")
payload_model = rpcns.model("Payload", {}, None, False)

def process_help_response(help_response):
    # json5.loads due to single quotes in response
    processed_res = json5.loads(str(help_response))["help"]
    line = "\n---------------------------------------------------------------------------------------------------------------------------------------------------------------------------\n\n"
    processed_html_res = ""
    for row in processed_res:
        processed_html_res += f"Command: {row['command']}\n"
        processed_html_res += f"Category: {row['category']}\n"
        processed_html_res += f"Description: {row['description']}\n"
        processed_html_res += f"Verbose: {row['verbose']}\n"
        processed_html_res += line
    return processed_html_res

@rpcns.route("/list-methods")
class RpcMethodResource(Resource):
    @rpcns.response(200, "Success")
    @rpcns.response(500, "Server error")
    def get(self):
        """Get the list of all valid rpc methods"""
        try:
            from utilities.shared import logger
            help_response = call_rpc_method("help", [])
            html_content = process_help_response(help_response)
            response = make_response(html_content)
            response.headers['Content-Type'] = 'text/html'
            return response

        except Exception as err:
            logger.log(f"Error: {err}", "error")
            return json5.loads(str(err)), 500

@rpcns.route("/<rpc_method>")
class RpcMethodResource(Resource):
    method_decorators = [rune_auth.validate_rune]
    @rpcns.doc(security=[{"rune": [], "nodeid": []}])
    @rpcns.doc(params={"rpc_method": (f"Name of the RPC method to be called")})
    @rpcns.expect(payload_model, validate=False)
    @rpcns.response(201, "Success")
    @rpcns.response(500, "Server error")
    def post(self, rpc_method):
        """Call any valid core lightning method (check list-methods response)"""
        try:
            from utilities.shared import logger
            if request.is_json:
                payload = request.get_json()
            else:
                payload = request.form.to_dict()
            return call_rpc_method(rpc_method, payload), 201

        except Exception as err:
            logger.log(f"Error: {err}", "error")
            return json5.loads(str(err)), 500
