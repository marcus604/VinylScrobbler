from configparser import ConfigParser
from pathlib import Path
import urllib.request
import sys
import json
import shutil
import pigpio, time, os
import keyboard
import threading

import discogs_client
from PIL import Image

#Custom
from Classes import *
from log import getLogger, logging

PROGRAM_NAME = "VinylScrobbler"
VERSION = 0.2
DATA_DIR_NAME = "data"
IMAGE_DIR_NAME = "images"
COLLECTION_FILE_NAME = "userCollection.json"
COLLECTION_FILE_FQ = "{}/{}".format(DATA_DIR_NAME, COLLECTION_FILE_NAME)
IMAGE_DIR_FQ = "{}/{}".format(DATA_DIR_NAME, IMAGE_DIR_NAME)
TYPE_PARTIAL = "Partial"
TYPE_FULL = "Full"

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

counter = 100

def logLaunch():
    logger.info("Starting {}".center(40, "=").format(PROGRAM_NAME))
    if MODE_READ_ONLY:
        logger.info("Read Only Mode".center(40, "="))
    if MODE_VERBOSE:
        logger.info("Verbose Logging".center(40, "="))


def deleteDirectory(dir):
    shutil.rmtree(dir)
    logger.debug("Deleting directory '{}'".format(dir))
    

#Needed to download images from discogs
def generateURLOpener():
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    urllib.request.install_opener(opener)

def saveAlbumArtwork(url, id, dest):
    filename = "{}/{}.jpg".format(dest, id)

    urllib.request.urlretrieve(url, filename)

    resizeImage(filename)
        
def resizeImage(imageFile):
    basewidth = 240
    img = Image.open(imageFile)
    wpercent = (basewidth/float(img.size[0]))
    hsize = int((float(img.size[1])*float(wpercent)))
    img = img.resize((basewidth,hsize), Image.ANTIALIAS)
    img.save(imageFile)

def getRecordCollection(type, user):
    generateURLOpener()
    userCollectionDict = {}
    collectionItems = getDiscogsUserCollection(user)

    totalAlbums = len(collectionItems)
    count = 0

    if type is TYPE_PARTIAL:
        currentCollection = getCurrentCollection(COLLECTION_FILE_FQ)

    for collectionItem in collectionItems:

        release = collectionItem.release
        id = release.id

        if type is TYPE_PARTIAL:
            if str(id) in currentCollection:
                logger.debug("Album {} already exists".format(id))
                continue

        
        #check if more than one artist
        if len(release.artists) != 1:
            logger.debug("More than 1 artist found on release {}".format(id))
        artist = release.artists[0].name

        #Download image
        imageURL = release.images[0]

        title = release.title

        tracks = []
        for track in release.tracklist:
            newTrack = {"title": track.title, "position": track.position, "duration": track.duration}
            tracks.append(newTrack)

        album = {"title": title, "artist": artist, "tracks": tracks}
        saveAlbumArtwork(imageURL.get("uri"), id, IMAGE_DIR_FQ)
        logger.debug("Grabbed album: {}".format(album))
        userCollectionDict[id] = album

    return userCollectionDict


def getCurrentCollection(filename):
    with open(filename, "r") as infile:
        return json.load(infile)

def saveToJSON(filename, data):
    with open(filename, "w") as outfile:
        json.dump(data, outfile)


def getDiscogsUser(discogsClient, username):
    return discogsClient.user(username)

def getDiscogsUserCollection(user):
    #return user.collection_folders[1].releases #TODO remove: used for debugging
    return user.collection_folders[0].releases #0 is all folder


def getDiscogsClient(appName, version, userToken):
    clientString = "{}/{}".format(appName, version)

    return discogs_client.Client(clientString, user_token=userToken)

def saveAlbumCollection(type, config):

    discogsClient = getDiscogsClient(PROGRAM_NAME, VERSION, config["TOKEN"])
    
    user = getDiscogsUser(discogsClient, config["USERNAME"])
    
    userCollection = getRecordCollection(type, user)

    saveToJSON(COLLECTION_FILE_FQ, userCollection)

def toggleBacklight():
    try:
        if pi.read(DISP_BL = 1):
                pi.write(DISP_BL, 0)
        else:
                pi.write(DISP_BL, 1)
    except TypeError as e:
        logger.info("backlight error: {}".format(e))


def getDiscogsLibrary():
        #Get config file
        config = ConfigParser()

        config.read("config.ini")
        discogsConfig = config["DISCOGS"]

        Path(IMAGE_DIR_FQ).mkdir(parents=True, exist_ok=True)
        

        try:
                getCurrentCollection(COLLECTION_FILE_FQ)
        except FileNotFoundError:
                logger.info("No collection found")
                saveAlbumCollection(TYPE_FULL, discogsConfig)

def init():
        #Log startup
        logLaunch()
        global pi
        counter = 100
        pi = pigpio.pi()                # init pigpio deamon
        pi.write(DISP_BL, 1)
        pi.set_mode(Enc_DT, pigpio.INPUT)
        pi.set_mode(Enc_CLK, pigpio.INPUT)
        pi.set_mode(Enc_SW, pigpio.INPUT)
        pi.callback(Enc_DT, pigpio.EITHER_EDGE, rotary_interrupt)
        pi.callback(Enc_CLK, pigpio.EITHER_EDGE, rotary_interrupt)
        pi.callback(Enc_SW, pigpio.FALLING_EDGE, rotary_switch_interrupt)
        os.system("fim -a -q data/images/*.jpg")

def rotary_switch_interrupt(gpio,level,tim):
        time.sleep(0.3)
        print("Count is: {}".format(counter))
        if(pi.read(Enc_SW) == 1):
                print("short press")
                return
        print("long press")
        getDiscogsLibrary()


# Callback fn:
def rotary_interrupt(gpio,level,tim):
        global last_DT, last_CLK,  last_gpio, counter

        if gpio == Enc_DT:
                last_DT = level
        else:
                last_CLK = level

        if gpio != last_gpio:                                   # debounce
                last_gpio = gpio
                if gpio == Enc_DT and level == 1:
                        if last_CLK == 1:
                                counter += 1
                                keyboard.press_and_release('n')
                                print("UP to {}".format(counter))
                elif gpio == Enc_CLK and level == 1:
                        if last_DT == 1:
                                counter -= 1
                                keyboard.press_and_release('b')
                                print("DOWN to {}".format(counter))

# init and loop forever (stop with CTRL C)
init()
while 1:
        time.sleep(10)
        toggleBacklight()
