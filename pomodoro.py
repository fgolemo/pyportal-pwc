
import displayio
from adafruit_display_text.label import Label
import time

cwd = ("/"+__file__).rsplit('/', 1)[0]
chime = cwd+"/chime1.wav"

class Pomodoro(displayio.Group):
    def __init__(self, touchscreen, display, fonts, player):
        super().__init__()
        self.display = display # pyportal.splash
        self.ts = touchscreen
        self.timer_min = 20
        self.timer_sec = 00
        self.timer_running = False
        self.timer = None
        self.player = player

        display.append(self)
        self._text_group = displayio.Group()
        self.append(self._text_group)

        self.timer_txt = Label(fonts.roboto_33) 
        self.timer_txt.anchor_point = (0.5, 0.0)
        self.timer_txt.anchored_position = (243, 167)
        self.timer_txt.text = "20 00"
        self.timer_txt.color = 0xFFFFFF
        self._text_group.append(self.timer_txt)

        self.btn_right = False
        self.btn_right_time = time.monotonic()
        self.btn_left = False
        self.btn_left_time = time.monotonic()
        
    def tick(self):
        # step the timer and display the results if new
        if self.timer_running:
            diff = time.monotonic() - self.timer
            if diff >= 1:
                seconds = diff % 60
                minutes = diff // 60
                self.timer_sec -= seconds
                if self.timer_sec < 0:
                    self.timer_sec += 60
                    minutes += 1
                self.timer_min -= minutes
                if self.timer_min < 0:
                    self.timer_min = 0
                    self.timer_sec = 0
                    self.timer_running = False
                    self.player(chime)
                    
                self.redraw()
                self.timer = time.monotonic()

    def redraw(self):
        colon = " "
        if self.timer_running:
            colon = ":"
        self.timer_txt.text = "{:02d}{}{:02d}".format(int(self.timer_min), colon, int(self.timer_sec))

    def btn_right_func(self):
        
        if not self.timer_running:
            print ("unpausing")
            # unpause
            self.timer = time.monotonic()
            self.timer_running = True
            
            # reset if at zero
            if self.timer_min == 0 and self.timer_sec == 0:
                self.timer_min == 20
            self.redraw()
        else:
            print ("pausing")
            # pause
            self.timer_running = False
            self.redraw()


    def btn_left_func(self):
        print ("resetting")
        self.timer_min = 20
        self.timer_sec = 0
        self.redraw()

    def check_touch(self):
        touch = self.ts.touch_point
        if touch:
            # print (touch) # top left: 160,110, bottom right 180,130
            if touch[0] <= 160 and touch[1] <= 110:
                # if self.btn_left or (time.monotonic() - self.btn_left_time) < 1:
                if self.btn_left:
                    # button was pressed before, ignoring
                    pass    
                else:
                    self.btn_left = True
                    # self.btn_left_time = time.monotonic()
                    # print ("btn left")
                    self.btn_left_func()
            else:
                self.btn_left = False
            
            if touch[0] >= 180 and touch[1] >= 130:
                # if self.btn_right or (time.monotonic() - self.btn_right_time) < 1:
                if self.btn_right:
                    # button was pressed before, ignoring
                    pass    
                else:
                    self.btn_right = True
                    # self.btn_right_time = time.monotonic()
                    # print ("btn right")
                    self.btn_right_func()
            else:
                self.btn_right = False
        else:
            if self.btn_left or self.btn_right:
                self.btn_left = False
                self.btn_right = False

