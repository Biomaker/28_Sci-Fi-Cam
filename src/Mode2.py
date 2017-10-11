from collections import OrderedDict

from PIL import Image, ImageDraw, ImageFont
import numpy as np
from fractions import Fraction
from time import sleep
import os

from threading import Thread, Event

class Mode2(object):
	def __init__(self, camera):
		self.camera 	= camera
		self.UIGetters 	= []
		self.UISetters 	= []
		self.UIStatic 	= []

	def init():
		pass

	def bind(self, UIElement, function, *args, **kwargs):
		if hasattr(self, function):
			UIElement._bind(self, function, *args, **kwargs)
			UIElement.controller = self
			if UIElement.role == UI_SETTER:
				self.UISetters.append(UIElement)
			else:
				self.UIGetters.append(UIElement)

			return True
		else:
			return False

	def addStatic(self, UIElement):
		if UIElement.role == UI_STATIC:
			UIElement.controller = self
			self.UIStatic.append(UIElement)

	def setButtonTrigger(self, pos, function):
		print "Setting callback ", pos
		self.camera.buttonThread.setCallback(pos, function)

	def update(self):
		self.camera.update()


UI_GETTER = 0
UI_SETTER = 1
UI_STATIC = 2

class UIElement(object):
	def __init__(self, box, role = UI_GETTER):
		self.role 		= role
		self.box 		= box
		self.value 		= "Nan"
		self.function 	= None
		self.selected 	= False
		self.color = (50, 50, 50, 255)
		self.selectedColor = (255, 255, 255, 255)

	def _bind(self, controller, function, *args, **kwargs):
		if hasattr(controller, function):
			self.args = args
			self.kwargs = kwargs
			self.function = getattr(controller, function)

	def _drawBox(self, imgDraw):
		if self.role == UI_SETTER and self.selected:
			imgDraw.rectangle(self.box, fill = self.selectedColor)
		else:
			imgDraw.rectangle(self.box, fill = self.color)

	def update(self, overlay):
		if self.role == UI_GETTER:
			self.value = function(*self.args, **self.kwargs )
		elif self.role == UI_SETTER:
			self.function( value = self.value, *self.args, **self.kwargs )

		img = Image.fromarray(overlay)
		imgDraw = ImageDraw.Draw(img)

		self._drawBox(imgDraw)
		
		if hasattr(self, "_drawContent"):
			self._drawContent(imgDraw)

		overlay = np.array(img)
		return overlay

class UITextModifyer(object):
	def getText(self):
		return str(self.value)

	def _drawContent(self, imgDraw):
		boxWidth 		= self.box[2] - self.box[0]
		boxHeight		= self.box[3] - self.box[1]

		fontSize  	= 1
		font 		= ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeMono.ttf", fontSize)

		value = str( self.getText() )

		while font.getsize(value)[0] < boxWidth * 0.8:
			fontSize += 1
			font 	= ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeMono.ttf", fontSize)

		textSize = font.getsize(value)

		textX = (boxWidth 	- textSize[0]) * 0.5 + self.box[0]
		textY = (boxHeight 	- textSize[1] * 1.25) * 0.5 + self.box[1]

		imgDraw.text((textX, textY), value, fill = (0, 0, 0, 255), font = font)

class UIImageModifyer(object):
	def loadImage(self):
		try:
			image = Image.open(os.path.join(self.controller.camera.iconDir, self.value))
			print "Loaded {0}".format(self.value)
		except:
			image = None
			print "Icon {0} not found".format(self.value)
		finally:
			return image
	
	def _drawContent(self, imgDraw):
		
		image = self.loadImage()
		if image:
			boxWidth 		= self.box[2] - self.box[0]
			boxHeight		= self.box[3] - self.box[1]
			image = image.resize( (boxWidth, boxHeight) )
			print image.size
			imgDraw.bitmap((self.box[0], self.box[1]), image)


class UILabel(UIElement, UITextModifyer):
	def __init__(self, box, value):
		super(UILabel, self).__init__(box, role = UI_STATIC)
		self.value = value

class UIImage(UIElement, UIImageModifyer):
	def __init__(self, box, value):
		super(UIImage, self).__init__(box, role = UI_STATIC)
		self.value = value
		self.boxRecord = self.box

	def hide(self):
		self.box = (0,0,0,0)

	def show(self):
		self.box = self.boxRecord

class UISelector(UIElement, UITextModifyer):
	def __init__(self, box):
		super(UISelector, self).__init__(box, role = UI_SETTER)
		self.current 	= -1
		self.values 	= OrderedDict()

	def getText(self):
		if len(self.values) > 0:
			return self.values[self.current][0]
		else:
			return "Nan"

	def setValues(self, values, default = 0):	
		self.values 	= values
		self.current 	= 0

		
		self.current = default
		
		self.set(self.current)

	def set(self, idx):
		if idx >=0 and idx < len(self.values):
			self.value = self.values[idx][1]
			self.current = idx

	def setNext(self):
		self.set( (self.current + 1) % len(self.values) )

	def setPrev(self):
		self.set ( (self.current - 1) % len(self.values) )


class SelectorMode(Mode2):
	def __init__(self, camera):
		super(SelectorMode, self).__init__(camera)
		self.selectedElement = UISelector(None)

		modeLabel = UILabel([0,400, 70,450], "mode")
		self.addStatic(modeLabel)

		selectLabel = UILabel([90, 400, 160, 450], "select")
		self.addStatic(selectLabel)

		upLabel = UILabel([180, 400, 250, 450], "up")
		self.addStatic(upLabel)

		downLabel = UILabel([270, 400, 340, 450], "down")
		self.addStatic(downLabel)

		selectLabel = UILabel([360, 400, 430, 450], "capture")
		self.addStatic(selectLabel)

		if hasattr(self, "icon"):
			icon = UIImage([0, 0, 100, 100], self.icon )
			self.addStatic(icon)

		self.setButtonTrigger(0, self.capture)
		self.setButtonTrigger(1, self.setPrev)
		self.setButtonTrigger(2, self.setNext)
		self.setButtonTrigger(3, self.selectNext)
		self.setButtonTrigger(4, self.setNextMode)

	def close(self):
		pass

	def capture(self):
		self.camera.capture()

	def setNext(self):
		self.selectedElement.setNext()
		self.update()

	def setPrev(self):
		self.selectedElement.setPrev()
		self.update()

	def select(self, element, update = True):
		if element in self.UISetters:
			self.selectedElement = element
			for element in self.UISetters:
				element.selected = False
			self.selectedElement.selected = True
		
		if update:
			self.update()
	
	def selectNext(self):
		if len(self.UISetters) > 0:
			index = 0
			if self.selectedElement in self.UISetters:
				index = self.UISetters.index(self.selectedElement) + 1
				if index == len(self.UISetters):
					index = 0
			
			self.select( self.UISetters[index] )

	def setNextMode(self):
		self.camera.setNextMode()

class AutoMode(SelectorMode):
	def __init__(self, camera):
		self.icon = "cameraA.png"

		super(AutoMode, self).__init__(camera)

		print "Auto MODE selected"
		

		self.camera.camera.framerate = 30
		self.camera.camera.shutter_speed = 0
		self.camera.camera.exposure_mode = "auto"
		print "Exposure: ", self.camera.camera.exposure_speed

		# print "Stopping preview"
		# self.camera.camera.stop_preview()
		# self.camera.camera.exposure_mode = "auto"
		# print "Starting preview"
		# self.camera.renderer = self.camera.camera.start_preview()
		# sleep(2)
		
		exposureCompensationSelector = UISelector([ 200, 0, 300, 100 ])
		exposureCompensationSelector.setValues(
			[('-4', -24), ('-3', -18), ('-2', -12), ('-1', -6), ('+/-', 0 ), ('+1', 6), ('+2', 12), ('+3', 18), ('+4', 24) ], 4
		)
		self.bind( exposureCompensationSelector, "setExposureCompensation" )

		whiteBalanceSelector = UISelector([350, 0, 450, 100])
		whiteBalanceSelector.setValues([ ("A", "auto"), ("S", "sunlight"), ("F", "fluorescent"), ("C", "cloudy") ], 0)
		self.bind( whiteBalanceSelector, "setWhiteBalance" )

		effectSelector = UISelector([500, 0, 600, 100])
		effectSelector.setValues([ ("X", "none"), ("N", "negative"), ("W", "watercolor"), ("C", "cartoon" ), ("P", "pastel"), ("WO", "washedout"), ("CS", "colorswap") ], 0)
		self.bind(effectSelector, "setEffect")
		
		self.select(exposureCompensationSelector, False)

	def close(self):
		self.setExposureCompensation(0)
		self.setWhiteBalance("auto")
		self.setEffect("none")

	def setExposureCompensation(self, value):
		self.camera.camera.exposure_compensation = value

	def setWhiteBalance(self, value):
		self.camera.camera.awb_mode = value

	def setEffect(self, value):
		self.camera.camera.image_effect = value

class ManualMode(SelectorMode):
	def __init__(self, camera):
		self.icon = "cameraM.png"
		self.shutter_speed = 0

		super(ManualMode, self).__init__(camera)

		print "Manual MODE selected"
		self.camera.camera.exposure_mode = "off"
		

		shutterSpeedSelector = UISelector([200, 0, 300, 100])
		shutterSpeedSelector.setValues(
			[('A', 0), ('1/30', 34000), ('1/15', 68000), ('1/8', 125000), ('1/4', 250000), ('1/2', 500000)]
		)
		self.bind( shutterSpeedSelector, "setShutterSpeed" )
		
		
		self.select(shutterSpeedSelector, False)

	def setShutterSpeed(self, value):
		if value:
			self.camera.camera.framerate = Fraction(1000000, value)
		else:
			if (self.camera.camera.exposure_speed):
				self.camera.camera.framerate = Fraction(1000000, self.camera.camera.exposure_speed)
		
		self.camera.camera.shutter_speed = value
		self.shutter_speed = value

	def capture(self):
		self.camera.camera.exposure_mode = "auto"
		self.camera.camera.shutter_speed = self.shutter_speed
		sleep(1)
		self.camera.camera.exposure_mode = "off"
		self.camera.capture()


class TimelapseTimer(Thread):
	def __init__(self, controller, interval):
		super(TimelapseTimer, self).__init__()
		self.controller = controller
		self.stopped = Event()
		self.interval = interval
	
	def run(self):
		print "Timer is running"
		while not self.stopped.wait(self.interval):
			try:
				print("Tick")
				self.controller.makeShot()
			except:
				self.stopped.set()

class TimelapseMode(SelectorMode):
	def __init__(self, camera):
		self.icon = "cameraT.png"
		self.shutter_speed = 0

		super(TimelapseMode, self).__init__(camera)
		self.camera.camera.exposure_mode = "off"

		self.active = False
		self.interval = 60
		self.counter = 0

		shutterSpeedSelector = UISelector([200, 0, 300, 100])
		shutterSpeedSelector.setValues(
			[('A', 0), ('1/30', 34000), ('1/15', 68000), ('1/8', 125000), ('1/4', 250000), ('1/2', 500000)]
		)
		self.bind( shutterSpeedSelector, "setShutterSpeed" )

		intervalSelector = UISelector([350, 0, 450, 100])
		intervalSelector.setValues([ ("10''", 10), ("20''", 20), ("30''", 30), ("45''", 45), ("1'", 60), ("2'", 120), ("3'", 180), ("4'", 240), ("5'", 300), ("10'", 600), ("20'", 1200), ("30'", 1800), ("60'", 3600) ], 4)
		self.bind( intervalSelector, "setInterval" )

		self.counterLabel = UILabel([540, 350, 640, 450], "-")
		self.addStatic(self.counterLabel)

		self.select(intervalSelector, False)

	def setInterval(self, value):
		self.interval = value
	
	def setShutterSpeed(self, value):
		if value:
			self.camera.camera.framerate = Fraction(1000000, value)
		else:
			if (self.camera.camera.exposure_speed):
				self.camera.camera.framerate = Fraction(1000000, self.camera.camera.exposure_speed)
		
		self.camera.camera.shutter_speed = value
		self.shutter_speed = value

	def makeShot(self):
		fileName = os.path.join(self.timelapseDir, "{0}.png".format(self.counter))

		self.camera.camera.exposure_mode = "auto"
		self.camera.camera.shutter_speed = self.shutter_speed
		sleep(1)
		self.camera.camera.exposure_mode = "off"


		self.camera.camera.capture(fileName)
		
		self.counter += 1
		self.counterLabel.value = "{0}".format(self.counter)
		self.camera.update()

		print "Saving to ", fileName

	def capture(self):
		if not self.active:
			self.active = True
			self.timelapseDir = self.camera._getNewFileName()
			try:
				os.mkdir(self.timelapseDir)
				self.timer = TimelapseTimer(self, 10)
				self.counterLabel.value = '0'
				self.camera.update()
				self.timer.start()
			except Exception as e:
				print e
			
		else:
			print "Stopping"
			self.timer.stopped.set()
			self.active = False
			self.counter = 0
			self.counterLabel.value = '-'
			self.camera.update()

class VideoWait(Thread):
	def __init__(self, controller):
		super(VideoWait, self).__init__()
		self.controller = controller
		self.stopped = Event()

	def run(self):
		print "Starting Recording..."
		while not self.stopped.is_set():
			self.controller.camera.camera.wait_recording(1)
			print "Tick..."
		self.controller.stopRecording()

class VideoCaptureMode(SelectorMode):
	def __init__(self, camera):
		try:
			self.icon = "cameraV.png"
			super(VideoCaptureMode, self).__init__(camera)
			self.camera.camera.exposure_mode = "auto"
			self.recording = False

			self.recordImage = UIImage([540, 350, 640, 450], "record.png")
			self.recordImage.hide()
			self.addStatic(self.recordImage)
		except Exception as e:
			print e

	def capture(self):
		try:
			if not self.recording:
				self.fileName = self.camera._getNewFileName()
				self.camera.camera.start_recording(self.fileName + ".h264.part", format = "h264")
				self.recording = True
				self.recordThread = VideoWait(self)
				self.recordThread.start()
				self.recordImage.show()
				self.camera.update()
			else:
				self.recordThread.stopped.set()
		except Exception as e:
			print e

	def close(self):
		if self.recording:
			self.recordThread.stopped.set()
		while self.recording:
			sleep(1)

	def stopRecording(self):
		print "Stopping Recording..."
		self.camera.camera.stop_recording()
		os.rename(self.fileName + ".h264.part", self.fileName + ".h264")
		self.recordImage.hide()
		self.camera.update()
		self.recording = False


