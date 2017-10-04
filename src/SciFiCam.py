import os
import sys
from time import sleep

import numpy as np
from PIL import Image

from picamera import PiCamera
import owncloud

from ButtonThread import ButtonThread
from OwnCloudThread import OwnCloudThread

from Mode2 import *
# from Stencil import *
# from Properties import *

class SciFiCam(object):
	def __init__(self):
		# Setting directories
		self.dir				= os.getenv('SCI_PI_CAM_DIR', '/home/pi/SciFiCam/')
		self.settingsFile		= os.path.join(self.dir, "settings.py")
		self.picDir				= os.path.join(self.dir, "pics")

		if not os.path.isdir(self.picDir):
			os.makedirs(self.picDir)

		setfile 				= open(self.settingsFile, 'a')
		setfile.close()
		
		#self.cameraResolution = (1280, 720)
		self.cameraResolution = (640, 480)
		self.overlaySize 	  = ( self.cameraResolution[1], self.cameraResolution[0],3 )
		# Setting camera
		self.camera				= PiCamera()
		self.camera.resolution	= self.cameraResolution
		self.camera.rotation	= 90
		self.blank				= np.ones(self.overlaySize, dtype=np.uint8) * 255
		self.UIOverlay			= self.camera.add_overlay(np.getbuffer(np.zeros( self.overlaySize, dtype=np.uint8)), format = 'rgb', alpha = 255, layer = 1)
		
		# Setting button thread
		self.nButtons			= 5
		self.buttonThread		= ButtonThread()
		self.buttonThread.setCallback(0, self.capture)
		self.buttonThread.setCallback(1, self.capture)
		self.buttonThread.setCallback(2, self.capture)
		self.buttonThread.setCallback(3, self.capture)
		self.buttonThread.setCallback(4, self.capture)
		
		print "Setting up OwnCloud"
		# Setting owncloud thread
		self.ocAddress			= self._getSetting("ocAddress")
		self.ocLogin				= self._getSetting("ocLogin")
		self.ocPass				= self._getSetting("ocPass")
		
		self.modes = []
		self.currentMode = None
		
	def _issueWaring(self, message):
		print "SciFiCam Warning: {0}".format(message)

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


	# def _setMode(self, mode):
	# 	for i in range(self.nButtons):
	# 		self.buttonThread.setCallback(i, mode.buttonFunction[i])
		
	# 	self.currentMode = mode
	# 	self._refreshOverlay()

	# def _refreshOverlay(self):
	# 	overlay = np.zeros((720, 1280, 3), dtype=np.uint8)

	# 	for stencil in self.currentMode.stencils:
	# 		overlay = stencil.draw(overlay)
	# 	self.camera.remove_overlay( self.UIOverlay )
	# 	self.UIOverlay = self.camera.add_overlay(np.getbuffer(overlay), alpha = 255, layer = 1)
	
	def start(self):
		self.buttonThread.start()
		
		try:
			self.ocThread = OwnCloudThread(self.ocAddress, self.ocLogin, self.ocPass, self.picDir)
			self.ocThread.start()
		except Exception as e:
			self.ocThread = None
			self._issueWaring("Could not initialise OwnCloud: {0}".format(sys.exc_info()[1]) )

		self.renderer = self.camera.start_preview()
		self.camera.preview.alpha = 128
		
		if len(self.modes) > 0:
			self.setMode( 0 )


	def addMode(self, mode):
		self.modes.append(mode)

	def setMode(self, idx):
		print "Setting MODE ", idx
		print self.modes
		if idx >= 0 and idx < len(self.modes):
			self.currentMode = self.modes[idx](self)
			print "Set MODE, trying to INIT", idx
			# self.currentMode.init()
			print "Done"
			self.update()
	
	def update(self):
		overlay = np.zeros( self.overlaySize, dtype=np.uint8)
		print overlay.shape
		for UIElement in self.currentMode.UISetters + self.currentMode.UIGetters + self.currentMode.UIStatic:
			overlay = UIElement.update(overlay)

		self.camera.remove_overlay(self.UIOverlay)
		self.UIOverlay = self.camera.add_overlay( np.getbuffer(overlay), format = 'rgb', alpha = 255, layer = 1 )

	def setNextMode(self):
		if len(self.modes) > 0:
			index = 0
			if self.currentMode.__class__ in self.modes:
				index = self.modes.index(self.currentMode.__class__) + 1
				if index == len(self.modes):
					index = 0
			self.setMode(index)

	def stop(self):
		self.buttonThread._stop_event.set()
		self.ocThread._stop_event.set()
		self.camera.stop_preview()

	def foo(self):
		print "FOO"

	def restart(self):
		print "Restarting..."
		self.stop()
		command = "/usr/bin/sudo /sbin/shutdown -r now"
		import subprocess
		process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
		output = process.communicate()[0]
		print output

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
	
	def changeBrightness(self, delta):
		if self.camera.brightness + delta > 100:
			self.camera.brightness = 100
		elif self.camera.brightness + delta < 0:
			self.camera.brightness = 0
		else:
			self.camera.brightness = self.camera.brightness + delta

if __name__ == "__main__":
	camera = SciFiCam()
	camera.addMode(AutoMode)
	camera.addMode(ManualMode)
	camera.start()
	try:
		while True:
			sleep(1)
	finally:
		print "Closing camera"
		camera.stop()
		sys.exit()
