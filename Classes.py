

class Album:
    
    def __init__(self, title, artist, tracks, artwork):
        #Config
        self.title = title
        self.artist = artist
        self.tracks = tracks
        self.artwork = artwork

    def __str__(self):
        return "{} - {}".format(self.artist, self.title)

    
    

class Track:

    def __init__(self, title, position, duration):
        self.title = title
        self.position = position
        self.duration = duration
        

class Class_Exception(Exception):
    pass







