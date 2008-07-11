# setup.py

import glob
import os
import sys
from distutils.core import setup
import py2exe

setup(name="RhapScrobbler",
	windows=[{
		"script":"rhapscrobbler.py",
		"icon_resources":[(1,"icon.ico")]
	}],
)
