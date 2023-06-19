
from secrets import secrets
import displayio
from adafruit_display_text.label import Label
from adafruit_oauth2 import OAuth2
import time

ignore_events=[
    "spep",
]

class GoogleEvents(displayio.Group):
    def __init__(self, calendar_id, display, fonts, requests):
        super().__init__()
        self.calendar_id = calendar_id
        self.max_events = 10
        self.events = []
        self.display = display # pyportal.splash
        self.requests = requests

        # Initialize an OAuth2 object with GCal API scope
        scopes = ["https://www.googleapis.com/auth/calendar.readonly"]
        self.google_auth = OAuth2(
            requests,
            secrets["google_client_id"],
            secrets["google_client_secret"],
            scopes,
            secrets["google_access_token"],
            secrets["google_refresh_token"],
        )

        if not self.google_auth.refresh_access_token():
            raise RuntimeError("Unable to refresh access token - has the token been revoked?")
        self.access_token_obtained = int(time.monotonic())


        display.append(self)
        self._text_group = displayio.Group()
        self.append(self._text_group)



        def make_label(x,y,text=""):
            l = Label(fonts.roboto_21) 
            l.x = x
            l.y = y
            l.text = text
            l.color = 0xFFFFFF
            return l

        self.event_1_title = make_label(5, 138)
        self._text_group.append(self.event_1_title)

        self.event_1_time = make_label(5, 163)
        self._text_group.append(self.event_1_time)

        self.event_1_diff = Label(fonts.roboto_21)
        self.event_1_diff.anchor_point = (1.0, 0.0)
        self.event_1_diff.anchored_position = (150, 155)
        self.event_1_diff.color = 0xFFFFFF
        self._text_group.append(self.event_1_diff)

        self.event_2_title = make_label(5, 197)
        self._text_group.append(self.event_2_title)

        self.event_2_time = make_label(5, 222)
        self._text_group.append(self.event_2_time)

        self.event_2_diff = Label(fonts.roboto_21)
        self.event_2_diff.anchor_point = (1.0, 0.0)
        self.event_2_diff.anchored_position = (150, 215)
        self.event_2_diff.color = 0xFFFFFF
        self._text_group.append(self.event_2_diff)



    def format_datetime(self, datetime, do_diff=True):
        """Formats ISO-formatted datetime returned by Google Calendar API into
        a struct_time.
        :param str datetime: Datetime string returned by Google Calendar API
        :return: struct_time

        """
        times = datetime.split("T")
        the_date = times[0]
        the_time = times[1]
        year, month, mday = [int(x) for x in the_date.split("-")]
        the_time = the_time.split("-")[0]
        if "Z" in the_time:
            the_time = the_time.split("Z")[0]
        hours, minutes, _ = [int(x) for x in the_time.split(":")]
        # am_pm = "am"
        # if hours >= 12:
        #     am_pm = "pm"
        #     # convert to 12hr time
        #     hours -= 12
        # via https://github.com/micropython/micropython/issues/3087
        formatted_time = "{:02d}:{:02d}".format(hours, minutes)

        now = time.localtime()  #struct_time(tm_year=2023, tm_mon=6, tm_mday=17, tm_hour=15, tm_min=4, tm_sec=17, tm_wday=5, tm_yday=168, tm_isdst=-1)

        if not do_diff:
            past = True
            if now[3] < hours or (now[3] == hours and now[4] < minutes) or now[2] < mday:
                past = False
            return formatted_time, hours, minutes, past
        
        day_man = 24*60 # minutes in a day
        diff_future = (mday - now[2])*day_man + (hours - now[3]) * 60 + (minutes - now[4])
        diff = ""
        if diff_future<0 and mday==now[2]:
            diff += "-"

        diff_future = abs(diff_future)

        # < 60min
        if diff_future <= 60:
            diff += "{}min".format(diff_future)
        elif 60 < diff_future < 120:
            diff += "1h{}".format(diff_future-60)
        elif 120 <= diff_future < day_man:
            h = diff_future // 60
            diff += "{}h+".format(h)
        else:
            h = (diff_future % day_man) // 60 
            diff += "1d+"

        return formatted_time, diff
    
    
    def get_calendar_events(self, calendar_id=None):
        """Returns events on a specified calendar.
        Response is a list of events ordered by their start date/time in ascending order.
        """
        if calendar_id is None:
            calendar_id = self.calendar_id

        time_min = self.get_current_time(False)
        time_max = self.get_current_time(time_max=True)
        print("Fetching calendar events from {0} to {1}".format(time_min, time_max))

        headers = {
            "Authorization": "Bearer " + self.google_auth.access_token,
            "Accept": "application/json",
            "Content-Length": "0",
        }
        url = (
            "https://www.googleapis.com/calendar/v3/calendars/{0}"
            "/events?maxResults={1}&timeMin={2}&timeMax={3}&orderBy=startTime"
            "&singleEvents=true".format(calendar_id, self.max_events, time_min, time_max)
        )
        resp = self.requests.get(url, headers=headers)
        resp_json = resp.json()
        if "error" in resp_json:
            raise RuntimeError("Error:", resp_json)
        resp.close()
        # parse the 'items' array so we can iterate over it easier
        self.events.clear()
        resp_items = resp_json["items"]
        if not resp_items:
            print("No events scheduled for today!")
        for event in range(0, len(resp_items)):
            self.events.append(resp_items[event])
        
        return self.events
    
    def get_current_time(self, time_max=False):
        # Format as RFC339 timestamp
        cur_time = time.localtime()
        if time_max:  # maximum time to fetch events is midnight (4:59:59UTC)
            cur_time_max = time.struct_time(
                (
                    cur_time[0],
                    cur_time[1],
                    cur_time[2] + 2, # 2 days ahead instead of one, i.e. tomrrow midnight instead of today midnight
                    4,
                    59,
                    59,
                    cur_time[6],
                    cur_time[7],
                    cur_time[8],
                )
            )
            cur_time = cur_time_max
        cur_time = "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}{:s}".format(
            cur_time[0],
            cur_time[1],
            cur_time[2],
            cur_time[3],
            cur_time[4],
            cur_time[5],
            "Z",
        )
        return cur_time
    
    def cycle(self):
        # check if we need to refresh token
        if (int(time.monotonic()) - self.access_token_obtained >= self.google_auth.access_token_expiration):
            print("Access token expired, refreshing...")
            if not self.google_auth.refresh_access_token():
                raise RuntimeError("Unable to refresh access token - has the token been revoked?")
            self.access_token_obtained = int(time.monotonic())

    def clear_event_1(self):
        self.event_1_title.text = ""
        self.event_1_time.text = ""
        self.event_1_diff.text = ""

    def clear_event_2(self):
        self.event_2_title.text = ""
        self.event_2_time.text = ""
        self.event_2_diff.text = ""

    def loading_msg(self):
        self.clear_event_2()
        self.event_1_title.text = "loading..."
        self.event_1_time.text = ""
        self.event_1_diff.text = ""

    def display_events(self):
        cursor = 0
        placed_events = 0

        while True:
            if cursor == len(self.events):
                break
            
            event = self.events[cursor]
            event_name = event["summary"][:15]
            ignore = False
            for name in ignore_events:
                if event_name == name:
                    ignore = True
                    break
            _, _, _, past = self.format_datetime(event["end"]["dateTime"], do_diff=False)
            if past or ignore:
                print ('ignoring event "{}"'.format(event_name))
                cursor += 1
                continue
            
            start, diff = self.format_datetime(event["start"]["dateTime"])
            
            if placed_events == 0:
                self.event_1_title.text = event_name
                self.event_1_time.text = start
                self.event_1_diff.text = diff
            else:
                self.event_2_title.text = event_name
                self.event_2_time.text = start
                self.event_2_diff.text = diff

            placed_events += 1
            cursor += 1
            if placed_events == 2:
                break
        
        if placed_events < 1:
            self.clear_event_1()
        if placed_events == 1:
            self.clear_event_2()
            
