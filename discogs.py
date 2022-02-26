import json
from urllib.error import URLError
import urllib.request
from pathlib import Path
import time
from urllib import request

import discogs_client
from PIL import Image

class DiscogsConnectError(Exception):
    pass

class DiscogsCredentialError(Exception):
    pass

class DiscogsLibraryError(Exception):
    pass

class Discogs:

    TYPE_PARTIAL = "Partial"
    TYPE_FULL = "Full"

    def __init__(self, token, username, dataDirName, imageDirName, collectionFileName, programName, version, logger):
        self.token = token
        self.username = username
        self.dataDirName = dataDirName
        self.imageDirName = imageDirName
        self.collectionFileName = collectionFileName
        self.programName = programName
        self.version = version
        self.logger = logger
        self.client = ""
        self.user = ""

        self.collectionFileFQPath = "{}/{}".format(dataDirName, collectionFileName)
        self.imageDirFQPath = "{}/{}".format(dataDirName, imageDirName)

    
    def getLibrary(self):
        try:
            with open(self.collectionFileFQPath, "r") as infile:
                return json.load(infile)
        except FileNotFoundError:
            raise DiscogsLibraryError("No library found")

    def connect(self):
        clienttString = "{}/{}".format(self.programName, self.version)

        try:
            self.getClient()
            self.getUser()
        except Exception as e:
            raise

    def createLibraryDir(self):
        Path(self.imageDirFQPath).mkdir(parents=True, exist_ok=True)
        self.logger.info("Created library directory: {}".format(self.imageDirFQPath))

    def getClient(self):
        clientString = "{}/{}".format(self.programName, self.version)

        self.client = discogs_client.Client(clientString, user_token=self.token)

        try:
            self.client.identity()
            self.logger.info("Discogs Client Created")
        except discogs_client.exceptions.HTTPError:
            raise DiscogsCredentialError("Invalid token")

    def getUser(self):
        self.user = self.client.user(self.username)

        try:
            self.user.id
            self.logger.info("Discogs user created")
        except discogs_client.exceptions.HTTPError:
            raise DiscogsCredentialError("No such username")

    def fullLibraryUpdate(self):
        self.getRecordCollection(self.TYPE_FULL)
        self.logger.info("Full discogs library updated")

    def partialLibraryUpdate(self):
        self.getRecordCollection(self.TYPE_PARTIAL)
        self.logger.info("Partial discogs library updated")
            
    
    def saveToJSON(self, filename, data):
        with open(filename, "w") as outfile:
            json.dump(data, outfile)

    #Needed to download images from discogs
    def generateURLOpener(self):
        userAgentString = "{}/{}".format(self.programName, self.version)

        opener = urllib.request.build_opener()
        opener.addheaders = [('User-agent', userAgentString)]
        urllib.request.install_opener(opener)
        
    def saveAlbumArtwork(self, url, id, dest):
        filename = "{}/{}.jpg".format(dest, id)

        timesRetried = 0
        request.urlretrieve(url, filename)

        self.resizeImage(filename)

    def resizeImage(self, imageFile):
        basewidth = 240
        img = Image.open(imageFile)
        wpercent = (basewidth/float(img.size[0]))
        hsize = int((float(img.size[1])*float(wpercent)))
        img = img.resize((basewidth,hsize), Image.ANTIALIAS)
        img.save(imageFile)


    def getRecordCollection(self, type):
        self.generateURLOpener()
        userCollectionDict = {}
        collectionItems = self.getDiscogsUserCollection(self.user)

        totalAlbums = len(collectionItems)
        count = 0

        if type is self.TYPE_PARTIAL:
            currentCollection = self.getLibrary()

        for collectionItem in collectionItems:

            release = collectionItem.release
            id = release.id

            if type is self.TYPE_PARTIAL:
                if str(id) in currentCollection:
                    self.logger.debug("Album {} already exists".format(id))
                    continue

            
            #check if more than one artist
            if len(release.artists) != 1:
                self.logger.debug("More than 1 artist found on release {}".format(id))
            artist = release.artists[0].name

            #Download image
            imageURL = release.images[0]

            title = release.title

            tracks = []
            for track in release.tracklist:
                newTrack = {"title": track.title, "position": track.position, "duration": track.duration}
                tracks.append(newTrack)

            album = {"title": title, "artist": artist, "tracks": tracks}
            self.saveAlbumArtwork(imageURL.get("uri"), id, self.imageDirFQPath)
            self.logger.debug("Grabbed album: {}".format(album))
            userCollectionDict[id] = album


        self.saveToJSON(self.collectionFileFQPath, userCollectionDict)

    def getDiscogsUserCollection(self, user):
        #return user.collection_folders[1].releases #TODO remove: used for debugging
        return user.collection_folders[0].releases #0 is all folder


    def saveAlbumCollection(self, type):

        discogsClient = self.getDiscogsClient(self.programName, self.version, self.token)
        
        user = self.getDiscogsUser(discogsClient, self.username)
        
        userCollection = self.getRecordCollection(type, user)

        self.saveToJSON(self.collectionFileFQPath, userCollection)


