import re
import socket
import sys
import json
import json5
import random
import argparse
import logging

LOG_LEVEL, RPC_PATH, CERTS_PATH, REST_PROTOCOL, REST_HOST, REST_PORT = "", "", "", "", "", ""
cln_socket = socket.socket(socket.AF_UNIX)
logger = logging.getLogger("")
caller = ""

def log(self, msg, level, *args, **kwargs):
    level_num = logging.getLevelName(level.upper())
    if self.isEnabledFor(level_num):
        self._log(level_num, msg, args, *kwargs)

def configure_logger():
    global logger
    if isinstance(caller, str):
        logger = logging.getLogger(caller)
        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(LOG_LEVEL or logging.ERROR)
        logger.log = log.__get__(logger, logging.getLoggerClass())
    else:
        logger = caller
    return logger

def read_config_from_json(file_path):
    try:
        with open(f"{file_path}/rest-config.json", "r") as f:
            return json5.load(f)
    
    except Exception as err:
        raise Exception(f"Error from config file ({file_path}/rest-config.json): {err}")


def read_config_from_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rest_config_path", help="Path to config file, default (.)", type=str, required=False)
    parser.add_argument("--rest_log_level", help="Log level (DEBUG/INFO/WARNING/ERROR), default (ERROR)", type=str, required=False)
    parser.add_argument("--rest_rpc_path", help="Path for the lightning-rpc file, default (/home/user/.lightning/bitcoin)", type=str, required=False)
    parser.add_argument("--rest_certs_path", help="Path for certificates for https, default (<rest_rpc_path>)", type=str, required=False)
    parser.add_argument("--rest_protocol", help="REST server protocol, default (https)", type=str, required=False)
    parser.add_argument("--rest_host", help="REST server host, default (127.0.0.1)", type=str, required=False)
    parser.add_argument("--rest_port", help="REST server port to listen, default (3010)", type=str, required=False)
    args = parser.parse_args()
    return vars(args)

def merge_configs(json_config, args_config):
    config = json_config.copy()

    # Overwrite values from command line if they exist
    for key, value in args_config.items():
        if value is not None:
            config[key] = value
    return config

def set_config(initiator, options):
    global caller, CERTS_PATH, RPC_PATH, LOG_LEVEL, REST_PROTOCOL, REST_HOST, REST_PORT
    caller = initiator
    if isinstance(caller, str):
        args_config = read_config_from_args()
        json_config = read_config_from_json(args_config["rest_config_path"] or ".")
        config = merge_configs(json_config, args_config)
        LOG_LEVEL = config.get("rest_log_level") or "ERROR"
        RPC_PATH = config.get("rest_rpc_path") or "/home/user/.lightning/bitcoin"
        CERTS_PATH = config.get("rest_certs_path") or RPC_PATH
        REST_PROTOCOL = config.get("rest_protocol") or "https"
        REST_HOST = config.get("rest_host") or "127.0.0.1"
        REST_PORT = config.get("rest_port") or "3010"
    else:
        CERTS_PATH = str(options["rest_certs_path"])
        REST_PROTOCOL = str(options["rest_protocol"])
        REST_HOST = str(options["rest_host"])
        REST_PORT = int(options["rest_port"])
    configure_logger()

def connect_socket(rpc_path):
    try:
        cln_socket.connect(f"{rpc_path}/lightning-rpc")
    except Exception as err:
        raise Exception(f"Error in RPC path ({rpc_path}) or socket connection: {err}")

def call_rpc_method(rpc_method, payload):
    try:
        if isinstance(caller, str):
            method_req = { "jsonrpc": "2.0", "id": "rest:" + rpc_method + "#" + str(random.randint(100000, 999999)), "method": rpc_method, "params": payload }
            cln_socket.sendall(json.dumps(method_req).encode())
            response = cln_socket.recv(1048576).decode()
        else:
            response = caller.rpc.call(rpc_method, payload)

        if '"error":' in str(response).lower():
            raise Exception(response)
        else:
            logger.log(f"{response}", "info")
            if '"result":' in str(response).lower():
                return json5.loads(response)["result"]
            else:
                return response

    except Exception as err:
        logger.log(f"Error: {err}", "error")
        if "error" in str(err).lower():
            match_err_obj = re.search(r'"error":\{.*?\}', str(err))
            if match_err_obj is not None:
                err = "{" + match_err_obj.group() + "}"
            else:
                match_err_str = re.search(r"error: \{.*?\}", str(err))
                if match_err_str is not None:
                    err = "{" + match_err_str.group() + "}"
        raise Exception(err)

def verify_rune(request):
    rune = request.headers.get("rune", None)
    nodeid = request.headers.get("nodeid", None)

    if nodeid is None:
        raise Exception('{ "error": {"code": 403, "message": "Not authorized: Missing nodeid"} }')

    if rune is None:
        raise Exception('{ "error": {"code": 403, "message": "Not authorized: Missing rune"} }')

    if request.is_json:
        rpc_params = request.get_json()
    else:
        rpc_params = request.form.to_dict()

    return call_rpc_method("commando-checkrune", [nodeid, rune, request.view_args["rpc_method"], rpc_params])
