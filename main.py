from configparser import ConfigParser
import sys
import threading
import pigpio, time, os
import pygame as pg
from pygame.locals import *
import pygame_menu


#Custom
from Classes import *
from discogs import *
from lastfm import *
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

WINSIZE = [320, 240]

#Pygame Events
ROTARY_UP = pg.USEREVENT + 1
ROTARY_DOWN = pg.USEREVENT + 2
ROTARY_SHORT = pg.USEREVENT + 3
ROTARY_LONG = pg.USEREVENT + 4
DONE_SCROBBLING = pg.USEREVENT + 5

ROTARY_UP_event = pg.event.Event(ROTARY_UP)
ROTARY_DOWN_event = pg.event.Event(ROTARY_DOWN)
ROTARY_SHORT_event = pg.event.Event(ROTARY_SHORT)
ROTARY_LONG_event = pg.event.Event(ROTARY_LONG)
DONE_SCROBBLING_event = pg.event.Event(DONE_SCROBBLING)

path = 'data/images/'




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
                pg.event.post(pg.event.Event(pg.KEYDOWN, key=pg.K_RETURN, test=True))
                return
        pg.event.post(ROTARY_LONG_event)    
        

# Callback fn:
def rotary_interrupt(gpio,level,tim):
        global last_DT, last_CLK,  last_gpio

        if gpio == Enc_DT:
                last_DT = level
        else:
                last_CLK = level

        if gpio != last_gpio:                                   
                last_gpio = gpio
                if gpio == Enc_DT and level == 1:
                        if last_CLK == 1:
                                pg.event.post(pg.event.Event(pg.KEYDOWN, key=pg.K_DOWN, test=True))
                                pg.event.post(ROTARY_UP_event)
                elif gpio == Enc_CLK and level == 1:
                        if last_DT == 1:
                                pg.event.post(pg.event.Event(pg.KEYDOWN, key=pg.K_UP, test=True))
                                pg.event.post(ROTARY_DOWN_event)
                   

def showLoadingScreen(screen):

    theme = pygame_menu.themes.THEME_DARK.copy()
    theme.title = False
    theme.widget_font_size = 36
   

    menu = pygame_menu.Menu(
        title=False,
        width=320, 
        height=240,
        theme=theme,
        center_content=False,
        mouse_enabled=False,
        mouse_visible=False,
        onclose=pygame_menu.events.CLOSE,
        )  

    menu.add.label("Syncing Libary").translate(0, 70)
    progressLabel = menu.add.label("0%").translate(0, 90)    
    
    while True:

        events = pg.event.get()

        percentageDone = discogs.syncProgress
        if percentageDone == 100:
            menu.close()
            return
        elif percentageDone:
            progressString = "{}%".format(percentageDone)
            progressLabel.set_title(progressString)
        
        menu.update(events)
        
        if menu.is_enabled():
            menu.draw(screen)
            pg.display.update()
        else:
            return

def showSettingsMenu(screen):

    theme = pygame_menu.themes.THEME_DARK.copy()
    theme.title_bar_style = pygame_menu.widgets.MENUBAR_STYLE_SIMPLE
    theme.widget_selection_effect = pygame_menu.widgets.SimpleSelection()

    #Settings Menu
    menu = pygame_menu.Menu(
        'Settings', 320, 240,
        theme=theme,
        mouse_enabled=False,
        mouse_visible=False,
        onclose=pygame_menu.events.CLOSE,
        )   
    
    menu.add.button('Records', pygame_menu.events.CLOSE)
    menu.add.button('Sync', showSyncMenu, screen)
    menu.add.button('Quit', pygame_menu.events.EXIT)

    menu.mainloop(screen)

def showSyncMenu(screen):

    theme = pygame_menu.themes.THEME_DARK.copy()
    theme.title_bar_style = pygame_menu.widgets.MENUBAR_STYLE_SIMPLE
    theme.widget_selection_effect = pygame_menu.widgets.SimpleSelection()

    #Settings Menu
    menu = pygame_menu.Menu(
        'Settings', 320, 240,
        theme=theme,
        mouse_enabled=False,
        mouse_visible=False,
        onclose=pygame_menu.events.CLOSE,
        )  

    menu.add.button('Update', startSyncing, "Update", screen)
    menu.add.button('Reset & Sync', startSyncing, "Reset", screen)
    menu.add.button('Back', pygame_menu.events.CLOSE) 

    menu.mainloop(screen)

def resetScreen(screen):
    black = 20, 20, 40
    screen.fill(black)

def startSyncing(syncType, screen):
    if syncType == "Update":
        syncThread = threading.Thread(target=discogs.partialLibraryUpdate)
    elif syncType == "Full":
        syncThread = threading.Thread(target=discogs.fullLibraryUpdate)
    elif syncType == "Reset":
        syncThread = threading.Thread(target=discogs.reset)

    syncThread.start()

    showLoadingScreen(screen)



def startScrobbling(record, recordID, screen):
    name = record['title']
    artist = record['artist']
    tracks = record['tracks']

    global stopScrobbling
    stopScrobbling = False
    logger.info("Scrobbling record: {} - {}".format(artist, name))
    scrobbleThread = threading.Thread(target=scrobbleRecord, args=[record])
    logger.debug("Starting new thread")
    scrobbleThread.start()

    showNowScrobblingMenu(record, recordID, screen)
    logger.info("Stop scrobbling")
    stopScrobbling = True

def scrobbleRecord(record):
    artist = record['artist']
    album = record['title']
    tracks = record['tracks']
    global stopScrobbling

    for track in tracks:
        if stopScrobbling:
            break
        trackTitle = track['title']
        logger.info("Now Playing {} - {} - {}".format(artist, album, trackTitle))
        duration = track['duration']
        halfwayTime = int(time.time()) + (duration / 2)
        endTime = int(time.time()) + duration
        lastfm.updateNowPlaying(artist, album, trackTitle)
        scrobbled = False
        while True:
            if stopScrobbling:
                break
            currentTime = int(time.time())
            if scrobbled:
                if (endTime - currentTime) <= 1:
                    if track == tracks[-1]:
                        logger.info("Finished scrobbling album")
                    break
            elif (halfwayTime - currentTime) <= 1:
                lastfm.scrobble(artist, album, trackTitle, currentTime)
                scrobbled = True
                logger.info("Scrobbled: {} - {} - {}".format(artist, album, trackTitle))         
    pg.event.post(DONE_SCROBBLING_event)
        
def showNowScrobblingMenu(record, recordID, screen):

    imagePath = ("{}{}.jpg".format(path, recordID))

    theme = pygame_menu.themes.THEME_DARK.copy()
    theme.title = False
    theme.widget_font_size = 16
    theme.widget_selection_effect = pygame_menu.widgets.SimpleSelection()
    theme.background_color = pygame_menu.BaseImage(
        image_path=imagePath,
        drawing_mode=pygame_menu.baseimage.IMAGE_MODE_CENTER
    )

    menu = pygame_menu.Menu(
        title=False,
        width=320, 
        height=240,
        theme=theme,
        center_content=False,
        mouse_enabled=False,
        mouse_visible=False,
        onclose=pygame_menu.events.CLOSE,
        )  

    buttonPosY = 200
    menu.add.button(
        'Stop', 
        pygame_menu.events.CLOSE,
        background_color=(51, 51, 51, 200),
        float=True).translate(0, buttonPosY) 
    
    while True:

        events = pg.event.get()
        
        for event in events:
            if event.type == DONE_SCROBBLING:
                menu.close()
                return
        
        menu.update(events)
        
        if menu.is_enabled():
            menu.draw(screen)
            pg.display.update()
        else:
            return
        
def showRecord(record, recordID, pg, screen):
    logger.debug("Record ID: {}".format(recordID))
    name = record['title']
    artist = record['artist']
    
    imagePath = ("{}{}.jpg".format(path, recordID))
   
    theme = pygame_menu.themes.THEME_DARK.copy()
    theme.widget_font_size = 20
    theme.title = False
    theme.widget_selection_effect = pygame_menu.widgets.SimpleSelection()    
    theme.background_color = pygame_menu.BaseImage(
        image_path=imagePath,
        drawing_mode=pygame_menu.baseimage.IMAGE_MODE_CENTER
    )
       
    menu = pygame_menu.Menu(
        title=False,
        width=320, 
        height=240,
        theme=theme,
        center_content=False,
        mouse_enabled=False,
        mouse_visible=False,
        onclose=pygame_menu.events.CLOSE,
        )  

    padding = 0
  
    artistLabel = menu.add.label(
        artist, 
        background_color=(51, 51, 51, 200),
        max_char=-1,
        float=True  
    )

    try:
        for labelPart in artistLabel:
            labelPart.translate(0 , 0 + padding)
            padding = padding + 30
    except:
        artistLabel.translate(0, 0)
        padding = padding + 30
        
    namePos = 15
    nameLabel = menu.add.label(
        name, 
        background_color=(51, 51, 51, 200),
        max_char=-1,
        float=True  
    )
    
    try:
        for labelPart in nameLabel:
            labelPart.translate(0, namePos + padding)
            padding = padding + 30
    except:
        nameLabel.translate(0, namePos + padding)
           
    buttonsPosY = 200
    scrobbleBtnPosX = 80
    backBtnPosX = -80

    menu.add.button(
        "Scrobble",
        startScrobbling, 
        record,
        recordID,
        screen,
        background_color=(51, 51, 51, 200),
        align=pygame_menu.locals.ALIGN_LEFT,
        float=True).translate(scrobbleBtnPosX, buttonsPosY)

    menu.add.button(
        "Back",
        pygame_menu.events.CLOSE,
        background_color=(51, 51, 51, 200),
        align=pygame_menu.locals.ALIGN_RIGHT,
        float=True).translate(backBtnPosX, buttonsPosY) 

    menu.mainloop(screen)

def showRecordsOnScreen(records, counter, pg, screen):
    currentRecordID = records[counter][0]

    fullPath = ("{}{}.jpg".format(path, currentRecordID))

    image = pg.image.load(fullPath)

    if image.get_width() != 240 or image.get_height() != 240:
        image = pg.transform.scale(image, (240, 240))

    screen.blit(image, (40, 0))

##################################################
#################Main Application#################
##################################################
def main():

    #Log startup
    logLaunch()

    global pi
    
    pi = pigpio.pi()                
    pi.write(DISP_BL, 1)
    pi.set_mode(Enc_DT, pigpio.INPUT)
    pi.set_mode(Enc_CLK, pigpio.INPUT)
    pi.set_mode(Enc_SW, pigpio.INPUT)
    pi.set_glitch_filter(Enc_SW, 1000)
    pi.callback(Enc_DT, pigpio.EITHER_EDGE, rotary_interrupt)
    pi.callback(Enc_CLK, pigpio.EITHER_EDGE, rotary_interrupt)
    pi.callback(Enc_SW, pigpio.FALLING_EDGE, rotary_switch_interrupt)
    
    config = ConfigParser()
    
    config.read("config.ini")
    logger.debug("Loaded config")

    preferencesConfig = config["PREFERENCES"]

    #Check if last.fm connection is valid
    lastfmConfig = config["LASTFM"]
    global lastfm
    lastfm = Lastfm(
        lastfmConfig["KEY"],
        lastfmConfig["SECRET"],
        lastfmConfig["USERNAME"],
        lastfmConfig["PASSWORD_HASH"],
        logger
    )
    
    lastfm.connect()

    discogsConfig = config["DISCOGS"]
    global discogs
    discogs = Discogs(
        discogsConfig["TOKEN"],
        discogsConfig["USERNAME"],
        DATA_DIR_NAME,
        IMAGE_DIR_NAME,
        COLLECTION_FILE_NAME,
        PROGRAM_NAME,
        VERSION,
        lastfm,
        int(preferencesConfig["DEFAULT_TRACK_DURATION"]),
        logger)

    pg.init()
    pg.mouse.set_visible(False)
    screen = pg.display.set_mode(WINSIZE)
    resetScreen(screen)

    try:
        discogs.connect()
        discogsLibrary = discogs.getLibrary()
    except DiscogsLibraryError as e:
        logger.debug(e)
        try:
            discogs.createLibraryDir()
            discogs.connect()
            startSyncing("Full", screen)
            discogsLibrary = discogs.getLibrary()
        except (DiscogsConnectError, DiscogsCredentialError) as e:
            logger.error(e)
            quit()
   

    #Start in the middle of the library
    numOfRecords = len(discogsLibrary) - 1
    counter = int(numOfRecords / 2)
    
    #Sort records by title then artist
    titleSortedRecords = sorted(discogsLibrary.items(), key=lambda items: items[1]['title'])
    sortedRecords = sorted(titleSortedRecords, key=lambda items: items[1]['artist'])

    showRecordsOnScreen(sortedRecords, counter, pg, screen)
    
    pg.display.update()

    global scrobbleThread

    while True:
        for event in pg.event.get():
            if event.type == QUIT:
                pg.quit()
                sys.exit()
            elif event.type == ROTARY_UP or event.type == ROTARY_DOWN:
                if event.type == ROTARY_UP: 
                    counter += 1
                    if counter > numOfRecords:
                        counter = 0
                else:
                    counter -= 1
                    if counter < 0:
                        counter = numOfRecords
                logger.debug("Count: {}".format(counter))
                showRecordsOnScreen(sortedRecords, counter, pg, screen)
            elif event.type == ROTARY_SHORT:
                logger.debug("Short press")
                currentRecordID = sortedRecords[counter][0]
                showRecord(discogsLibrary[currentRecordID], currentRecordID, pg, screen)
                resetScreen(screen)
                showRecordsOnScreen(sortedRecords, counter, pg, screen)
            elif event.type == ROTARY_LONG:
                logger.debug("Long press")
                showSettingsMenu(screen)
                if discogs.changed:
                    discogsLibrary = discogs.getLibrary()
                    numOfRecords = len(discogsLibrary) - 1
                    #Start in the middle of the library
                    counter = int(numOfRecords / 2)
                    
                    #Sort records by title then artist
                    titleSortedRecords = sorted(discogsLibrary.items(), key=lambda items: items[1]['title'])
                    sortedRecords = sorted(titleSortedRecords, key=lambda items: items[1]['artist'])
                    discogs.changed = False
                resetScreen(screen)
                showRecordsOnScreen(sortedRecords, counter, pg, screen)
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

