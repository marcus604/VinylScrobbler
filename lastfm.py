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
            self.logger.debug("Lastfm could not find track duration: {} - {}".format(artist, track))
            return 0
        return duration / 1000
    
    def updateNowPlaying(self, artist, album, trackTitle):
        self.network.update_now_playing(
            artist=artist,
            album=album,
            title=trackTitle
        )
        

    def scrobble(self, artist, album, trackTitle, timestamp):
        self.network.scrobble(
            artist=artist,
            album=album,
            title=trackTitle,
            timestamp=timestamp
        )

    

def hashPassword(password):
    return pylast.md5(password)



