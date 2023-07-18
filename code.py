
import sys
import time
import board
from adafruit_pyportal import PyPortal
from fontloader import Fonts
from googlecal import GoogleEvents
import busio
import adafruit_adt7410
from analogio import AnalogIn
from pomodoro import Pomodoro

cwd = ("/"+__file__).rsplit('/', 1)[0] # the current working directory (where this file is)
sys.path.append(cwd)
import openweather_graphics  # pylint: disable=wrong-import-position



# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

# Use cityname, country code where countrycode is ISO3166 format.
# E.g. "New York, US" or "London, GB"
LOCATION = "Montreal, CA"

# Set up where we'll be fetching data from
DATA_SOURCE = "http://api.openweathermap.org/data/2.5/weather?q="+LOCATION
DATA_SOURCE += "&appid="+secrets['openweather_token']
# You'll need to get a token from openweather.org, looks like 'b6907d289e10d714a6e88b30761fae22'
DATA_LOCATION = []

# Calendar ID
CALENDAR_ID = "fgolemo@gmail.com"

# Amount of time to wait between refreshing the calendar, in minutes
REFRESH_TIME = 15

# Initialize the pyportal object and let us know what data to fetch and where
# to display it
pyportal = PyPortal(url=DATA_SOURCE,
                    json_path=DATA_LOCATION,
                    status_neopixel=board.NEOPIXEL,
                    default_bg=0x000000)
print ("Connecting to Wifi...")
pyportal.network.connect()

i2c_bus = busio.I2C(board.SCL, board.SDA)
adt = adafruit_adt7410.ADT7410(i2c_bus, address=0x48)
adt.high_resolution = True

light_sensor = AnalogIn(board.LIGHT)


fonts = Fonts(cwd)
gfx = openweather_graphics.OpenWeather_Graphics(pyportal.splash, adt=adt, fonts=fonts, am_pm=False, celsius=True)
gce = GoogleEvents(CALENDAR_ID, pyportal.splash, fonts, pyportal.network.requests)
ts = pyportal.touchscreen
pom = Pomodoro(pyportal.touchscreen, pyportal.splash, fonts, pyportal.play_file, pyportal.network._wifi.neopix)

def set_backlight(val):
    """Adjust the TFT backlight.
    :param val: The backlight brightness. Use a value between ``0`` and ``1``, where ``0`` is
                off, and ``1`` is 100% brightness.
    """
    val = max(0, min(1.0, val))
    try:
        board.DISPLAY.auto_brightness = False
    except AttributeError:
        pass
    board.DISPLAY.brightness = val

localtile_refresh = None
weather_refresh = None
cal_refresh = None

update_noncritical_1 = None
update_noncritical_2 = None

while True:

    pom.check_touch()
    pom.tick()

    # only set screen brightness and gauth token once per 30s (and on first run)
    if (not update_noncritical_1) or (time.monotonic() - update_noncritical_1) > 30:
        gce.cycle()
        light_value = light_sensor.value
        print('Light Value: ', light_value)
        
        # TODO make this a bit more nuanced
        # 6400-7400 bright daylight from the side
        if light_value < 1500: 
            # turn on the backlight
            set_backlight(1)
        else: 
            set_backlight(0.2)
        
        update_noncritical_1 = time.monotonic()


    # only query the online time once per hour (and on first run)
    if (not localtile_refresh) or (time.monotonic() - localtile_refresh) > 3600:
        try:
            print("Getting time from internet!")
            gfx.loading_time_msg()
            pyportal.get_local_time()
            localtile_refresh = time.monotonic()
        except Exception as e:
            print("Some error occured in time, retrying! -", e)
            continue

    # only query the weather every 10 minutes (and on first run)
    if (not weather_refresh) or (time.monotonic() - weather_refresh) > 600:
        try:
            gfx.loading_weather_msg()
            value = pyportal.fetch()
            print("Response is", value)
            gfx.display_weather(value)
            weather_refresh = time.monotonic()
        except Exception as e:
            print("Some error occured in weather, retrying! -", e)
            continue

    # only query the calendar every 10 minutes (and on first run)
    if (not cal_refresh) or (time.monotonic() - cal_refresh) > 600:
        try:
            gce.loading_msg()
            gce.get_calendar_events()
            print (gce.events)
            cal_refresh = time.monotonic()
        except Exception as e:
            print("Some error occured in cal, retrying! -", e)
            continue

    # only update time, events, and temp once per 30s (and on first run)
    if (not update_noncritical_2) or (time.monotonic() - update_noncritical_2) > 30:
        gfx.update_time()
        gfx.update_roomtemp()
        gce.display_events()
        
        update_noncritical_2 = time.monotonic()


    # no sleep here because for touches we have to be as fast as possible
    # time.sleep(30)  # wait 30 seconds before updating anything again
    pass


# ======================================================


# # SPDX-FileCopyrightText: 2021 Brent Rubell, written for Adafruit Industries
# #
# # SPDX-License-Identifier: Unlicense
# from adafruit_display_text.label import Label
# from adafruit_bitmap_font import bitmap_font
# from adafruit_oauth2 import OAuth2
# from adafruit_pyportal import Network, Graphics

# # Add a secrets.py to your filesystem that has a dictionary called secrets with "ssid" and
# # "password" keys with your WiFi credentials. DO NOT share that file or commit it into Git or other
# # source control.
# # pylint: disable=no-name-in-module,wrong-import-order
# try:
#     from secrets import secrets
# except ImportError:
#     print("WiFi secrets are kept in secrets.py, please add them there!")
#     raise

# network = Network()
# network.connect()

# graphics = Graphics()

# # DisplayIO Setup
# # Set up fonts
# font_small = bitmap_font.load_font("/fonts/Arial-12.bdf")
# font_large = bitmap_font.load_font("/fonts/Roboto-Medium-21.bdf")
# # preload fonts
# glyphs = b"0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-,.: "
# font_small.load_glyphs(glyphs)
# font_large.load_glyphs(glyphs)

# label_overview_text = Label(
#     font_large, x=0, y=45, text="To authorize this device with Google:"
# )
# graphics.splash.append(label_overview_text)

# label_verification_url = Label(font_small, x=0, y=100, line_spacing=1)
# graphics.splash.append(label_verification_url)

# label_user_code = Label(font_small, x=0, y=150)
# graphics.splash.append(label_user_code)

# label_qr_code = Label(font_small, x=0, y=190, text="Or scan the QR code:")
# graphics.splash.append(label_qr_code)

# # Set scope(s) of access required by the API you"re using
# scopes = ["https://www.googleapis.com/auth/calendar.readonly"]

# # Initialize an oauth2 object
# google_auth = OAuth2(
#     network.requests,
#     secrets["google_client_id"],
#     secrets["google_client_secret"],
#     scopes,
# )

# # Request device and user codes
# # https://developers.google.com/identity/protocols/oauth2/limited-input-device#step-1:-request-device-and-user-codes
# google_auth.request_codes()

# # Display user code and verification url
# # NOTE: If you are displaying this on a screen, ensure the text label fields are
# # long enough to handle the user_code and verification_url.
# # Details in link below:
# # https://developers.google.com/identity/protocols/oauth2/limited-input-device#displayingthecode
# print(
#     "1) Navigate to the following URL in a web browser:", google_auth.verification_url
# )
# print("2) Enter the following code:", google_auth.user_code)

# # modify display labels to show verification URL and user code
# label_verification_url.text = (
#     "1. On your computer or mobile device,\n    go to: %s"
#     % google_auth.verification_url
# )
# label_user_code.text = "2. Enter code: %s" % google_auth.user_code

# # Create a QR code
# graphics.qrcode(google_auth.verification_url.encode(), qr_size=2, x=170, y=165)
# graphics.display.show(graphics.splash)

# # Poll Google"s authorization server
# print("Waiting for browser authorization...")
# if not google_auth.wait_for_authorization():
#     raise RuntimeError("Timed out waiting for browser response!")

# print("Successfully Authenticated with Google!")

# # print formatted keys for adding to secrets.py
# print("Add the following lines to your secrets.py file:")
# print("\t'google_access_token' " + ":" + " '%s'," % google_auth.access_token)
# print("\t'google_refresh_token' " + ":" + " '%s'" % google_auth.refresh_token)
# # Remove QR code and code/verification labels
# graphics.splash.pop()
# graphics.splash.pop()
# graphics.splash.pop()

# label_overview_text.text = "Successfully Authenticated!"
# label_verification_url.text = (
#     "Check the REPL for tokens to add\n\tto your secrets.py file"
# )

# # prevent exit
# while True:
#     pass