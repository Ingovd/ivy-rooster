import os


## Domain the service is running at

SERVER_NAME = 'localhost:5000'

# Will set SQLALCHEMY_DATABASE_URI to 'dialect:///relative/path/to/database.db'
# SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join('..', 'roosters', 'roosters.db')
SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:Klimop123@/?db=/cloudsql/primal-timing-278013:europe-west4:rooster"


## flask sesssion

# Change to your own secret to support secure sessions
SECRET_KEY = b'replacewithsecret'
