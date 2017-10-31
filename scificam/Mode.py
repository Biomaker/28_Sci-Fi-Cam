from collections import OrderedDict

from PIL import Image, ImageDraw, ImageFont
import numpy as np
from fractions import Fraction
from time import sleep
import os

from threading import Thread, Event
from subprocess import call

'''
Mode

A base calass for camera modes.
'''
class Mode(object):
	def __init__(self, camera):
		self.camera 	= camera
		self.UIGetters 	= []
		self.UISetters 	= []
		self.UIStatic 	= []
	
	'''
	init() is called before rendering a mode.

	'''
	def init(self):
		pass

	'''
	bind() binds a mode method as a getter or setter function to a given UI element.
			*args and **kwargs can be used to paramerarise the getter or setter function.
	'''
	def bind(self, UIElement, function = "None", *args, **kwargs):
		
		UIElement._bind(self, function, *args, **kwargs)

		if UIElement.role == UI_STATIC:
			self.UIStatic.append(UIElement)
			return True
		elif UIElement.role == UI_SETTER:
			self.UISetters.append(UIElement)
			return True
		elif UIElement.role == UI_GETTER:
			self.UIGetters.append(UIElement)
			return True
		else:
			return False

	'''
	setButtonTrigger() sets a callback for a button at given position.
	'''
	def setButtonTrigger(self, pos, function):
		self.camera._issueMessage("Setting callback {0}".format(pos), level = 2)
		self.camera.buttonThread.setCallback(pos, function)

	'''
	update() is used to re-render the mode.
	'''
	def update(self):
		self.camera.update()
	
	'''
	close() is called before removing the mode from display.
	'''
	def close(self):
		pass


'''
UIElement

A base class for UI elements. Can be of one of three types:
UI_GETTER: uses update() to retrieve a value using given function
UI_SETTER: uses update() to call a given function with it's value
UI_STATIC: does not use update()

'''

UI_GETTER = 0
UI_SETTER = 1
UI_STATIC = 2

class UIElement(object):
	def __init__(self, box, role = UI_GETTER):
		self.role			= role
		self.box			= box
		self.value			= "Nan"
		self.function		= None
		self.selected		= False
		self.color 			= (50, 50, 50, 255)
		self.selectedColor	= (255, 255, 255, 255)
	
	'''
	_bind() binds a controller function to the UIElement.
	'''
	def _bind(self, controller, function, *args, **kwargs):
		self.controller = controller
		if hasattr(controller, function):
			self.args = args
			self.kwargs = kwargs
			self.function = getattr(controller, function)
	
	'''
	_drawBox() renders a placeholder for the UI element.
	'''
	def _drawBox(self, imgDraw):
		if self.role == UI_SETTER and self.selected:
			imgDraw.rectangle(self.box, fill = self.selectedColor)
		else:
			imgDraw.rectangle(self.box, fill = self.color)

	'''
	update() is called every time a Mode is re-rendered. It calls _drawBox() function to
	render a placeholder and _drawContent() function, which is defied by UIModifiers,to
	render a UI element value.
	'''
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

'''
UITextModifyer

Renders the value of a UI element as a string
'''
class UITextModifyer(object):
	
	'''
	getText() formats the value to a string.
	'''
	def getText(self):
		return str(self.value)

	'''
	_drawContent() draws string inside a placeholder of the UIElement.
	'''
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

'''
UIImageModifyer

Renders an icon from /icons folder with name given as a value of a UI element
'''

class UIImageModifyer(object):
	
	'''
	loadImage() loads an image from the "/icon" folder.
	'''
	def loadImage(self):
		try:
			image = Image.open(os.path.join(self.controller.camera.iconDir, self.value))
		except:
			image = None
		finally:
			return image
	
	'''
	_drawContent() renders the icon isonde a placeholder of the UIElement.
	'''
	def _drawContent(self, imgDraw):
		image = self.loadImage()
		if image:
			boxWidth 		= self.box[2] - self.box[0]
			boxHeight		= self.box[3] - self.box[1]
			image = image.resize( (boxWidth, boxHeight) )
			imgDraw.bitmap((self.box[0], self.box[1]), image)

'''
UILabel

A label class: a single-valued static UIElement with UITextModifyer
'''

class UILabel(UIElement, UITextModifyer):
	def __init__(self, box, value):
		super(UILabel, self).__init__(box, role = UI_STATIC)
		self.value = value

'''
UIImage

An Image class: a single-valued static UIElement with UIImageModifyer
'''

class UIImage(UIElement, UIImageModifyer):
	def __init__(self, box, value):
		super(UIImage, self).__init__(box, role = UI_STATIC)
		self.value = value
		self.boxRecord = self.box

	'''
	hide() hides an image
	'''
	def hide(self):
		self.box = (0,0,0,0)

	'''
	show() shows an image
	'''
	def show(self):
		self.box = self.boxRecord

'''
UISelector

A selector class: a multi-valued setter UIElement with UITextModifyer. It is used to
store a list of values.
'''

class UISelector(UIElement, UITextModifyer):
	def __init__(self, box):
		super(UISelector, self).__init__(box, role = UI_SETTER)
		self.current 	= -1
		self.values 	= OrderedDict()
	
	'''
	getText() overrides UITextModifyer mehod to return the currently selected value from the list.
	'''
	def getText(self):
		if len(self.values) > 0:
			return self.values[self.current][0]
		else:
			return "Nan"

	'''
	setValues() sets the list of values.
	'''
	def setValues(self, values, default = 0):	
		self.values 	= values
		self.current 	= 0

		
		self.current = default
		
		self.set(self.current)

	'''
	setValue() sets curent value to the value from the list, given it's index
	'''
	def set(self, idx):
		if idx >=0 and idx < len(self.values):
			self.value = self.values[idx][1]
			self.current = idx
	
	'''
	setNext() sets next value from the list. In case of the end of the list, a first value is set
	'''
	def setNext(self):
		if len(self.values) > 0:
			self.set( (self.current + 1) % len(self.values) )
	
	'''
	setPrev() sets previous value from the list. In case the the end of list, a last value is set
	'''
	def setPrev(self):
		if len(self.values) > 0:
			self.set ( (self.current - 1) % len(self.values) )

'''
SelectorMode

A base class for sequential modes.

Button callbacs:
	0: capture image
	1: set previous value from selected UISelector
	2: set next value from selected UISelector
	3: select next UISelector
	4: select next mode from the list of camera modes
'''
class SelectorMode(Mode):
	def __init__(self, camera):
		super(SelectorMode, self).__init__(camera)
		self.selectedElement = UISelector(None)

		modeLabel = UILabel([0,425, 70,475], "mode")
		self.bind(modeLabel)

		selectLabel = UILabel([90, 425, 160, 475], "select")
		self.bind(selectLabel)

		upLabel = UILabel([180, 425, 250, 475], "up")
		self.bind(upLabel)

		downLabel = UILabel([270, 425, 340, 475], "down")
		self.bind(downLabel)

		selectLabel = UILabel([360, 425, 430, 475], "capture")
		self.bind(selectLabel)

		if hasattr(self, "icon"):
			icon = UIImage([20, 20, 120, 120], self.icon )
			self.bind(icon)

		self.setButtonTrigger(0, self.capture)
		self.setButtonTrigger(1, self.setPrev)
		self.setButtonTrigger(2, self.setNext)
		self.setButtonTrigger(3, self.selectNext)
		self.setButtonTrigger(4, self.setNextMode)

	def close(self):
		pass

	def capture(self):
		self.camera.capture()
	
	'''
	setNext() sets a next value on the active UISelector.
	'''
	def setNext(self):
		self.selectedElement.setNext()
		self.update()

	'''
	setPrev() sets a previous value on the active UISelector.
	'''
	def setPrev(self):
		self.selectedElement.setPrev()
		self.update()

	'''
	select() sets the given UISetter to an active state.
	'''
	def select(self, element, update = True):
		if element in self.UISetters:
			self.selectedElement = element
			for element in self.UISetters:
				element.selected = False
			self.selectedElement.selected = True
		
		if update:
			self.update()
	
	'''
	selectNext() selects the next UISetters.
	'''
	def selectNext(self):
		if len(self.UISetters) > 0:
			index = 0
			if self.selectedElement in self.UISetters:
				index = self.UISetters.index(self.selectedElement) + 1
				if index == len(self.UISetters):
					index = 0
			
			self.select( self.UISetters[index] )
	
	'''
	setNextMode() sets the next mode in the list of camera modes.
	'''
	def setNextMode(self):
		self.camera.setNextMode()


'''
AutoMode

A SelectorMode for automatic camera settigns.

Settings:
	Exposure correction
	Visual effects
	AWB
'''
class AutoMode(SelectorMode):
	def __init__(self, camera):
		self.icon = "cameraA.png"

		super(AutoMode, self).__init__(camera)

		self.camera.camera.framerate = 30
		self.camera.camera.shutter_speed = 0
		self.camera.camera.exposure_mode = "auto"
		
		exposureCompensationSelector = UISelector([ 220, 20, 320, 120 ])
		exposureCompensationSelector.setValues(
			[('-4', -24), ('-3', -18), ('-2', -12), ('-1', -6), ('+/-', 0 ), ('+1', 6), ('+2', 12), ('+3', 18), ('+4', 24) ], 4
		)
		self.bind( exposureCompensationSelector, "setExposureCompensation" )

		whiteBalanceSelector = UISelector([370, 20, 470, 120])
		whiteBalanceSelector.setValues([ ("A", "auto"), ("S", "sunlight"), ("F", "fluorescent"), ("C", "cloudy") ], 0)
		self.bind( whiteBalanceSelector, "setWhiteBalance" )

		effectSelector = UISelector([520, 20, 620, 120])
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

'''
ManualMode

A SelectorMode for manual camera settings.

Settigns:
	Shutter speed
'''
class ManualMode(SelectorMode):
	def __init__(self, camera):
		self.icon = "cameraM.png"
		self.shutter_speed = 0

		super(ManualMode, self).__init__(camera)

		self.camera.camera.exposure_mode = "off"
		

		shutterSpeedSelector = UISelector([220, 20, 320, 120])
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

'''
TimelapseTimer

A helper class for delayign timelapse steps
'''
class TimelapseTimer(Thread):
	def __init__(self, controller, interval):
		super(TimelapseTimer, self).__init__()
		self.controller = controller
		self.stopped = Event()
		self.interval = interval
	
	def run(self):
		self.controller.camera._issueMessage("Starting timelapse timer", level = 0)
		while not self.stopped.wait(self.interval):
			try:
				self.controller.makeShot()
			except:
				self.stopped.set()

'''
TimelapseMode

A SelectorMode for capturing time-lapses.

Settings:
	Shutter speed
	Timelapse interval
'''

class TimelapseMode(SelectorMode):
	def __init__(self, camera):
		self.icon = "cameraT.png"
		self.shutter_speed = 0

		super(TimelapseMode, self).__init__(camera)
		self.camera.camera.exposure_mode = "off"

		self.active = False
		self.interval = 60
		self.counter = 0

		shutterSpeedSelector = UISelector([220, 20, 320, 120])
		shutterSpeedSelector.setValues(
			[('A', 0), ('1/30', 34000), ('1/15', 68000), ('1/8', 125000), ('1/4', 250000), ('1/2', 500000)]
		)
		self.bind( shutterSpeedSelector, "setShutterSpeed" )

		intervalSelector = UISelector([370, 20, 470, 120])
		intervalSelector.setValues([ ("10''", 10), ("20''", 20), ("30''", 30), ("45''", 45), ("1'", 60), ("2'", 120), ("3'", 180), ("4'", 240), ("5'", 300), ("10'", 600), ("20'", 1200), ("30'", 1800), ("60'", 3600) ], 4)
		self.bind( intervalSelector, "setInterval" )

		self.counterLabel = UILabel([520, 375, 620, 475], "-")
		self.bind(self.counterLabel)

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
		self.camera._issueMessage("Saving picture to {0}".format(fileName), level = 2)

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
				self.camera._issueMessage("Failed to capture an image", level = 0, exception = e)
		else:
			self.camera._issueMessage("Stopping timelapse timer", level = 2)
			self.timer.stopped.set()
			self.active = False
			self.counter = 0
			self.counterLabel.value = '-'
			self.camera.update()

'''
VideoWait

A helper Thread class for waiting for recording end.
'''
class VideoWait(Thread):
	def __init__(self, controller):
		super(VideoWait, self).__init__()
		self.controller = controller
		self.stopped = Event()

	def run(self):
		self.controller.camera._issueMessage("Starting video recording", level = 2)
		while not self.stopped.is_set():
			self.controller.camera.camera.wait_recording(1)
		self.controller.stopRecording()

'''
VideoCaptureMode

A SelectorMode for capturing videos.
'''
class VideoCaptureMode(SelectorMode):
	def __init__(self, camera):
		try:
			self.icon = "cameraV.png"
			super(VideoCaptureMode, self).__init__(camera)
			self.camera.camera.exposure_mode = "auto"
			self.recording = False

			self.recordImage = UIImage([520, 375, 620, 475], "record.png")
			self.recordImage.hide()
			self.bind(self.recordImage)
		except Exception as e:
			self.camera._issueMessage("Failed to start VideoCaptureMode", level = 0, exception = e)

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
			self.camera._issueMessage("Failed to capture a video", level = 0, exception = e)

	def close(self):
		if self.recording:
			self.recordThread.stopped.set()
		while self.recording:
			sleep(1)

	def stopRecording(self):
		self.camera._issueMessage("Stopping video recording", level = 2)
		self.camera.camera.stop_recording()
		os.rename(self.fileName + ".h264.part", self.fileName + ".h264")
		self.recordImage.hide()
		self.camera.update()
		self.recording = False

'''
ShutDownMode

A SelectorMode for rebooting the camera.
'''
class ShutDownMode(SelectorMode):
	def __init__(self, camera):
		super(ShutDownMode, self).__init__(camera)
		self.message = UILabel([0, 125, 640, 225], "Press capture to power off")
		self.bind(self.message)
		
	def capture(self):
		self.camera.restart()
		 # call("sudo nohup shutdown -h now", shell=True)

'''
ErrorMode

A mode for displaying error messages
'''
class ErrorMode(Mode):
	def __init__(self, camera, message = ''):
		super(ErrorMode, self).__init__(camera)
		if not message:
			message = "SciFiCam caught an unexpected error"
		
		self.errorLabel = UILabel([0, 25, 640, 125], "ERROR")
		self.bind(self.errorLabel)

		self.errorLabel1 = UILabel([0, 125, 640, 225], message)
		self.bind(self.errorLabel1)

		self.errorLabel2 = UILabel([0, 225, 640, 325], "See Log for details. Press capture to reboot")
		self.bind(self.errorLabel2)

		selectLabel = UILabel([360, 425, 430, 475], "reboot")
		self.bind(selectLabel)
		
		self.setButtonTrigger(0, self.restart)
		self.setButtonTrigger(1, self.none)
		self.setButtonTrigger(2, self.none)
		self.setButtonTrigger(3, self.none)
		self.setButtonTrigger(4, self.none)

	def none(self):
		pass

	def restart(self):
		 self.camera.restart()