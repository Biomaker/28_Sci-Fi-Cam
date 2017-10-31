from distutils.core import setup, Extension

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
	scripts = ['scificam/scificam']
)