from quajoo_weather import app, cache
from models import City
from flask import jsonify, request, make_response
import json
from datetime import datetime
import requests

weather_api_key = "05117393b55f2642ad27db0f0a383008"
weather_api_url = "https://api.openweathermap.org/data/2.5/weather" 

@app.route('/cities', methods=['GET'])
def get_all_cities():
    _cities = City.objects()
    cities = [city.to_json() for city in _cities]
    return make_response({'cities': cities})

@app.route('/cities/<string:city_name>', methods=['GET'])
def get_city(city_name):
    city = City.objects(name=city_name).first()
    if not city:
        return make_response({'error': f'city not in the database: {city_name}'}, 404)
    else:
        return make_response(city.to_json())

@app.route('/cities/<string:city_name>/temp', methods=['GET'])
def get_city_temp(city_name):
    city = City.objects(name=city_name).first()    
    if not city:
        return make_response({'error': f'city not in the database: {city_name}'}, 404)
    else:
        return request_get_city_temp(city_name)

@app.route('/cities', methods=['POST'])
def add_city():
    try:
        data = json.loads(request.data)
        city_name = data['name']
    except json.JSONDecodeError as e:
        return make_response({'error': f'invalid request body: {request.data}'}, 400)
    except KeyError as e:
        return make_response({'error': f'invalid request body: {request.data}'}, 400)

    city = City.objects(name=city_name).first()
    if not city:
        new_city = City(name=data['name'])
        new_city.save()
        return make_response(new_city.to_json(), 201)
    else:
        return make_response({'error': f'city already exists: {city.name}'}, 409)

@app.route('/cities/<string:city_name>', methods=['DELETE'])
def delete_city(city_name):
    city = City.objects(name=city_name).first()
    if not city:
        return make_response({'error': f'city not in the database: {city_name}'}, 404)
    else:
        city.delete()
    return make_response(city.to_json(), 202)

@app.route("/batch/cities")
def city_batch_request():
    try:
        batch_requests = json.loads(request.data) 
    except ValueError as e:
        return ('Invalid data', 400)

    responses = []

    for req in batch_requests:
        try:
            method = req['method']
            url = req['url']
            body =  json.dumps(req.get('body', None)) 
        except KeyError as e:
            responses.append({'status': 400, 'response': f'Invalid field: {req}'})
            continue

        with app.app_context():
            with app.test_request_context(url, method=method, data=body):
                try:
                    response = app.preprocess_request()
                    if response is None:
                        response = app.dispatch_request()

                except Exception as e:
                    responses.append({'status': 400, 'response': f'Invalid request: {req}'})
                    continue
                
        responses.append({
            "status": response.status_code,
            "response": json.loads(response.response[0])
        })
        
    return make_response(jsonify(responses), 207)

@cache.memoize(timeout=300)
def request_get_city_temp(city_name):
    response = requests.get(
        weather_api_url, 
        params = {
            'q': city_name,
            'units': 'metric',
            'appid': weather_api_key
        }
    )
    if (response.status_code != 200):
        return ({'error': f'{response.json()["message"]}: {city_name}'}, response.status_code)

    response_data = {
        'Name': city_name, 
        'Celsius': response.json()['main']['temp'], 
        'Fahrenheit': celsius_to_fahrenheit(response.json()['main']['temp']), 
        'Timestamp': datetime.now().strftime("%H:%M:%S")
    }
    
    return make_response(response_data, 200)

def celsius_to_fahrenheit(value):
    return round(((value * 9) / 5) + 32, 2)