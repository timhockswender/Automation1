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
        A string containing the weather forecast, or an error message if the
        request fails.
    """
    base_url = API_BASE_URL
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,weathercode",
        "current_weather": True,
        "temperature_unit": "fahrenheit",
        "timezone": "America/New_York"
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raises an exception for bad status codes
        data = response.json()

        # Extract today's forecast
        current_temp = data["current_weather"]["temperature"]
        max_temp = data["daily"]["temperature_2m_max"][0]
        min_temp = data["daily"]["temperature_2m_min"][0]

        return f"Current Temp: {current_temp}°F | High: {max_temp}°F | Low: {min_temp}°F"
    except requests.exceptions.RequestException as e:
        return f"Could not retrieve weather: {e}"

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
        forecast = get_weather(coords["latitude"], coords["longitude"])
        report += f"{location}: {forecast}\n"
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
