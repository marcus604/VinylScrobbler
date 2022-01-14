import os
from enum import Enum

from PIL import Image, ImageDraw, ImageFont

class MENU_SETTINGS(Enum):
    ALBUM = 1
    SYNC = 2
    RESET = 3

    def __str__(self):
        return self.name.capitalize()

class MENU_SELECT_DISC(Enum):
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6

    def __str__(self):
        return "Disc {}".format(self.value)
    
class MENU_SELECT_SIDE(Enum):
    A = 1
    B = 2

    def __str__(self):
        return "Side {}".format(self.name)



RESOURCES_DIR = "resources/menus"

DIR_SETTINGS = "settings"
DIR_SELECT_DISC = "select_disc"
DIR_SELECT_SIDE = "select_side"

EXT_STRING = ".png"

DISPLAY_DIMENSIONS = (240,240)

FONT_REGULAR_STRING = "DejaVuSans.ttf"
FONT_BOLD_STRING = "DejaVuSans-Bold.ttf"
FONT_SIZE = 32
FONT_COLOUR = (255,255,255)

def drawMenu(img, menuOptions, selected):
    draw = ImageDraw.Draw(img) 
    imageWidth, imageHeight = img.size 
    font = ImageFont.truetype(FONT_REGULAR_STRING, size=FONT_SIZE)
    fontBold = ImageFont.truetype(FONT_BOLD_STRING, size=FONT_SIZE)

    spacing = 0
    
    for option in menuOptions:
        optionString = str(option)
        width, height = draw.textsize(optionString, font)
        spacing += (imageHeight - height) // (len(menuOptions) + 1)
        
        position = (20, spacing)
        if option is selected:
            draw.text(position, optionString, fill=FONT_COLOUR, font=fontBold)
        else:
            draw.text(position, optionString, fill=FONT_COLOUR, font=font)

    return img


def generateMenuImages(menuOptions, path):

    count = 1
    for option in menuOptions:
        img = Image.new("RGB", DISPLAY_DIMENSIONS, color = 'black')
        img = drawMenu(img, menuOptions, option)

        menuNameString = "{}/{}/{}-{}{}".format(RESOURCES_DIR, path, count, str(option), EXT_STRING)
        img.save(menuNameString)
        count += 1



#generateMenuImages(MENU_SETTINGS, DIR_SETTINGS)
#generateMenuImages(MENU_SELECT_DISC, DIR_SELECT_DISC)
#generateMenuImages(MENU_SELECT_SIDE, DIR_SELECT_SIDE)
