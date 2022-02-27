from configparser import ConfigParser
from lastfm import hashPassword

config = ConfigParser()

def writeConfig(config):
    with open(CONFIG_FILE_NAME, "w") as configFile:
        config.write(configFile)

CONFIG_FILE_NAME = "config.ini"
config.read(CONFIG_FILE_NAME)


discogsConfig = config["DISCOGS"]
lastfmConfig = config["LASTFM"]

while discogsConfig["TOKEN"] == "":
    token = input("Enter your discogs token: ")
    config.set("DISCOGS", "TOKEN", token)
    writeConfig(config)

while discogsConfig["USERNAME"] == "":
    username = input("Enter your discogs username: ")
    config.set("DISCOGS", "USERNAME", username)
    writeConfig(config)

while lastfmConfig["KEY"] == "":
    key = input("Enter your last.fm key: ")
    config.set("LASTFM", "KEY", key)
    writeConfig(config)

while lastfmConfig["SECRET"] == "":
    secret = input("Enter your last.fm secret: ")
    config.set("LASTFM", "SECRET", secret)
    writeConfig(config)

while lastfmConfig["USERNAME"] == "":
    username = input("Enter your last.fm username: ")
    config.set("LASTFM", "USERNAME", username)
    writeConfig(config)

while lastfmConfig["PASSWORD_HASH"] == "":
    password = input("Enter your last.fm password (Password is stored hashed): ")
    password_hash = hashPassword(password)
    config.set("LASTFM", "PASSWORD_HASH", password_hash)
    writeConfig(config)




