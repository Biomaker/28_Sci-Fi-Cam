import os
import sys
import threading
import owncloud
from time import sleep

class OwnCloudThread(threading.Thread):
	def __init__(self, ocAddress, ocLogin, ocPass, ocLocalDir, ocRemoteDir = "SciFiCam"):
		super(OwnCloudThread, self).__init__()
		print "Initialising client for {0}".format(ocAddress)
		self.client		= owncloud.Client(ocAddress)
		print "Logging in as {0}".format(ocLogin)
		self.client.login(ocLogin, ocPass)
		
		self.remoteDir	= ocRemoteDir
		self.localDir	= ocLocalDir
		fileInfo = self.client.file_info(self.remoteDir)
		if not fileInfo:
			self.client.mkdir(self.remoteDir)

		self._stop_event 	= threading.Event()

	def updateDir(self, remoteDir, localDir):
		print "RemoteDir: ", remoteDir
		remoteFiles = [ str(os.path.basename( os.path.normpath(file.path) )) for file in self.client.list(remoteDir)]

		for fileName in os.listdir(localDir):
			
			localPath = os.path.join(localDir, fileName)
			remotePath = os.path.join(remoteDir, fileName)
			
			if not fileName in remoteFiles:

				print "Uploading {0} to {1}".format(localPath, remotePath)

				if os.path.isdir(localPath):
					self.client.mkdir( remotePath )
					# self.client.put_directory( remotePath, localPath )
				else:
					self.client.put_file( remotePath, localPath )
	
			elif os.path.isdir(localPath):
				print "Dir exists: ", remotePath
				self.updateDir(remotePath, localPath)


	def run(self):
		while True:
			if self._stop_event.is_set():
				break
			self.updateDir(self.remoteDir, self.localDir)
			sleep(3)
