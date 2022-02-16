from configparser import ConfigParser
import sys
import shutil
import pigpio, time, os
import pygame as pg
from pygame.locals import *

#Custom
from Classes import *
from discogs import *
from log import getLogger, logging

PROGRAM_NAME = "VinylScrobbler"
VERSION = 0.2
DATA_DIR_NAME = "data"
IMAGE_DIR_NAME = "images"
COLLECTION_FILE_NAME = "userCollection.json"

logger = getLogger(__name__, "logs/{}.log".format(PROGRAM_NAME))

MODE_READ_ONLY = False
MODE_VERBOSE = False

#GPIO Pins
Enc_DT = 17
Enc_CLK = 18
Enc_SW = 4
DISP_BL = 21

pi = 0

last_DT = 1
last_CLK = 1
last_gpio = 0

numOfRecords = 0
counter = 1

WINSIZE = [320, 240]

#Pygame Events
ROTARY_UP = pg.USEREVENT + 1
ROTARY_DOWN = pg.USEREVENT + 2
ROTARY_SHORT = pg.USEREVENT + 3
ROTARY_LONG = pg.USEREVENT + 4

ROTARY_UP_event = pg.event.Event(ROTARY_UP)
ROTARY_DOWN_event = pg.event.Event(ROTARY_DOWN)
ROTARY_SHORT_event = pg.event.Event(ROTARY_SHORT)
ROTARY_LONG_event = pg.event.Event(ROTARY_LONG)


def logLaunch():
    logger.info("Starting {}".center(40, "=").format(PROGRAM_NAME))
    if MODE_READ_ONLY:
        logger.info("Read Only Mode".center(40, "="))
    if MODE_VERBOSE:
        logger.info("Verbose Logging".center(40, "="))

def toggleBacklight():
    try:
        if pi.read(DISP_BL = 1):
                pi.write(DISP_BL, 0)
        else:
                pi.write(DISP_BL, 1)
    except TypeError as e:
        logger.debug("backlight error: {}".format(e))


def rotary_switch_interrupt(gpio,level,tim):
        time.sleep(0.3)
        if(pi.read(Enc_SW) == 1):
                pg.event.post(ROTARY_SHORT_event)
                return
        pg.event.post(ROTARY_LONG_event)    
        

# Callback fn:
def rotary_interrupt(gpio,level,tim):
        global last_DT, last_CLK,  last_gpio, counter, numOfRecords

        if gpio == Enc_DT:
                last_DT = level
        else:
                last_CLK = level

        if gpio != last_gpio:                                   # debounce
                last_gpio = gpio
                if gpio == Enc_DT and level == 1:
                        if last_CLK == 1:
                                counter += 1
                                if counter > numOfRecords:
                                    counter = 1
                                logger.debug("UP to {}".format(counter))
                                pg.event.post(ROTARY_UP_event)
                elif gpio == Enc_CLK and level == 1:
                        if last_DT == 1:
                                counter -= 1
                                if counter < 1:
                                    counter = numOfRecords
                                logger.debug("DOWN to {}".format(counter))
                                pg.event.post(ROTARY_DOWN_event)
                



##################################################
#################Main Application#################
##################################################
def main():

    #Log startup
    logLaunch()
    
    config = ConfigParser()
    
    config.read("config.ini")
    logger.debug("Loaded config")

    discogsConfig = config["DISCOGS"]

    discogs = Discogs(
        discogsConfig["TOKEN"],
        discogsConfig["USERNAME"],
        DATA_DIR_NAME,
        IMAGE_DIR_NAME,
        COLLECTION_FILE_NAME,
        PROGRAM_NAME,
        VERSION,
        logger)

    try:
        discogs.getLibrary()
    except DiscogsLibraryError as e:
        logger.debug(e)
        try:
            discogs.createLibraryDir()
            discogs.connect()
            discogs.fullLibraryUpdate()
        except (DiscogsConnectError, DiscogsCredentialError) as e:
            logger.error(e)
            quit()
        
    
    #Check if last.fm connection is valid
    
    global pi
    
    pi = pigpio.pi()                # init pigpio deamon
    pi.write(DISP_BL, 1)
    pi.set_mode(Enc_DT, pigpio.INPUT)
    pi.set_mode(Enc_CLK, pigpio.INPUT)
    pi.set_mode(Enc_SW, pigpio.INPUT)
    pi.set_glitch_filter(Enc_SW, 1000)
    pi.callback(Enc_DT, pigpio.EITHER_EDGE, rotary_interrupt)
    pi.callback(Enc_CLK, pigpio.EITHER_EDGE, rotary_interrupt)
    pi.callback(Enc_SW, pigpio.FALLING_EDGE, rotary_switch_interrupt)
    
    
    pg.init()
    pg.mouse.set_visible(False)
    screen = pg.display.set_mode(WINSIZE)
    black = 20, 20, 40
    screen.fill(black)

    path = 'data/images/'

    imageFiles = os.listdir(path)

    records = []

    for imageFile in imageFiles:
        records.append(imageFile)    
    
    global counter
    global numOfRecords
    numOfRecords = len(records) - 1
    counter = int(numOfRecords / 2)
    currentRecord = records[counter]

    fullPath = ("{}{}".format(path, currentRecord))

    image = pg.image.load(fullPath)

    screen.blit(image, (40, 0))
    
    pg.display.update()


    while True:
        #toggleBacklight()
        for event in pg.event.get():
            if event.type == QUIT:
                pg.quit()
                sys.exit()
            elif event.type == ROTARY_UP or event.type == ROTARY_DOWN:
                currentRecord = records[counter]
                fullPath = ("{}{}".format(path, currentRecord))
                image = pg.image.load(fullPath)
                screen.blit(image, (40, 0))
            elif event.type == ROTARY_SHORT:
                logger.debug("Short press PG")
            elif event.type == ROTARY_LONG:
                logger.debug("long press PG")
            
        pg.display.update()


##################################################
#####################Launcher#####################
##################################################
if __name__ == "__main__":

    VERBOSE_FLAG = "-v"         
    READ_ONLY_FLAG = "-r"       
    
    logLevel = logging.INFO
    if len(sys.argv) != 1:
        for arg in sys.argv[1:]:
            if arg == VERBOSE_FLAG:
                logLevel = logging.DEBUG
                MODE_VERBOSE = True
            if arg == READ_ONLY_FLAG:
                MODE_READ_ONLY = True
    
    logger.setLevel(logLevel)
    main()

