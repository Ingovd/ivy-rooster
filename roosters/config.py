import os


## Domain the service is running at

SERVER_NAME = 'localhost:5000'

# Will set SQLALCHEMY_DATABASE_URI to 'dialect:///relative/path/to/database.db'
# SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join('..', 'roosters', 'roosters.db')
SQLALCHEMY_DATABASE_URI = "mysql+pymysql://crud:bwbe9ne8YsP4ZDXt@/rooster?unix_socket=/cloudsql/ivy-rooster:europe-west1:klimop"


## flask sesssion

# Change to your own secret to support secure sessions
SECRET_KEY = b'replacewithsecret'
