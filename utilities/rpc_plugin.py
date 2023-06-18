import os
from pyln.client import Plugin

plugin = Plugin()

plugin.add_option(name="rest_certs_path", default=os.getcwd(), description="Path for certificates (for https)", opt_type="string", deprecated=False)
plugin.add_option(name="rest_protocol", default="https", description="REST server protocol", opt_type="string", deprecated=False)
plugin.add_option(name="rest_host", default="127.0.0.1", description="REST server host", opt_type="string", deprecated=False)
plugin.add_option(name="rest_port", default=3010, description="REST server port to listen", opt_type="int", deprecated=False)
