from configparser import ConfigParser
from lib2to3.pgen2.pgen import PgenGrammar
from pathlib import Path
import urllib.request
import sys
import json
import shutil
import pigpio, time, os
#import keyboard
import threading



from PIL import Image
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

recordSize = 0
counter = 1

WINSIZE = [320, 240]

UPDATE = pg.USEREVENT + 1
UPDATE_event = pg.event.Event(UPDATE)


def logLaunch():
    logger.info("Starting {}".center(40, "=").format(PROGRAM_NAME))
    if MODE_READ_ONLY:
        logger.info("Read Only Mode".center(40, "="))
    if MODE_VERBOSE:
        logger.info("Verbose Logging".center(40, "="))


def deleteDirectory(dir):
    shutil.rmtree(dir)
    logger.debug("Deleting directory '{}'".format(dir))
    



def toggleBacklight():
    try:
        if pi.read(DISP_BL = 1):
                pi.write(DISP_BL, 0)
        else:
                pi.write(DISP_BL, 1)
    except TypeError as e:
        logger.debug("backlight error: {}".format(e))


def showSettings():
    #os.system("pkill fim")
    #os.system("fim -a -q resources/menus/settings/*.png")
    currentMode = "Settings"

def showAlbumSelection():
    #os.system("pkill fim; fim -a -q data/images/*.jpg")
    currentMode = "Albums"

def rotary_switch_interrupt(gpio,level,tim):
        time.sleep(0.3)
        logger.info("Count is: {}".format(counter))
        if(pi.read(Enc_SW) == 1):
                logger.debug("Short press")
                return
        logger.debug("Long press")
        # Step 1 – Convert event into event datatype of pygame 
        
        pg.event.post(UPDATE_event)    # event_name as parameter
        #if currentMode == "Albums": 
        #    showSettings()
        #elif currentMode == "Settings":
        #    showAlbumSelection()

# Callback fn:
def rotary_interrupt(gpio,level,tim):
        global last_DT, last_CLK,  last_gpio, counter, recordSize

        if gpio == Enc_DT:
                last_DT = level
        else:
                last_CLK = level

        if gpio != last_gpio:                                   # debounce
                last_gpio = gpio
                if gpio == Enc_DT and level == 1:
                        if last_CLK == 1:
                                counter += 1
                                if counter > recordSize:
                                    counter = 1
                                logger.debug("UP to {}".format(counter))
                elif gpio == Enc_CLK and level == 1:
                        if last_DT == 1:
                                counter -= 1
                                if counter < 1:
                                    counter = recordSize
                                logger.debug("DOWN to {}".format(counter))
                pg.event.post(UPDATE_event)



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
            #Display loading menu
        except (DiscogsConnectError, DiscogsCredentialError) as e:
            logger.error(e)
            quit()
        
    
    global currentMode
    currentMode = "Settings"
 

    #Check if last.fm connection is valid
    
    global pi
    
    pi = pigpio.pi()                # init pigpio deamon
    pi.write(DISP_BL, 1)
    pi.set_mode(Enc_DT, pigpio.INPUT)
    pi.set_mode(Enc_CLK, pigpio.INPUT)
    pi.set_mode(Enc_SW, pigpio.INPUT)
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
        #fullPath = ("{}{}".format(path, imageFile))
        #print(fullPath)
        #image = pg.image.load(fullPath)
        #screen.blit(image, (40, 0))
    
        #pg.display.update()
        #time.sleep(0.5)
    
    
    global counter
    global recordSize
    recordSize = len(records) - 1
    counter = int(recordSize / 2)
    currentRecord = records[counter]

    fullPath = ("{}{}".format(path, currentRecord))

    image = pg.image.load(fullPath)

    screen.blit(image, (40, 0))
    
    pg.display.update()

    #showSettings()


    while True:
        #toggleBacklight()
        for event in pg.event.get():
            if event.type == QUIT:
                pg.quit()
                sys.exit()
            if event.type == UPDATE:
                #logger.debug("pygame update to record {}".format(counter))
                currentRecord = records[counter]
                fullPath = ("{}{}".format(path, currentRecord))
                image = pg.image.load(fullPath)
                screen.blit(image, (40, 0))
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

