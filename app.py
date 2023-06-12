from flask import Flask, render_template, request
import requests
import os, json
from config import API_KEY
import cachetools
import mysql.connector
from datetime import datetime

app = Flask(__name__, static_folder='/assets')

# Connect to the MySQL database
db_connection = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME')
)
db_cursor = db_connection.cursor()

def search_cache(city):
  expire_seconds = 30
  # With this we read the database

  db_cursor.execute("SELECT response, timestamp FROM weather_data WHERE request = %s;", (city,))
  result = db_cursor.fetchone()
  # No sql rows
  if (result == None):
    return None

  json_data, time_data = result[0], result[1]
  delta = datetime.now() - time_data
  if (delta.seconds > expire_seconds):
    db_cursor.execute("DELETE FROM weather_data WHERE request = %s;", (city,))
    db_connection.commit()
    return None
  return json_data

# With this command we insert data into the database
def insert_cache(city, json):
  db_cursor.execute("INSERT INTO weather_data (request, response, timestamp) VALUES (%s, %s, %s);", (city, json, datetime.now()))
  db_connection.commit()

def get_weather(api_key, city, language = "en", num_days=8):
    # Check if the weather data is already cached
    data = search_cache(city)

    # If not found in cache, make API call
    if not data:
        print("Not in cache")
        base_url = "http://api.openweathermap.org/data/2.5/forecast"
        params = {
            "q": city,
            "appid": api_key,
            "lang": language,
            "units": "metric",
            "cnt": min(num_days, 40)  # Limit to maximum 5 days (40 forecast entries)
        }
        response = requests.get(base_url, params=params)
        data = response.json()
        if response.status_code != 200:
            return None, None, None, None, None, None

        # Update cache with api response
        insert_cache(city, json.dumps(data))
    else:
        print("Found in cache")
        # Convert raw json string from cache to python object
        data = json.loads(data)

    # If we are here, we have data
    city_name = data["city"]["name"]
    country_name = data["city"]["country"]
    sunrise = data["city"]["sunrise"]
    sunset = data["city"]["sunset"]
    timezone = data["city"]["timezone"]
    weather_info = []
    for forecast in data["list"]:
        weather = {
            "date": forecast["dt_txt"],
            "temperature": forecast["main"]["temp"],
            "humidity": forecast["main"]["humidity"],
            "pressure": forecast["main"]["pressure"],
            "wind_speed": forecast["wind"]["speed"],
            "weather_condition": forecast["weather"][0]["description"],
            "sea_level": forecast["main"]["sea_level"],
            "grnd_level": forecast["main"]["grnd_level"],
            "wind_speed": forecast["wind"]["speed"],
        }
        weather_info.append(weather)

    return city_name, country_name, sunrise, sunset, timezone, weather_info[:num_days]
       

@app.route('/', methods=['GET'])
def index():
    city_name = request.args.get("city")
    if city_name:
        # Get the city name entered by the user
        # city_name = request.form['city']

        # Get weather data for the entered city (English)
        city, country,sunrise,sunset,timezone, weather_data = get_weather(API_KEY, city_name, "en")

        if weather_data is not None:
             # Convert the timestamp to a datetime object
            datetime_obj = datetime.fromtimestamp(sunrise)

            # Retrieve the date from the datetime object
            date = datetime_obj.date()
            return render_template('weather.html',date=date, city=city, country=country,sunrise=sunrise,sunset=sunset,timezone=timezone, weather=weather_data)
        else:
            error_message = "Failed to retrieve weather data for " + city_name
            return render_template('error.html', error=error_message)

    return render_template('index.html')

#TODO 
# @app.route('/weather/<city>', methods=['GET'])
# def weather_by_city(city):
#     # Get weather data for the specified city (English)
#     city, country, weather_data = get_weather(API_KEY, city, "en")
#     if weather_data is not None:
#         return render_template('weather.html', city=city, country=country, weather=weather_data)
#     else:
#         error_message = "Failed to retrieve weather data for " + city
#         return render_template('error.html', error=error_message)

# @app.route('/weather/<city>/<language>', methods=['GET'])
# def weather_by_city_and_language(city, language):
#     # Get weather data for the specified city and language
#     city, country, weather_data = get_weather(API_KEY, city, language)
#     if weather_data is not None:
#         return render_template('weather.html', city=city, country=country, weather=weather_data)
#     else:
#         error_message = "Failed to retrieve weather data for " + city
#         return render_template('error.html', error=error_message)

if __name__ == '__main__':
    app.run(debug=True)