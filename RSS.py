import urllib
from xml.dom import minidom

import time
import datetime
import re
import random
import rfc822

def getItems(url, sinceTime = None):
    items = []

    dom = minidom.parse(urllib.urlopen(url))

    for itemNode in dom.documentElement.getElementsByTagName("item"):
        item = dict()

        # parse all the RSS items into a dictionary
        for childNode in itemNode.childNodes:
            if childNode.nodeName == "pubDate":
                item["pubDate"] = int(rfc822.mktime_tz(rfc822.parsedate_tz(childNode.firstChild.nodeValue)))
                        
            elif childNode.nodeType == minidom.Node.ELEMENT_NODE:
                item[childNode.nodeName] = childNode.firstChild.nodeValue

        # filter out any items older than sinceTime if not null
        if sinceTime == None or item["pubDate"] > sinceTime:
            items.append(item)

    return items
