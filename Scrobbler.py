import time
import urllib
import urllib2
import md5

from RSConfig import xor_crypt_string

class Scrobbler:
    username = None
    password = None
    clientID = None
    sessionID = None
    nowPlayingURL = None
    submissionURL = None

    def __init__(self, username, password, clientID = "tst"):
        # unfortunate, but necessary
        self.username = username
        self.password = xor_crypt_string(password)
        self.clientID = clientID
    
    # logs into last.fm
    def handshake(self):
        ts = int(time.time())
        token = md5.new(md5.new(xor_crypt_string(self.password)).hexdigest() + str(ts)).hexdigest()

        params = {
            'hs' : 'true',
            'p' : '1.2',
            'c' : self.clientID,
            'v' : '1.0',
            'u' : self.username,
            't' : ts,
            'a' : token
        }
            
        response = urllib2.urlopen('http://post.audioscrobbler.com/?'+ urllib.urlencode(params)).read()

        stuff = response.split('\n')

        if stuff[0] != "OK":
            raise ScrobblerException(stuff[0])

        else:
            self.sessionID = stuff[1]
            self.nowPlayingURL = stuff[2]
            self.submissionURL = stuff[3]
            
    # submits tracks to last.fm
    def submit(self, artist, track, startTime, source = 'P', rating = None, trackLength = None, album = None, trackNumber = None, mbTrackID = None, rep = False):

        if self.sessionID == None:
            self.handshake()

        params = {
            's' : self.sessionID,
            'a[0]' : artist,
            't[0]' : track,
            'i[0]' : startTime,
            'o[0]' : source,
            'r[0]' : 'L',
            'l[0]' : '',
            'b[0]' : '',
            'n[0]' : '',
            'm[0]' : ''
        }
            
        if rating      != None: params['r[0]'] = rating
        if trackLength != None: params['l[0]'] = trackLength
        if album       != None: params['b[0]'] = album
        if trackNumber != None: params['n[0]'] = trackNumber
        if mbTrackID   != None: params['m[0]'] = mbTrackID
        
        params = 's=%s&a[0]=%s&t[0]=%s&i[0]=%d&o[0]=P&r[0]=L&l[0]=%d&b[0]=%s&n[0]=&m[0]=' % (self.sessionID, artist, track, startTime, trackLength, album)
        
        req = urllib2.Request(url=self.submissionURL, data=params, headers={ "Content-Type": "application/x-www-form-urlencoded" })
        response = urllib2.urlopen(req).read()
        stuff = response.split('\n')

        if stuff[0] == "BADSESSION" and rep == False:
            self.handshake(self.username, self.password)
            self.submit(artist, track, startTime, source, rating, trackLength, album, trackNumber, mbTrackID, rep = True)

        elif stuff[0] != "OK":
            raise ScrobblerException(stuff[0])
            

class ScrobblerException(Exception):
    response = None
    message = None
    
    def __init__(self, value):
        if value.startswith("BADAUTH"):
            self.response = "BADAUTH"
            self.message = "Invalid Username or Password"
        elif value.startswith("BANNED"):
            self.response = "BANNED"
            self.message = "Client is banned"
        elif value.startswith("FAILED"):
            self.response = "FAILED"
            self.message = value[7:]
        else:
            self.response = "UNKNOWN"
            self.message = value
    
    def getResponse(self):
        return self.response
        
    def getMessage(self):
        return self.message
    
    def __str__(self):
        return self.response + ": " + repr(self.message)