import wx
import sys
import time
import urllib
import cStringIO
import os
import threading

import Scrobbler
import Rhapsody
import RSConfig

from RSConfig import xor_crypt_string


ID_TIMER = 1029
ID_WXSTATICTEXT2 = 1028
ID_WXSTATICTEXT1 = 1027
ID_WXSTYLEDTEXTCTRL1 = 1024
ID_WXBUTTON3 = 1023
ID_WXBUTTON2 = 1022
ID_WXBUTTON1 = 1021
ID_WXPANEL1 = 1020

WX_STAY_ON_TOP = 0x8000

RHAPSODY_PATH = 'c:\\Program Files\\Rhapsody\\rhapsody.exe'

class MainFrame(wx.Frame):
    albumArt = None
    songTrack = None
    songArtist = None
    songAlbum = None
    lastSongSizer1 = None
    lastSongSizer2 = None
    mainPanel = None
    mainSizer = None
    tbIcon = None
    trackTimer = None
    lastTimestamp = None
    rhapsody = None
    scrobbler = None
    lock = None
    syncthread = None
    
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, -1, title, size=wx.Size(400,225), style = wx.DEFAULT_FRAME_STYLE | WX_STAY_ON_TOP)

        self.mainPanel = wx.Panel(self, ID_WXPANEL1, wx.Point(0,0), wx.Size(400,225))
        self.mainSizer = wx.BoxSizer(wx.VERTICAL);
        self.SetSizer(self.mainSizer);
        self.SetAutoLayout(True);

        self.lastSongSizer1 = wx.BoxSizer(wx.HORIZONTAL)
        self.lastSongSizer2 = wx.BoxSizer(wx.VERTICAL)

        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.albumArt = wx.StaticBitmap(self, wx.ID_ANY, wx.NullBitmap, size = wx.Size(96,96))
        
        self.songTrack = wx.StaticText(self.mainPanel, wx.ID_ANY, "Track");
        self.songTrack.Disable()

        self.songArtist = wx.StaticText(self.mainPanel, wx.ID_ANY, "Artist");
        self.songArtist.Disable()

        self.songAlbum = wx.StaticText(self.mainPanel, wx.ID_ANY, "Album");
        self.songAlbum.Disable()

        titleText = wx.StaticText(self.mainPanel, ID_WXSTATICTEXT1, "RhapScrobbler", wx.Point(147,3), wx.DefaultSize, 0, "WxStaticText1");
        titleText.SetFont(wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL,wx.FONTWEIGHT_NORMAL, False, "Tahoma"));

        hideButton = wx.Button(self.mainPanel, ID_WXBUTTON1, "Hide", wx.Point(131,20), wx.Size(75,25), 0, wx.DefaultValidator, "WxButton1");
        hideButton.Bind(wx.EVT_BUTTON, self.onHide)

        configButton = wx.Button(self.mainPanel, ID_WXBUTTON2, "Configure", wx.Point(143,55), wx.Size(75,25), 0, wx.DefaultValidator, "WxButton2");
        configButton.Bind(wx.EVT_BUTTON, self.btnConfig)

        quitButton = wx.Button(self.mainPanel, ID_WXBUTTON3, "Quit", wx.Point(143,90), wx.Size(75,25), 0, wx.DefaultValidator, "WxButton3");
        quitButton.Bind(wx.EVT_BUTTON, self.btnQuit)

        self.lastSongSizer1.Add(self.albumArt,0,wx.ALIGN_CENTER | wx.ALL,5)
        self.lastSongSizer2.Add(self.songTrack,0,wx.ALL,2)
        self.lastSongSizer2.Add(self.songArtist,0,wx.ALL,2)
        self.lastSongSizer2.Add(self.songAlbum,0,wx.ALL,2)
        self.lastSongSizer1.Add(self.lastSongSizer2,0,wx.ALIGN_TOP | wx.ALL,5)

        buttonSizer.Add(hideButton,0,wx.ALIGN_CENTER | wx.ALL,5);
        buttonSizer.Add(configButton,0,wx.ALIGN_CENTER | wx.ALL,5);
        buttonSizer.Add(quitButton,0,wx.ALIGN_CENTER | wx.ALL,5);

        self.mainSizer.Add(titleText,0,wx.ALIGN_CENTER | wx.ALL,5);
        self.mainSizer.Add(self.lastSongSizer1,0,wx.ALL,5);
        self.mainSizer.Add(buttonSizer,0,wx.ALIGN_CENTER | wx.ALL,5);

        self.SetTitle("RhapScrobbler");
        self.SetIcon(wx.NullIcon);

        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.Bind(wx.EVT_ICONIZE, self.onHide)
        
        self.GetSizer().Layout();
        self.Center();

        wx.InitAllImageHandlers()

        self.tbIcon = wx.TaskBarIcon()

        if sys.argv[0].endswith(".exe"):
            self.tbIcon.SetIcon(wx.Icon(sys.argv[0], wx.BITMAP_TYPE_ICO), "lawl")
        else:
            self.tbIcon.SetIcon(wx.Icon("icon.ico", wx.BITMAP_TYPE_ICO), "lawl")

        self.tbIcon.Bind(wx.EVT_TASKBAR_LEFT_UP, self.toggleWindow)
        
        self.lock = threading.RLock()

        self.initialize(False)

        self.Show(True)

    def initialize(self, reinitialize = True):

        config = RSConfig.load()

        if config.has_key("LastFM") and config.has_key("Rhapsody"):
            if config["Rhapsody"].has_key("startrhapsody") and config["Rhapsody"]["startrhapsody"] == "True" and reinitialize == False:
                # TODO: this should probably check the registry instead
                if os.path.exists(RHAPSODY_PATH):
                    os.spawnl(os.P_NOWAIT, RHAPSODY_PATH)


            if config["LastFM"].has_key("username") and config["LastFM"].has_key("password"):
                self.scrobbler = Scrobbler.Scrobbler(config["LastFM"]["username"], xor_crypt_string(config["LastFM"]["password"]))
            
            if config["Rhapsody"].has_key("url"):
                self.rhapsody = Rhapsody.Rhapsody(config["Rhapsody"]["url"])

                try:
                    tracks = self.rhapsody.getTracks()
                    
                    if len(tracks) > 0:
                        self.updateLastTrack(tracks[0]['track'], tracks[0]['artist'], tracks[0]['album'], tracks[0]['albumArt'])
                        
                except:
                    wx.MessageBox("An error occurred while loading tracks from Rhapsody", "Error")


        if self.scrobbler != None and self.rhapsody != None:

            if self.trackTimer != None:
                # remove the old timer
                self.trackTimer.cancel()
                del self.trackTimer
            
            # create/start the rhapsody polling timer
            if config["Rhapsody"].has_key("poll"):
                # using user-specified poll delay
                self.trackTimer = PeriodicThread(float(config["Rhapsody"]["poll"]) / 1000.0, self.syncThread)
            else:
                # default to two-minute poll delay
                self.trackTimer = PeriodicThread(120.0, self.syncThread)

            self.trackTimer.start()
    
    def toggleWindow(self, event):
        if self.IsShown():
            self.Hide()
        else:
            self.Show()
            self.SetFocus()
    
    def onHide(self, event):
        self.Hide()
    
    def onClose(self, event):
        self.trackTimer.cancel()
        self.tbIcon.RemoveIcon()
        self.Destroy()
    
    def btnQuit(self, event):
        self.Close(1)

    def btnConfig(self, event):
        d = ConfigDialog(self, wx.ID_ANY)

        if d.ShowModal() == wx.ID_OK:
            self.initialize()

    def syncThread(self):

        if self.scrobbler != None and self.rhapsody != None:
            try:
                asTracks = self.scrobbler.getTracks()

                if len(asTracks) > 0:
                    rsTracks = self.rhapsody.getTracks(asTracks[0]['timestamp'])
                else:
                    rsTracks = self.rhapsody.getTracks()
            except:
                return

            if len(rsTracks) > 0:
                wx.CallAfter(self.updateLastTrack, rsTracks[0]['track'], rsTracks[0]['artist'], rsTracks[0]['album'], rsTracks[0]['albumArt'])

                for track in reversed(rsTracks):
                    self.scrobbler.submit(artist = track['artist'], track = track['track'], album = track['album'], startTime = track['timestamp'], trackLength = track['duration'])



    def updateLastTrack(self, track, artist, album, albumArt = None):
        img = wx.NullImage

        if albumArt != None:
            try:
                u = urllib.urlopen(albumArt)
                data = u.read()
                u.close()
            
                img = wx.ImageFromStream(cStringIO.StringIO(data), wx.BITMAP_TYPE_JPEG)
                img.Rescale(96,96)

            except:
                img = wx.NullImage
                pass

        albumArt = wx.StaticBitmap(self.mainPanel, wx.ID_ANY, wx.BitmapFromImage(img), size = wx.Size(96,96))
        songTrack = wx.StaticText(self.mainPanel, wx.ID_ANY, track);
        songArtist = wx.StaticText(self.mainPanel, wx.ID_ANY, artist);
        songAlbum = wx.StaticText(self.mainPanel, wx.ID_ANY, album);

        self.lastSongSizer1.Replace(self.albumArt, albumArt)
        self.lastSongSizer2.Replace(self.songTrack, songTrack)
        self.lastSongSizer2.Replace(self.songArtist, songArtist)
        self.lastSongSizer2.Replace(self.songAlbum, songAlbum)
        
        self.songTrack.Destroy()
        self.songArtist.Destroy()
        self.songAlbum.Destroy()
        self.albumArt.Destroy()

        self.songTrack = songTrack
        self.songArtist = songArtist
        self.songAlbum = songAlbum
        self.albumArt = albumArt

        self.GetSizer().Layout()
        

class ConfigDialog(wx.Dialog):
    parent = None
    lastfm = None
    rhapsody = None
    
    def __init__(self, parent, id):
        wx.Dialog.__init__(self, parent, id, "Configure RhapScrobbler", size = wx.Size(300, 400))
        self.parent = parent
        
        notebook = wx.Notebook(self, wx.ID_ANY, wx.Point(0,0), self.GetSize(), style = wx.NO_BORDER)

        config = RSConfig.load()

        # load the last.fm config dialog
        self.lastfm = ConfigDialogLastFM(notebook)

        if config.has_key("LastFM"):
            if config["LastFM"].has_key("username"):
                self.lastfm.userEdit.SetValue(config["LastFM"]["username"])

            if config["LastFM"].has_key("password"):
                # insert stars into the password field (protect against snooping programs)
                self.lastfm.passEdit.SetValue("*" * len(config["LastFM"]["password"]))

        # load the rhapsody config dialog
        self.rhapsody = ConfigDialogRhapsody(notebook)

        if config.has_key("Rhapsody"):
            if config["Rhapsody"].has_key("url"):
                self.rhapsody.feedEdit.SetValue(config["Rhapsody"]["url"])
                
            if config["Rhapsody"].has_key("poll"):
                # convert the poll time from microseconds to minutes
                self.rhapsody.checkEdit.SetValue(str(float(config["Rhapsody"]["poll"]) / 60000))

            if config["Rhapsody"].has_key("startrhapsody"):
                if config["Rhapsody"]["startrhapsody"] == "True":
                    self.rhapsody.startCheckbox.SetValue(True)
                elif config["Rhapsody"]["startrhapsody"] == "False":
                    self.rhapsody.startCheckbox.SetValue(False)

        notebook.AddPage(self.lastfm, "Last.FM")
        notebook.AddPage(self.rhapsody, "Rhapsody")
        
        buttonPanel = wx.Panel(self, style = wx.TAB_TRAVERSAL | wx.ALL)

        okButton = wx.Button(buttonPanel, wx.ID_ANY, "OK");
        okButton.Bind(wx.EVT_BUTTON, self.btnOk)

        cancelButton = wx.Button(buttonPanel, wx.ID_ANY, "Cancel");
        cancelButton.Bind(wx.EVT_BUTTON, self.btnCancel)

        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonSizer.Add(okButton, 0, wx.ALL | wx.ALIGN_CENTER, 10)
        buttonSizer.Add(cancelButton, 0, wx.ALL | wx.ALIGN_CENTER, 10)
        buttonPanel.SetSizer(buttonSizer)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(notebook, 1, wx.EXPAND)
        sizer.Add(buttonPanel, 0, wx.ALIGN_CENTER)

        self.SetSizer(sizer)
        
    def btnOk(self, event):
        valid = True

        config = dict(
            LastFM = dict(
                username = self.lastfm.userEdit.GetValue(),
                password = self.lastfm.passEdit.GetValue()
            ),

            Rhapsody = dict(
                url = self.rhapsody.feedEdit.GetValue(),
                poll = str(float(self.rhapsody.checkEdit.GetValue()) * 60000),
                startrhapsody = str(self.rhapsody.startCheckbox.GetValue())
            )
        )

        # they didn't change the password field so unset it
        if config["LastFM"]["password"] == "*" * len(config["LastFM"]["password"]):
            del config["LastFM"]["password"]

        # make sure their last.fm username / password is correct
        # (take their word for it if they didn't change the password field)
        if config["LastFM"].has_key("password"):
            scrobbler = Scrobbler.Scrobbler(config["LastFM"]["username"], config["LastFM"]["password"])

            try:
                scrobbler.handshake()
            except Scrobbler.ScrobblerException, e:
                wx.MessageBox(str(e), "Last.FM Error")
                valid = False

        # make sure they specified a good rhapsody url
        if config["Rhapsody"]["url"] == "":
            valid = False
        else:
            try:
                rhapsody = Rhapsody.Rhapsody(config["Rhapsody"]["url"])
                rhapsody.getTracks()
            except:
                wx.MessageBox("Bad Rhapsody URL specified", "Rhapsody Error")
                valid = False

        # if valid, save the config file
        if valid:
            if config["LastFM"].has_key("password"):
                config["LastFM"]["password"] = xor_crypt_string(config["LastFM"]["password"])

            RSConfig.save(config)
            self.EndModal(wx.ID_OK)

    def btnCancel(self, event):
        self.EndModal(wx.ID_CANCEL)


class ConfigDialogLastFM(wx.Panel):
    userEdit = None
    passEdit = None

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        
        label = wx.StaticText(self, wx.ID_ANY, "Please enter your Last.FM Username and Password", wx.Point(15,16), wx.DefaultSize)

        userLabel = wx.StaticText(self, wx.ID_ANY, "Username", wx.Point(15,55), wx.DefaultSize)
        passLabel = wx.StaticText(self, wx.ID_ANY, "Password", wx.Point(14,82), wx.DefaultSize)
        
        self.userEdit = wx.TextCtrl(self, wx.ID_ANY, "", wx.Point(74,53), wx.Size(190,19))
        self.passEdit = wx.TextCtrl(self, wx.ID_ANY, "", wx.Point(74,79), wx.Size(190,19), wx.TE_PASSWORD)


class ConfigDialogRhapsody(wx.Panel):
    feedEdit = None
    checkEdit = None
    startCheckbox = None
    
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        feedLabel = wx.StaticText(self, wx.ID_ANY, "Rhapsody URL", wx.Point(8,29))

        self.feedEdit = wx.TextCtrl(self, wx.ID_ANY, "", wx.Point(84,27), wx.Size(190,19))

        feedLabel2 = wx.StaticText(self, wx.ID_ANY, "Paste your ", wx.Point(15, 52))
        feedLabel2.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_INFOBK));
        feedLabel3 = wx.HyperlinkCtrl(self, wx.ID_ANY, "Recently Played Tracks", "http://www.rhapsody.com/myrhapsody/feeds.html", wx.Point(70,52))
        feedLabel3.SetNormalColour(wx.BLUE);
        feedLabel3.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_INFOBK));
        feedLabel4 = wx.StaticText(self, wx.ID_ANY, " RSS feed above.", wx.Point(181, 52))
        feedLabel4.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_INFOBK));

        checkLabel = wx.StaticText(self, wx.ID_ANY, "Check Rhapsody every", wx.Point(8,92))
        self.checkEdit = wx.TextCtrl(self, wx.ID_ANY, "2.0", wx.Point(123,90), wx.Size(62,19))
        checkLabel2 = wx.StaticText(self, wx.ID_ANY, "minutes", wx.Point(188,92))

        self.startCheckbox = wx.CheckBox(self, wx.ID_ANY, "Start Rhapsody when starting RhapScrobbler", wx.Point(10,134), wx.Size(250,17))


class MainApp(wx.App):
    def OnInit(self):
        frame = MainFrame(None, -1, "RhapScrobbler")
        frame.Show(True)
        
        if sys.argv[0].endswith(".exe"):
            frame.SetIcon(wx.Icon(sys.argv[0], wx.BITMAP_TYPE_ICO))
        else:
            frame.SetIcon(wx.Icon("icon.ico", wx.BITMAP_TYPE_ICO))

        self.SetTopWindow(frame)
        return 1

class PeriodicThread(threading.Thread):

    def __init__(self, interval, function, args=[], kwargs={}):
        threading.Thread.__init__(self)
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.finished = threading.Event()

    def cancel(self):
        self.finished.set()

    def run(self):
        while not self.finished.isSet():
            self.function(*self.args, **self.kwargs)
            self.finished.wait(self.interval)


MainApp(0).MainLoop()
