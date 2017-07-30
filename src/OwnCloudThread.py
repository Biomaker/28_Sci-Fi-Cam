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
		
		self.remoteDir	= "SciFiCam"
		self.localDir	= ocLocalDir
		fileInfo = self.client.file_info(self.remoteDir)
		if not fileInfo:
			self.client.mkdir(self.remoteDir)

		self.active		= False
	
	def run(self):
		while True:
			remoteFiles = [ str(os.path.basename(file.path)) for file in self.client.list(self.remoteDir)]
			print remoteFiles
			for fileName in os.listdir(self.localDir):
				print fileName
				if not fileName in remoteFiles:
					localPath 	= os.path.join(self.localDir, fileName)
					remotePath 	= os.path.join(self.remoteDir, fileName)
					self.client.put_file( remotePath, localPath )
					print "Uploading {0}".format(localPath)
			sleep(3)
