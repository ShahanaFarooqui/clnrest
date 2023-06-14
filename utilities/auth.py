import json5
from functools import wraps
from flask import request
from .shared import logger, verify_rune

class RuneHTTPAuth():
    def validate_rune(self, f):
        @wraps(f)
        def decorated(*args, **kwargs):
            try:
                is_valid_rune = verify_rune(request)
                
                if "error" in is_valid_rune:
                    logger.log(f"Error: {is_valid_rune}", "error")
                    raise Exception(is_valid_rune)

            except Exception as err:
                # Fix Me: Remove after lightningd checkrune is available
                if not "unknown command" in str(err).lower():
                    return json5.loads(str(err)), 403

            return f(*args, **kwargs)
        return decorated

rune_auth = RuneHTTPAuth()
