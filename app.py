from flask import Flask, render_template, request
import datetime
import requests
import os
from config import API_KEY, DB_URL
import cachetools
import mysql.connector


app = Flask(__name__, static_folder='/assets')

# Create the cache with a maximum size of 1000 entries and 15-minute TTL
cache = cachetools.TTLCache(maxsize=1000, ttl=900)

# Connect to the MySQL database
db_connection = mysql.connector.connect(
    host=DB_URL,
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME')
)
db_cursor = db_connection.cursor()

def get_weather(api_key, city, language="en", num_days=8):
    # Check if the weather data is already cached
    cached_data = cache.get(city)
    if cached_data:
        return cached_data
    # Check if the weather data is stored in the database
    db_cursor.execute("SELECT * FROM weather_data WHERE city = %s", (city,))
    db_data = db_cursor.fetchone()

    if db_data:
        # Retrieve the weather data from the database
        city_name, country_name, sunrise, sunset, timezone, weather_info = db_data
    else:
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

        if response.status_code == 200:
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

            # Cache the weather data
            cache[city] = (city_name, country_name, sunrise, sunset, timezone, weather_info[:num_days])
            # Insert the weather data into the database
            db_cursor.execute("INSERT INTO weather_data (city, city_name, country_name, sunrise, sunset, timezone, weather_info) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                              (city, city_name, country_name, sunrise, sunset, timezone, str(weather_info[:num_days])))
            db_connection.commit()
        else:
            return None, None, None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get the city name entered by the user
        city_name = request.form['city']

        # Get weather data for the entered city (English)
        city, country,sunrise,sunset,timezone, weather_data = get_weather(API_KEY, city_name, "en")

        # Convert the timestamp to a datetime object
        datetime_obj = datetime.datetime.fromtimestamp(sunrise)

        # Retrieve the date from the datetime object
        date = datetime_obj.date()

        if weather_data is not None:
            return render_template('weather.html',date=date, city=city, country=country,sunrise=sunrise,sunset=sunset,timezone=timezone, weather=weather_data)
        else:
            error_message = "Failed to retrieve weather data for " + city_name
            return render_template('error.html', error=error_message)

    return render_template('index.html')

@app.route('/weather/<city>', methods=['GET'])
def weather_by_city(city):
    # Get weather data for the specified city (English)
    city, country, weather_data = get_weather(API_KEY, city, "en")
    if weather_data is not None:
        return render_template('weather.html', city=city, country=country, weather=weather_data)
    else:
        error_message = "Failed to retrieve weather data for " + city
        return render_template('error.html', error=error_message)

@app.route('/weather/<city>/<language>', methods=['GET'])
def weather_by_city_and_language(city, language):
    # Get weather data for the specified city and language
    city, country, weather_data = get_weather(API_KEY, city, language)
    if weather_data is not None:
        return render_template('weather.html', city=city, country=country, weather=weather_data)
    else:
        error_message = "Failed to retrieve weather data for " + city
        return render_template('error.html', error=error_message)

if __name__ == '__main__':
    app.run(debug=True)