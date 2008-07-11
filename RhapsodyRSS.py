import urllib
from xml.dom import minidom

import time
import datetime
import re
import random
import rfc822

class RhapsodyRSS:
    feedURL = None
    
    def __init__(self, feedURL):
        self.feedURL = feedURL
        
    def getTracks(self, sinceTime = None):
        u = urllib.urlopen(self.feedURL + "&r=" + str(random.uniform(0,100000)))
        dom = minidom.parse(u)

        tracks = []

        for itemNode in dom.documentElement.getElementsByTagName("item"):
            timestamp = int(rfc822.mktime_tz(rfc822.parsedate_tz(getChildContent(itemNode, "pubDate"))))

            if sinceTime == None or timestamp > sinceTime:
                tracks.append({
                    'artist'    : getChildContent(itemNode, "rhap:artist"),
                    'album'     : getChildContent(itemNode, "rhap:album"),
                    'track'     : getChildContent(itemNode, "rhap:track"),
                    'duration'  : int(getChildContent(itemNode, "rhap:duration")),
                    'albumArt'  : getChildContent(itemNode, "rhap:album-art"),
                    'timestamp' : timestamp
                })
            
        return tracks

def getChildContent(parent, tagName, altValue = ""):
    nodes = parent.getElementsByTagName(tagName)
    
    if len(nodes) > 0:
        if nodes[0].firstChild != None:
            return nodes[0].firstChild.nodeValue
    
    return altValue