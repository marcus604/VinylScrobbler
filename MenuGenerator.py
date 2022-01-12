from PIL import Image, ImageDraw, ImageFont
import os

START_MENU_ALBUM = "Albums"
START_MENU_SYNC = "Sync"
START_MENU_RESET = "Reset"

SELECT_MENU_DISC1 = "Disc 1"
SELECT_MENU_DISC2 = "Disc 2"
SELECT_MENU_DISC3 = "Disc 3"
SELECT_MENU_DISC4 = "Disc 4"
SELECT_MENU_DISC5 = "Disc 5"
SELECT_MENU_DISC6 = "Disc 6"

SELECT_MENU_SIDEA = "Side A"
SELECT_MENU_SIDEB = "Side B"


RESOURCES_DIR = "resources/menus"

START_DIR = "start"
SELECT_DISC_DIR = "select_disc"
SELECT_SIDE_DIR = "select_side"

EXT_STRING = ".png"


FONT_REGULAR_STRING = "DejaVuSans.ttf"
FONT_BOLD_STRING = "DejaVuSans-Bold.ttf"

FONT_SIZE = 32
FONT_COLOUR = (255,255,255)

def drawMenu(img, options, selected):
    draw = ImageDraw.Draw(img) 
    imageWidth, imageHeight = img.size 
    font = ImageFont.truetype(FONT_REGULAR_STRING, size=FONT_SIZE)
    fontBold = ImageFont.truetype(FONT_BOLD_STRING, size=FONT_SIZE)

    spacing = 0
    
    for option in options:
        width, height = draw.textsize(option, font)
        spacing += (imageHeight - height) // (len(options) + 1)
        
        position = (20, spacing)
        if option is selected:
            draw.text(position, option, fill=FONT_COLOUR, font=fontBold)
        else:
            draw.text(position, option, fill=FONT_COLOUR, font=font)

    return img


def generateMenuImages(options, path):

    for option in options:
        img = Image.new("RGB", (240,240), color = 'black')
        img = drawMenu(img, options, option)

        menuNameString = "{}/{}/{}{}".format(RESOURCES_DIR, path, option, EXT_STRING)
        img.save(menuNameString)

startMenus = [START_MENU_ALBUM, START_MENU_SYNC, START_MENU_RESET]

selectDiscMenus = [SELECT_MENU_DISC1, SELECT_MENU_DISC2, SELECT_MENU_DISC3, SELECT_MENU_DISC4, SELECT_MENU_DISC5, SELECT_MENU_DISC6]
selectSideMenus = [SELECT_MENU_SIDEA, SELECT_MENU_SIDEB]

#generateMenuImages(startMenus, START_DIR)
#generateMenuImages(selectDiscMenus, SELECT_DISC_DIR)
#generateMenuImages(selectSideMenus, SELECT_SIDE_DIR)







