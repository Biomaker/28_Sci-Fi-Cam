import os
from setuptools import setup
from setuptools.command.install import install
import subprocess

class SciFiCamInstall(install):
	def run(self):
		
		cmd = "sudo apt-get install cmake"
		
		print "Installing cmake...\n{0}".format(subprocess.check_output(cmd, shell=True))

		dirPath = os.path.dirname(os.path.realpath(__file__))
		buildPath = os.path.join( dirPath, 'fbcp/build' )

		cmd = "cmake .."

		print "Building fbcp...\n{0}".format( subprocess.check_output(cmd, cwd = buildPath, shell=True) )

		cmd = "sudo make install"
		print "Installing fbcp...\n{0}".format( subprocess.check_output(cmd, cwd = buildPath, shell=True) )

		install.run(self)		
setup(
	name = 'scificam',
	packages = ['scificam'],
	version = '0.1',
	description = 'Firmware for SciFiCam',
	author = 'Mihails Delmans',
	author_email = 'm.delmans@gmail.com',
	url = 'https://github.com/BioMakers/28_Sci-Fi-Cam', 
	download_url = 'https://github.com/BioMakers/28_Sci-Fi-Cam/archive/0.1.tar.gz',
	keywords = ['Raspberry', 'camera'], 
	classifiers = [],
	install_requires = ['pyocclient', 'pillow==2.6.1', 'picamera', 'numpy==1.8.2'],
	scripts = ['scificam/scificam'],
	cmdclass={'install': SciFiCamInstall}
)