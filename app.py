from flask import Flask, render_template, request

import requests

app = Flask(__name__, static_folder='/assets')
def get_weather(api_key, city, language="en", num_days=8):
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
        weather_info = []
        for forecast in data["list"]:
            weather = {
                "date": forecast["dt_txt"],
                "temperature": forecast["main"]["temp"],
                "humidity": forecast["main"]["humidity"],
                "pressure": forecast["main"]["pressure"],
                "wind_speed": forecast["wind"]["speed"],
                "weather_condition": forecast["weather"][0]["description"],
            }
            weather_info.append(weather)

        return city_name, country_name, weather_info[:num_days]
    else:
        return None, None, None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get the city name entered by the user
        city_name = request.form['city']

        # API key
        api_key = "a9709dfa8608c8b21d7da65cc345af77"

        # Get weather data for the entered city (English)
        city, country, weather_data = get_weather(api_key, city_name, "en")
        if weather_data is not None:
            return render_template('weather.html', city=city, country=country, weather=weather_data)
        else:
            error_message = "Failed to retrieve weather data for " + city_name
            return render_template('error.html', error=error_message)

    return render_template('index.html')

@app.route('/weather/<city>', methods=['GET'])
def weather_by_city(city):
    # API key
    api_key = "a9709dfa8608c8b21d7da65cc345af77"

    # Get weather data for the specified city (English)
    city, country, weather_data = get_weather(api_key, city, "en")
    if weather_data is not None:
        return render_template('weather.html', city=city, country=country, weather=weather_data)
    else:
        error_message = "Failed to retrieve weather data for " + city
        return render_template('error.html', error=error_message)

@app.route('/weather/<city>/<language>', methods=['GET'])
def weather_by_city_and_language(city, language):
    # API key
    api_key = "a9709dfa8608c8b21d7da65cc345af77"

    # Get weather data for the specified city and language
    city, country, weather_data = get_weather(api_key, city, language)
    if weather_data is not None:
        return render_template('weather.html', city=city, country=country, weather=weather_data)
    else:
        error_message = "Failed to retrieve weather data for " + city
        return render_template('error.html', error=error_message)

if __name__ == '__main__':
    app.run(debug=True)