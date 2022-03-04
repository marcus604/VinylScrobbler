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

ROTARY_UP_event = pg.event.Event(ROTARY_UP)
ROTARY_DOWN_event = pg.event.Event(ROTARY_DOWN)
ROTARY_SHORT_event = pg.event.Event(ROTARY_SHORT)
ROTARY_LONG_event = pg.event.Event(ROTARY_LONG)

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
                

def showSettingsMenu(screen):

    theme = pygame_menu.themes.THEME_DARK.copy()
    theme.title_bar_style = pygame_menu.widgets.MENUBAR_STYLE_SIMPLE
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

    #Settings Menu
    menu = pygame_menu.Menu(
        'Settings', 320, 240,
        theme=theme,
        mouse_enabled=False,
        mouse_visible=False,
        onclose=pygame_menu.events.CLOSE,
        )  

    menu.add.button('Update', discogs.partialLibraryUpdate)
    menu.add.button('Reset & Sync', discogs.reset)
    menu.add.button('Back', pygame_menu.events.CLOSE) 

    menu.mainloop(screen)

def resetScreen(screen):
    black = 20, 20, 40
    screen.fill(black)

def getNumberOfSides(record):
    tracks = record['tracks']
    numOfSides = 2
    lastTrack = tracks[-1]
    position = lastTrack['position']
    if "J" in position:
        numOfSides = 10
    elif "H" in position:
        numOfSides = 8
    elif "F" in position:
        numOfSides = 6
    elif "D" in position:
        numOfSides = 4

    return numOfSides

#Based on given album title length return an appropriate font size
def getMenuFontSize(title):
    length = len(title)

def startScrobbling(record):
    name = record['title']
    artist = record['artist']
    tracks = record['tracks']

    logger.info("Scrobbling record: {} - {}".format(artist, name))
    scrobbleThread = threading.Thread(target=scrobbleRecord, args=[record])
    logger.debug("Starting new thread")
    scrobbleThread.start()
    
        

def scrobbleRecord(record):
    artist = record['artist']
    album = record['title']
    tracks = record['tracks']

    for track in tracks:
        trackTitle = track['title']
        logger.info("Scrobbling track: {} - {} - {}".format(artist, album, trackTitle))
        duration = track['duration']
        lastfm.updateNowPlaying(artist, album, trackTitle)
        time.sleep(duration / 2)
        currentTime = int(time.time())
        lastfm.scrobble(artist, album, trackTitle, currentTime)
        time.sleep(duration / 2)
        



def showRecord(record, pg, screen):
    logger.debug("Record ID: {}".format(record))
    name = record['title']
    artist = record['artist']
    numOfSides = getNumberOfSides(record)
   
    theme = pygame_menu.themes.THEME_DARK.copy()
    theme.widget_font_size = 20
    theme.title = False
    theme.widget_selection_effect = pygame_menu.widgets.SimpleSelection()
    theme.widget_selection_color = (255, 0, 0)
    
    
    
    menu = pygame_menu.Menu(
        title=False,
        width=320, 
        height=240,
        theme=theme,
        mouse_enabled=False,
        mouse_visible=False,
        onclose=pygame_menu.events.CLOSE,
        )  

    
    menu.add.label(artist, align=pygame_menu.locals.ALIGN_LEFT)
    menu.add.label(name, align=pygame_menu.locals.ALIGN_LEFT)

    menu.add.button("Scrobble", startScrobbling, record, align=pygame_menu.locals.ALIGN_CENTER)
    #for side in range(numOfSides):
    #    sideString = "Side {}".format(side + 1)
    #    menu.add.button(sideString, lastfm.scrobbleSide, record, side + 1, align=pygame_menu.locals.ALIGN_CENTER)
   
    menu.add.button('Back', pygame_menu.events.CLOSE) 

    menu.mainloop(screen)

def showRecordsOnScreen(records, counter, pg, screen):
    currentRecordID = records[counter][0]

    fullPath = ("{}{}.jpg".format(path, currentRecordID))

    image = pg.image.load(fullPath)

    screen.blit(image, (40, 0))

##################################################
#################Main Application#################
##################################################
def main():

    #Log startup
    logLaunch()
    
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

    
    try:
        discogs.connect()
        discogsLibrary = discogs.getLibrary()
    except DiscogsLibraryError as e:
        logger.debug(e)
        try:
            discogs.createLibraryDir()
            discogs.connect()
            #Show something on screen, 221 records took 6 minutes
            discogs.fullLibraryUpdate()
            discogsLibrary = discogs.getLibrary()
        except (DiscogsConnectError, DiscogsCredentialError) as e:
            logger.error(e)
            quit()
   
    

    
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
    resetScreen(screen)

    numOfRecords = len(discogsLibrary) - 1
    #Start in the middle of the library
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
                logger.debug("Short press PG")
                currentRecordID = sortedRecords[counter][0]
                showRecord(discogsLibrary[currentRecordID], pg, screen)
                resetScreen(screen)
                showRecordsOnScreen(sortedRecords, counter, pg, screen)
            elif event.type == ROTARY_LONG:
                logger.debug("long press PG")
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

