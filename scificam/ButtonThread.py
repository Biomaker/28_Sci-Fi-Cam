import array, fcntl
from time import sleep
import threading

'''
Button Thread

Handles keypresses on 4Dpi hat
'''
class ButtonThread(threading.Thread):
	def __init__(self):
		super(ButtonThread, self).__init__()

		self._stop_event 	= threading.Event()
		self.lock			= threading.Lock()
		
		self.callbacks 		= [None, None, None, None, None]

		self._IOC_NRBITS	=	8
		self._IOC_TYPEBITS	=	8
		self._IOC_SIZEBITS	=	14
		self._IOC_DIRBITS 	=	2
		self._IOC_DIRMASK	=	(1 << self._IOC_DIRBITS) - 1
		self._IOC_NRMASK	=	(1 << self._IOC_NRBITS) - 1
		self._IOC_TYPEMASK	=	(1 << self._IOC_TYPEBITS ) - 1
		self._IOC_NRSHIFT	=	0
		self._IOC_TYPESHIFT	=	self._IOC_NRSHIFT	+	self._IOC_NRBITS
		self._IOC_SIZESHIFT	=	self._IOC_TYPESHIFT	+	self._IOC_TYPEBITS
		self._IOC_DIRSHIFT	=	self._IOC_SIZESHIFT	+	self._IOC_SIZEBITS
		self._IOC_NONE		=	0
		self._IOC_WRITE		=	1
		self._IOC_READ		=	2

	'''
	setCallback() sets a callbacks of a button to the given function
	'''
	def setCallback(self, button, fn):
		self.callbacks[button] = fn

	def _IOC(self, dir, type, nr, size):
		ioc = (dir << self._IOC_DIRSHIFT ) | (type << self._IOC_TYPESHIFT ) | (nr << self._IOC_NRSHIFT ) | (size << self._IOC_SIZESHIFT)
		if ioc > 2147483647: ioc -= 4294967296
		return ioc

	def _IOR(self, type, nr, size):
		return self._IOC(self._IOC_READ,  type, nr, size)
	
	'''
	readKeys() reads the status of the buttons
	'''
	def readKeys(self):
		LCD4DPI_GET_KEYS = self._IOR(ord('K'), 1, 4)
		buf = array.array('h',[0])

		keys = []
		
		with open('/dev/fb1', 'rw') as fd:
			fcntl.ioctl(fd, LCD4DPI_GET_KEYS, buf, 1)
			
			if not buf[0] & 0b00001:
				if self.callbacks[0]:
					self.callbacks[0]()
			if not buf[0] & 0b00010:
				if self.callbacks[1]:
					self.callbacks[1]()
			if not buf[0] & 0b00100:
				if self.callbacks[2]:
					self.callbacks[2]()
			if not buf[0] & 0b01000:
				if self.callbacks[3]:
					self.callbacks[3]()
			if not buf[0] & 0b10000:
				if self.callbacks[4]:
					self.callbacks[4]()

		return keys

	def run(self):
		while not self._stop_event.wait(0.2):
			try:
				self.keys = self.readKeys()
			except:
				print "Exception"
				self.stop()
	
	def stop(self):
		self._stop_event.set()

if __name__ == "__main__":
	bt = ButtonThread()
	bt.start()
	sleep(5)
	bt.stop()
