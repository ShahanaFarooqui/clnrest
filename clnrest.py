#!/usr/bin/env python3
import os
from pyln.client import Plugin
from multiprocessing import Process
from utilities.shared import set_config
from utilities.app import create_app, set_application_options, CLNRestApplication

plugin = Plugin()

jobs = {}
plugin.add_option(name="rest_certs_path", default=os.getcwd(), description="Path for certificates (for https)", opt_type="string", deprecated=False)
plugin.add_option(name="rest_protocol", default="https", description="REST server protocol", opt_type="string", deprecated=False)
plugin.add_option(name="rest_host", default="127.0.0.1", description="REST server host", opt_type="string", deprecated=False)
plugin.add_option(name="rest_port", default=3010, description="REST server port to listen", opt_type="int", deprecated=False)

def worker():
    app = create_app()
    options = set_application_options()
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
    set_config(plugin, options)
    from utilities.shared import REST_PORT
    start_server(REST_PORT)

plugin.run()
