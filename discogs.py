import json

import discogs_client
from PIL import Image

def saveToJSON(filename, data):
    with open(filename, "w") as outfile:
        json.dump(data, outfile)

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