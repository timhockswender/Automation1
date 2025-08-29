import requests
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# --- Constants ---
API_BASE_URL = "https://api.open-meteo.com/v1/forecast"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
EMAIL_SUBJECT = "Your Daily Weather Forecast"
EMAIL_GREETING = "Good morning!\n\nHere is your daily weather forecast:\n\n"


# --- Configuration ---
# Your email details
sender_email = os.environ.get("SENDER_EMAIL")
password = os.environ.get("EMAIL_PASSWORD")

if not sender_email or not password:
    raise ValueError("SENDER_EMAIL and EMAIL_PASSWORD environment variables must be set")

# New: List of recipients
recipients = ["timhockswender@gmail.com", "chrishockswender@gmail.com"]

# Locations with their latitude and longitude
WMO_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}

def get_weather_description(wmo_code):
    """Returns a human-readable description for a WMO weather code."""
    return WMO_CODES.get(wmo_code, "Unknown weather code")

locations = {
    "Naples, FL": {"latitude": 26.1420, "longitude": -81.7948},
    "Davidson, NC": {"latitude": 35.5024, "longitude": -80.8437}
}

# --- Function to get the weather forecast ---
def get_weather(lat, lon):
    """Gets the weather forecast for a given latitude and longitude.

    Args:
        lat: The latitude of the location.
        lon: The longitude of the location.

    Returns:
        A dictionary containing the weather forecast, or None if the
        request fails.
    """
    base_url = API_BASE_URL
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,weathercode,precipitation_sum,precipitation_probability_max",
        "current_weather": True,
        "temperature_unit": "fahrenheit",
        "timezone": "America/New_York"
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raises an exception for bad status codes
        data = response.json()

        # Extract today's forecast
        weather_data = {
            "current_temp": data["current_weather"]["temperature"],
            "max_temp": data["daily"]["temperature_2m_max"][0],
            "min_temp": data["daily"]["temperature_2m_min"][0],
            "weather_code": data["daily"]["weathercode"][0],
            "precipitation_sum": data["daily"]["precipitation_sum"][0],
            "precipitation_probability_max": data["daily"]["precipitation_probability_max"][0]
        }
        return weather_data
    except requests.exceptions.RequestException as e:
        print(f"Could not retrieve weather: {e}")
        return None

# --- Email and Weather Functions ---
def build_weather_report(locations):
    """Builds the weather report for all locations.

    Args:
        locations: A dictionary where keys are location names and values are
                   dictionaries with "latitude" and "longitude".

    Returns:
        A formatted string with the weather report for all locations.
    """
    report = EMAIL_GREETING
    for location, coords in locations.items():
        weather_data = get_weather(coords["latitude"], coords["longitude"])
        if weather_data:
            report += f"{location}:\n"
            report += f"  Current Temp: {weather_data['current_temp']}°F\n"
            report += f"  High: {weather_data['max_temp']}°F | Low: {weather_data['min_temp']}°F\n"

            precipitation_prob = weather_data['precipitation_probability_max']
            if precipitation_prob > 0:
                weather_desc = get_weather_description(weather_data['weather_code'])
                report += f"  Precipitation: {weather_desc} ({precipitation_prob}% chance)\n"
                report += f"  Total Precipitation: {weather_data['precipitation_sum']}mm\n"
            report += "\n"
        else:
            report += f"{location}: Could not retrieve weather data.\n\n"
    return report

def send_email(email_body):
    """Sends an email with the given body to the configured recipients.

    Args:
        email_body: The body of the email to be sent.
    """
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = ", ".join(recipients)
    msg['Subject'] = EMAIL_SUBJECT

    msg.attach(MIMEText(email_body, 'plain'))

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, recipients, msg.as_string())
        print("Email sent successfully!")
    except smtplib.SMTPAuthenticationError:
        print("Error: SMTP authentication failed. Check your SENDER_EMAIL and EMAIL_PASSWORD.")
    except smtplib.SMTPException as e:
        print(f"An SMTP error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# --- Main Execution ---
if __name__ == "__main__":
    weather_report = build_weather_report(locations)
    send_email(weather_report)
