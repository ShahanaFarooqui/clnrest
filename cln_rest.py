from utilities.shared import set_config, connect_socket
from utilities.app import create_app, set_application_options, CLNRestApplication

if __name__ == "__main__":
    try:
        set_config(__name__, None)
        from utilities.shared import logger, RPC_PATH
        connect_socket(RPC_PATH)
        app = create_app()
        options = set_application_options()
        CLNRestApplication(app, options).run()

    except Exception as err:
        logger.log(f"{err}", "error")