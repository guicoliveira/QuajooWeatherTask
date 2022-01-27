from flask import Flask, jsonify, make_response, request
from flask_caching import Cache
from pymongo import MongoClient
import requests
import json
from datetime import datetime

config = {
    "DEBUG": True,
    "CACHE_TYPE": "simple",
    "CACHE_DEFAULT_TIMEOUT": 300
}

app = Flask(__name__)
app.config.from_mapping(config)
cache = Cache(app)

def get_db():
    client = MongoClient(host='weather_db',
                        port=27017, 
                        username='root', 
                        password='pass',
                        authSource="admin")
    db = client["weather_db"]
    return db

weather_api_key = "05117393b55f2642ad27db0f0a383008"
weather_api_url = "https://api.openweathermap.org/data/2.5/weather" 

@app.route("/")
def index():
    return "Hello, you can check city weather from around the World here!"

@app.route("/cities", methods=['GET'])
def get_cities():
    db = get_db()
    _cities = db.cities.find()
    cities = [{"name": city["name"]} for city in _cities]
    return jsonify({'cities': cities})

@app.route("/cities/<string:city_name>", methods=['GET'])
@cache.memoize(timeout=300)
def get_city_temp(city_name):
    response = requests.get(
        weather_api_url, 
        params = {
            'q': city_name,
            'units': 'metric',
            'appid': weather_api_key
        }
    )
    if (response.status_code != 200):
        return ({'error': response.json()['message']}, response.status_code)

    db = get_db()
    if not db.cities.count_documents({'name': city_name}) > 0:        
        db.cities.insert_one({'name': city_name})

    response_data = {
        'Name': city_name, 
        'Celsius': response.json()['main']['temp'], 
        'Fahrenheit': celsius_to_fahrenheit(response.json()['main']['temp']), 
        'Timestamp': datetime.now().strftime("%H:%M:%S")
    }
    
    return (response_data, 200)

def celsius_to_fahrenheit(value):
    return round(((value * 9) / 5) + 32, 2)

@app.route("/batch")
def batch_request():
    try:
        batch_requests = json.loads(request.data) 
    except ValueError as e:
        return ('Invalid data', 400)

    responses = []

    for req in batch_requests:
        city = req['city']
        response = get_city_temp(city)
        responses.append({'status': response[1], 'response': response[0]})

    return (jsonify(responses), 207)

