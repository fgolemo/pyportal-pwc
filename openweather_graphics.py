# SPDX-FileCopyrightText: 2019 Limor Fried for Adafruit Industries
#
# SPDX-License-Identifier: MIT

import time
import json
import displayio
from adafruit_display_text.label import Label
import adafruit_imageload


cwd = ("/"+__file__).rsplit('/', 1)[0] # the current working directory (where this file is)

weekdays = {
    0: "Mon",
    1: "Tue",
    2: "Wed",
    3: "Thu",
    4: "Fri",
    5: "Sat",
    6: "Sun",
}

months = {
    1: "Jan",
    2: "Feb",
    3: "Mar",
    4: "Apr",
    5: "May",
    6: "Jun",
    7: "Jul",
    8: "Aug",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Dec",
}

icons = {
    "01d": 0,
    "01n": 1,
    "02d": 2,
    "02n": 3,
    "03d": 4,
    "03n": 5,
    "04d": 6,
    "04n": 7,
    "09d": 8,
    "09n": 9,
    "10d": 10,
    "10n": 11,
    "11d": 12,
    "11n": 13,
    "13d": 14,
    "13n": 15,
    "50d": 16,
    "50n": 17
}

class OpenWeather_Graphics(displayio.Group): 
    def __init__(self, root_group, fonts, am_pm=True, celsius=True, adt=None):
        super().__init__()
        self.am_pm = am_pm
        self.celsius = celsius
        self.adt = adt

        root_group.append(self)
        self._icon_group = displayio.Group()
        self.append(self._icon_group)
        self._text_group = displayio.Group()
        self.append(self._text_group)

        self._icon_sprite = None
        self._icon_file = None
        # self.set_icon(cwd+"/weather_background.bmp")
        # self.set_icon(cwd+"/bg1.bmp")
        self.set_icon(cwd+"/bg4.bmp")

        self.city_text = None

        self.time_text = Label(fonts.roboto_33)
        self.time_text.x = 35
        self.time_text.y = 20
        self.time_text.color = 0xFFFFFF
        self._text_group.append(self.time_text)

        self.weekday_text = Label(fonts.roboto_33)
        # self.weekday_text.x = 60
        # self.weekday_text.y = 60
        self.weekday_text.color = 0xFFFFFF
        self.weekday_text.anchor_point = (0.5, 0.0)
        self.weekday_text.anchored_position = (75, 48)

        self._text_group.append(self.weekday_text)

        self.date_text = Label(fonts.roboto_33)
        self.date_text.x = 20
        self.date_text.y = 100
        self.date_text.color = 0xFFFFFF
        self._text_group.append(self.date_text)

        self.temp_text = Label(fonts.roboto_21)
        self.temp_text.anchor_point = (1.0, 0.0)
        self.temp_text.anchored_position = (316, 13)
        self.temp_text.color = 0xFFFFFF
        self._text_group.append(self.temp_text)

        self.roomtemp_text = Label(fonts.roboto_21)
        self.roomtemp_text.anchor_point = (1.0, 0.0)
        self.roomtemp_text.anchored_position = (316, 98)
        self.roomtemp_text.color = 0xFFFFFF
        self._text_group.append(self.roomtemp_text)

        self.room_text = Label(fonts.roboto_21)
        self.room_text.x = 165
        self.room_text.y = 105
        self.room_text.color = 0xFFFFFF
        self.room_text.text = "Room"
        self._text_group.append(self.room_text)

        self.weather_text = Label(fonts.roboto_21)
        self.weather_text.color = 0xFFFFFF
        self.weather_text.x = 165
        self.weather_text.y = 20
        self._text_group.append(self.weather_text)

        sprite_sheet, palette = adafruit_imageload.load(cwd+"/weather-icons3.bmp",
                                                bitmap=displayio.Bitmap,
                                                palette=displayio.Palette)
        palette.make_transparent(0)


        # Create a sprite (tilegrid)
        self.sprite = displayio.TileGrid(sprite_sheet, pixel_shader=palette,
                                    width = 1,
                                    height = 1,
                                    tile_width = 64,
                                    tile_height = 64)
        self.sprite[0] = 1
        self.sprite.x = 210
        self.sprite.y = 30
        self._text_group.append(self.sprite)

    def loading_time_msg(self):
        self.time_text.text = "loading"

    def loading_weather_msg(self):
        self.weather_text.text = "loading"

    def display_weather(self, weather):
        weather = json.loads(weather)

        weather_icon = weather['weather'][0]['icon']
        if weather_icon not in icons:
            print ("can't find icon:",weather_icon)
        self.sprite[0] = icons[weather_icon]

        self.update_time()

        main_text = weather['weather'][0]['main']
        
        print(main_text)
        if len(main_text) > 8:
            main_text = main_text[:8]
        self.weather_text.text = main_text

        temperature = weather['main']['temp'] - 273.15 # its...in kelvin
        print(temperature)
        if self.celsius:
            self.temp_text.text = "%d°C" % temperature
        else:
            self.temp_text.text = "%d°F" % ((temperature * 9 / 5) + 32)


    def update_time(self):
        """Fetch the time.localtime(), parse it out and update the display text"""
        now = time.localtime()
        # print (now)
        month = now[1]
        weekday = now[6]
        day = now[2]
        self.weekday_text.text = weekdays[weekday]
        self.date_text.text = "{0:02d}. {1}".format(day, months[month])
        hour = now[3]
        minute = now[4]
        format_str = "%02d:%02d"
        if self.am_pm:
            if hour >= 12:
                hour -= 12
                format_str = format_str+" PM"
            else:
                format_str = format_str+" AM"
            if hour == 0:
                hour = 12
        time_str = format_str % (hour, minute)
        print(time_str)
        self.time_text.text = time_str
        # self.time_text.text = "123\n456\n789\nabc\ndef\nghi"

    def update_roomtemp(self):
        temp = round(self.adt.temperature,1)
        self.roomtemp_text.text = str(temp)+"°C"


    def set_icon(self, filename):

        print("Set icon to ", filename)
        if self._icon_group:
            self._icon_group.pop()

        if not filename:
            return  # we're done, no icon desired

        if self._icon_file:
            self._icon_file.close()
        self._icon_file = open(filename, "rb")
        icon = displayio.OnDiskBitmap(self._icon_file)
        self._icon_sprite = displayio.TileGrid(
            icon, pixel_shader=getattr(icon, 'pixel_shader', displayio.ColorConverter()))

        # # CircuitPython 7+ compatible
        # icon = displayio.OnDiskBitmap(filename)
        # self._icon_sprite = displayio.TileGrid(icon, pixel_shader=background.pixel_shader)

        self._icon_group.append(self._icon_sprite)
