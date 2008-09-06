import RSS
import random

class Rhapsody:
    feedURL = None
    
    def __init__(self, feedURL):
        self.feedURL = feedURL
        
    def getTracks(self, sinceTime = None):
        tracks = []
        
        # grab the tracks from the RSS feed and filter out the things we're not interested in
        items = RSS.getItems(self.feedURL + "&r=" + str(random.uniform(0,100000)), sinceTime)

        for item in items:
            tracks.append({
                'artist'    : item['rhap:artist'],
                'album'     : item['rhap:album'],
                'track'     : item['rhap:track'],
                'duration'  : int(item['rhap:duration']),
                'albumArt'  : item['rhap:album-art'],
                'timestamp' : item['pubDate']
            })
           
        return tracks
