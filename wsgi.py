import os

import argparse

from roosterapp import create_app


CLI_WELCOME = 'Yet Another Url Shorting Service.'
CLI_KEY_HELP = 'If this flag is used, the key store service is run'
CLI_PATH_HELP = 'The path to the instance folder containing the config.py'


def main():
    parser = argparse.ArgumentParser(description=CLI_WELCOME)
    parser.add_argument('-k', '--key', help=CLI_KEY_HELP,
                        action='store_true')
    parser.add_argument('-p', '--path', help=CLI_PATH_HELP, nargs='?')

    args = parser.parse_args()
    if args.path is None:
        args.path = "/roosters"
    path = setup_instance_path(args.path)

    config = {'INSTANCE_PATH': path}

    app = create_app(config)
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting on port {port}.")
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
