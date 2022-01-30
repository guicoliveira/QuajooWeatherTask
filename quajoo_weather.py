from flask import Flask
from flask_caching import Cache
from flask_mongoengine import MongoEngine

config = {
    "DEBUG": True,
    "CACHE_TYPE": "simple",
    "CACHE_DEFAULT_TIMEOUT": 300
}

app = Flask(__name__)
app.config.from_mapping(config)
app.config['MONGODB_SETTINGS'] = {
    'db': 'weather_db',
    'host': 'weather_db',
    'port': 27017,
    'username': 'root',
    'password': 'pass',
    'authentication_source': 'admin'
}

db = MongoEngine()
db.init_app(app)
cache = Cache(app)

import views

if __name__ == "__main__":
    app.run(debug=True)
