from flask import Markup

# Messages flashed to end user
USR_INVALID_URL = 'Please specify a valid url to be shortened'
USR_USED_KEY = 'Your key is already in use, please try a different custom key'
USR_UNEXPECTED = ('Unexpected error while handling your request, '
                  'please try again later')
USR_HTML_URL_ADD_1URL = Markup(
                         ("Successfully added your url. "
                          "Here is your link <a href='http://{0}'>{0}</a>")
                        )
USR_URL_DEL_1URL = "Successfully removed url: {}"
USR_UPDATE_1URL_2URL = "Successfully updated {} to {}"

# Messages for internal use
APP_CREATED_FLASK_1PATH = "Created Flask application in folder: {}"
APP_INVALID_DB = ("Invalid (or no) database configured, "
                  "running the service in memory (TESTING ONLY)")
APP_DB_SETUP_1ERR = "Unexpected error when setting up database: {}"
APP_KEY_1ERR = "Key store error during url creation: {}"
APP_UNEXPECTED_1ERR = "Unexpected error when handling url creation: {}"
APP_CACHE_1ERR = "Unexpected error when retrieving from cache: {}"
APP_INTERNAL_1ERR_2WHERE = "Server aborted with 503 at {1}: {0}"
