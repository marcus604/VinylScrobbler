#Libraries
from configparser import ConfigParser
from pathlib import Path
import urllib.request
import sys
import json
import shutil

import discogs_client
from PIL import Image

#Custom
from Classes import *
from log import getLogger, logging


PROGRAM_NAME = "VinylScrobbler"
VERSION = 0.1
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






##################################################
#################Main Application#################
##################################################
def main():
    #Log startup
    logLaunch()

    #### Logic
    #Rotary button is pressed to wake up
    #Show album in middle (can scroll backwards and forwards)
    #Single tap to load album info
    #Every hour check for updates to discogs library

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

    while True:
        
        #Show loading on display if load takes too long
        #if no existing database (.json) then grab albums from discogs
        #Show middle album
        #Wait for input
        selection = input("refresh: p/f/q: ")

        if selection == "p":
            logger.info("Starting partial scan")
            saveAlbumCollection(TYPE_PARTIAL, discogsConfig)
        elif selection == "f":
            logger.info("Starting full rebuild")
            deleteDirectory(DATA_DIR_NAME)
            Path(IMAGE_DIR_FQ).mkdir(parents=True, exist_ok=True)
            saveAlbumCollection(TYPE_FULL, discogsConfig)
        elif selection == "q":
            break

    
    logger.info("Finished {}".center(40, "=").format(PROGRAM_NAME))

    
        
    
    
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
