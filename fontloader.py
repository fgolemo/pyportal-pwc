from adafruit_bitmap_font import bitmap_font

class Fonts():
    def __init__(self, cwd):
        roboto_33_path = cwd+"/fonts/Roboto-Medium-33.bdf"
        roboto_21_path = cwd+"/fonts/Roboto-Medium-21.bdf"
        glyphs = b'0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-,.: '

        self.roboto_33 = bitmap_font.load_font(roboto_33_path)
        self.roboto_21 = bitmap_font.load_font(roboto_21_path)
        
        self.roboto_33.load_glyphs(glyphs)
        self.roboto_21.load_glyphs(glyphs)
