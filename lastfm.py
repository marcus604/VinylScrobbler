import pylast

class Lastfm:

    def __init__(self, key, secret, username, passwordHash, logger):
        self.key = key
        self.secret = secret
        self.username = username
        self.passwordHash = passwordHash
        self.logger = logger

        self.network = ""
        
    def connect(self):
        self.network = pylast.LastFMNetwork(
            api_key=self.key,
            api_secret=self.secret,
            username=self.username,
            password_hash=self.passwordHash,
        )

    def getTrackDuration(self, artist, track):
        try:
            track = self.network.get_track(artist, track)
            duration = track.get_duration()
        except:
            self.logger.info("Lastfm could not find track duration: {} - {}".format(artish, track))
            return 0
        return duration / 1000
    
    def scrobble(self):
        self.logger.info("Scrobbling track")

def hashPassword(password):
    return pylast.md5(password)



