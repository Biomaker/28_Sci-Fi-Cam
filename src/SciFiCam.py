import os
import sys
from time import sleep

import numpy as np
from PIL import Image

from picamera import PiCamera
import owncloud

from ButtonThread import ButtonThread
from OwnCloudThread import OwnCloudThread

from Mode import CaptureMode
from Stencil import Stencil

class SciFiCam(object):
	def __init__(self):
		# Setting directories
		self.dir				= os.getenv('SCI_PI_CAM_DIR', '/home/pi/sci-fi-cam/')
		self.settingsFile		= os.path.join(self.dir, "settings.py")
		self.picDir				= os.path.join(self.dir, "pics")

		if not os.path.isdir(self.picDir):
			os.makedirs(self.picDir)

		setfile 				= open(self.settingsFile, 'a')
		setfile.close()

		# Setting camera
		self.camera				= PiCamera()
		self.camera.resolution	= (1280, 720)
		self.camera.rotation	= 90
		self.renderer			= self.camera.start_preview()
		self.camera.preview.alpha = 128
		self.blank				= np.ones((720, 1280, 3), dtype=np.uint8) * 255

		# Setting button thread
		self.nButtons			= 5
		self.buttonThread		= ButtonThread()
		self.buttonThread.setCallback(0, self.capture)
		self.buttonThread.setCallback(1, self.capture)
		self.buttonThread.setCallback(2, self.capture)
		self.buttonThread.setCallback(3, self.capture)
		self.buttonThread.setCallback(4, self.capture)
		self.buttonThread.start()
		print "Setting up OwnCloud"
		# Setting owncloud thread
		ocAddress			= self._getSetting("ocAddress")
		ocLogin				= self._getSetting("ocLogin")
		ocPass				= self._getSetting("ocPass")
		
		try:
			self.ocThread = OwnCloudThread(ocAddress, ocLogin, ocPass, self.picDir)
			self.ocThread.start()
		except Exception as e:
			self._issueWaring("Could not initialise OwnCloud: {0}".format(sys.exc_info()[1]) )
		captureMode = CaptureMode(self)

		self._setMode(captureMode)
		self.camera._set_exposure_mode('nightpreview')
		
	def _issueWaring(self, message):
		print "SciFiCam Warning: {0}".format(message)

	def _setMode(self, mode):
		for i in range(self.nButtons):
			self.buttonThread.setCallback(i, mode.buttonFunction[i])
		
		self.currentMode = mode
		self._refreshOverlay()

	def _refreshOverlay(self):
		overlay = np.zeros((720, 1280, 3), dtype=np.uint8)

		for stencil in self.currentMode.stencils:
			overlay = stencil.draw(overlay)
	
		self.camera.add_overlay(np.getbuffer(overlay), alpha = 255, layer = 1)

	def close(self):
		self.buttonThread._stop_event.set()

	def _getSetting(self, name):
		settings= {}
		execfile( self.settingsFile, settings )
		
		if name in settings:
			return settings[name]
		else:
			self._setSetting(name, None)
			return None

	def _setSetting(self, name, val):
		settings= {}
		execfile( self.settingsFile, settings )
		
		settings[name] = val

		settingFile = open(self.settingsFile, 'w')
		for key, val in settings.iteritems():
			if key != "__builtins__":
				settingFile.write("{0}='{1}'\n\n".format(key, val))
		settingFile.close()

	def _getNewFileName(self):
		counter = int( self._getSetting("counter") )
		
		if not counter:
			counter = 0

		self._setSetting("counter", counter+1)

		return os.path.join( self.dir, "pics", "{0}.jpg".format(counter) )

	def capture(self):
		print "Click"

		# Drawing flash effect
		o = self.camera.add_overlay(np.getbuffer(self.blank), alpha = 255, layer = 5)
		sleep(0.2)
		self.camera.remove_overlay(o)

		# Capturing to file
		fileName = self._getNewFileName()
		print "Saving to ", fileName
		self.camera.capture(fileName)
		
		# Holding captured image
		image = Image.open(fileName)
		o = self.camera.add_overlay(image.tostring(), size = image.size, alpha = 255, layer = 3)
		sleep(1)
		self.camera.remove_overlay(o)

if __name__ == "__main__":
	camera = SciFiCam()
	try:
		while True:
			sleep(1)
	finally:
		camera.close()
		sys.exit()