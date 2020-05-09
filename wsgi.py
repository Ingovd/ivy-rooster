import os

import argparse

from yauss import create_app as create_yauss
from key_store import create_app as create_key_store


CLI_WELCOME = 'Yet Another Url Shorting Service.'
CLI_KEY_HELP = 'If this flag is used, the key store service is run'
CLI_PATH_HELP = 'The path to the instance folder containing the config.py'


def main():
    parser = argparse.ArgumentParser(description=CLI_WELCOME)
    parser.add_argument('-k', '--key', help=CLI_KEY_HELP,
                        action='store_true')
    parser.add_argument('-p', '--path', help=CLI_PATH_HELP, nargs='?')

    args = parser.parse_args()
    path = setup_instance_path(args.path)

    config = {'INSTANCE_PATH': path}

    if args.key:
        app = create_key_store(config)
    else:
        app = create_yauss(config)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)


def setup_instance_path(path):
    if path is None:
        return None
    if os.path.isdir(path):
        return path
    abs_path = os.getcwd() + path
    if os.path.isdir(abs_path):
        return abs_path
    raise OSError(f"Neither {path} nor {abs_path} exists.")


if __name__ == "__main__":
    main()
