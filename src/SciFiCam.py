import os
import sys
from time import sleep, strftime

import numpy as np
from PIL import Image

from picamera import PiCamera
import owncloud

from ButtonThread import ButtonThread
from OwnCloudThread import OwnCloudThread

from Mode import *

class SciFiCam(object):
	def __init__(self):
		## Setting directories
		self.dir				= os.getenv('SCI_PI_CAM_DIR', '/home/pi/SciFiCam/')
		self.settingsFile		= os.path.join(self.dir, "settings.py")
		self.picDir				= os.path.join(self.dir, "pics")
		self.iconDir			= os.path.join(self.dir, "icons")
		self.log 				= open(os.path.join(self.dir, "scificam.log"), "a")

		if not os.path.isdir(self.picDir):
			os.makedirs(self.picDir)

		setfile 				= open(self.settingsFile, 'a')
		setfile.close()
		

		self.displayResolution = (640, 480)
		self.overlaySize 	  = ( self.displayResolution[1], self.displayResolution[0],3 )
		
		## Setting camera
		self.camera				= PiCamera()
		self.camera.resolution	= self.displayResolution
		self.camera.rotation	= 90
		self.blank				= np.ones(self.overlaySize, dtype=np.uint8) * 255
		self.UIOverlay			= self.camera.add_overlay(np.getbuffer(np.zeros( self.overlaySize, dtype=np.uint8)), format = 'rgb', alpha = 255, layer = 1)
		
		## Setting button thread
		self.nButtons			= 5
		self.buttonThread		= ButtonThread()
		self.buttonThread.setCallback(0, self.capture)
		self.buttonThread.setCallback(1, self.capture)
		self.buttonThread.setCallback(2, self.capture)
		self.buttonThread.setCallback(3, self.capture)
		self.buttonThread.setCallback(4, self.capture)
		
		## Setting owncloud thread
		self.ocAddress			= self._getSetting("ocAddress")
		self.ocLogin			= self._getSetting("ocLogin")
		self.ocPass				= self._getSetting("ocPass")
		
		self.modes = [ErrorMode]

		self.currentMode = None
		
	def _issueMessage(self, message, level = 0, exception = None):

		levelHeaders = ["ERROR", "WARNING", "LOG"]

		errorMessage = "{0}: ".format(levelHeaders[level])
		errorMessage += message
		if exception:
			errorMessage += "({0})".format(exception)

		print errorMessage
		self.log.write( strftime("%d/%m/%Y %I:%M:%S ") + errorMessage +'\n')
		
		if level==0:
			self.setMode(0, message = message)

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

		return os.path.join( self.dir, "pics", "{0}".format(counter) )

	
	def start(self):
		try:
			self.buttonThread.start()
			if self.ocAddress and self.ocLogin and self.ocPass:
				try:
					self.ocThread = OwnCloudThread(self, self.ocAddress, self.ocLogin, self.ocPass, self.picDir)
					self.ocThread.start()
				except Exception as e:
					self.ocThread = None
					self._issueMessage("Could not initialise OwnCloud", exception = e )
			else:
				self.ocThread = None
			if len(self.modes) > 1:
				self.setMode( 1 )
			else:
				self._issueMessage("No modes found", level = 0, exception = e)
		except Exception as e:
			self._issueMessage("Faield to start camera", level = 0, exception = e)


	def addMode(self, mode):
		try:
			self.modes.append(mode)
		except Exception as e:
			self._issueMessage("Faield to add mode", level = 0, exception = e)

	def setMode(self, idx, *args, **kwargs):
		self._issueMessage("Setting mode {0}".format(idx), level = 2)
		try:
			if idx >= 0 and idx < len(self.modes):
				self.camera.stop_preview()
				self.renderer = self.camera.start_preview()
				self.camera.preview.alpha = 128
				if self.currentMode:
					self.currentMode.close()
				self.currentMode = self.modes[idx](self, *args, **kwargs)
				self.update()
		except Exception as e:
			self._issueMessage("Failed to set mode {0}".format(idx), level = 0, exception = e)
	
	def update(self):
		try:
			overlay = np.zeros( self.overlaySize, dtype=np.uint8)
			for UIElement in self.currentMode.UISetters + self.currentMode.UIGetters + self.currentMode.UIStatic:
				overlay = UIElement.update(overlay)

			self.camera.remove_overlay(self.UIOverlay)
			self.UIOverlay = self.camera.add_overlay( np.getbuffer(overlay), format = 'rgb', alpha = 255, layer = 1 )
		except:
			self._issueMessage("Failed to run update", level = 0, exception = e)

	def setNextMode(self):
		if len(self.modes) > 1:
			index = 1
			if self.currentMode.__class__ in self.modes:
				index = self.modes.index(self.currentMode.__class__) + 1
				if index == len(self.modes):
					index = 1
			self.setMode(index)

	def stop(self):
		self._issueMessage("Stopping camera", level = 2)
		self.buttonThread._stop_event.set()
		if self.ocThread:
			self.ocThread._stop_event.set()
		self.camera.stop_preview()

	def restart(self):
		self._issueMessage("System reboot", level = 2)
		self.stop()
		command = "/usr/bin/sudo /sbin/shutdown -r now"
		
		import subprocess
		process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
		output = process.communicate()[0]

	def capture(self):
		try:
			self._issueMessage("Capturing picture", level = 2)

			# Drawing flash effect
			o = self.camera.add_overlay(np.getbuffer(self.blank), alpha = 255, layer = 5)
			sleep(0.2)
			self.camera.remove_overlay(o)

			# Capturing to file
			fileName = self._getNewFileName() + ".png"
			self._issueMessage("Saving picture to {0}".format(fileName), level = 2)
			self.camera.capture(fileName)
			
			# Holding captured image
			image = Image.open(fileName)
			o = self.camera.add_overlay(image.tostring(), size = image.size, alpha = 255, layer = 3)
			sleep(1)
			self.camera.remove_overlay(o)
		except Exception as e:
			self._issueMessage("Failed to capture an image", level = 0, exception = e)

if __name__ == "__main__":
	camera = SciFiCam()
	camera.addMode(AutoMode)
	camera.addMode(ManualMode)
	camera.addMode(TimelapseMode)
	camera.addMode(VideoCaptureMode)
	camera.addMode(ShutDownMode)
	camera.start()
	try:
		while True:
			sleep(1)
	finally:
		camera.stop()
		sys.exit()
