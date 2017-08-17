from collections import OrderedDict

from PIL import Image, ImageDraw, ImageFont
import numpy as np

class Mode2(object):
	def __init__(self, camera):
		self.camera 	= camera
		self.UIGetters 	= []
		self.UISetters 	= []

	def bind(self, UIElement, function, *args, **kwargs):
		if hasattr(self, function):
			UIElement._bind(self, function, *args, **kwargs)
			
			if UIElement.role == UI_SETTER:
				self.UISetters.append(UIElement)
			else:
				self.UIGetters.append(UIElement)

			return True
		else:
			return False

	def setButtonTrigger(self, pos, function):
		self.camera.buttonThread.setCallback(pos, function)

	def update(self):
		self.camera.update()


UI_GETTER = 0
UI_SETTER = 1

class UIElement(object):
	def __init__(self, box, role = UI_GETTER):
		self.role 		= role
		self.box 		= box
		self.value 		= "Nan" 
		self.function 	= None
		self.selected 	= False
		self.selectedColor = (50, 50, 50, 255)
		self.color = (255, 255, 255, 255)

	def _bind(self, controller, function, *args, **kwargs):
		if hasattr(controller, function):
			self.args = args
			self.kwargs = kwargs
			self.function = getattr(controller, function)

	def _drawBox(self, imgDraw):
		print "Drawing box "
		if self.role == UI_SETTER and self.selected:
			imgDraw.rectangle(self.box, fill = self.selectedColor)
		else:
			print "with color: ", self.color
			imgDraw.rectangle(self.box, fill = self.color)

	def update(self, overlay):
		if self.role == UI_GETTER:
			self.value = function(*self.args, **self.kwargs )
		else:
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

		print "drawing text: ", value

		imgDraw.text((textX, textY), value, fill = (0, 0, 0, 255), font = font)

class UILabel(UIElement, UITextModifyer):
	def __init__(self, box):
		super(UILabel, self).__init__(box, role = UI_GETTER)
		

class UISelector(UIElement, UITextModifyer):
	def __init__(self, box):
		super(UISelector, self).__init__(box, role = UI_SETTER)
		self.current 	= -1
		self.values 	= OrderedDict()

	def getText(self):
		if len(self.values) > 0:
			return self.values.items()[self.current][0]
		else:
			return "Nan"

	def setValues(self, values):	
		self.values 	= OrderedDict(values)
		self.current 	= 0
		self.set(self.current)

	def set(self, idx):
		if idx >=0 and idx < len(self.values):
			self.value = self.values.items()[idx][1]
			self.current = idx

	def setNext(self):
		self.set( self.current + 1 )

	def setPrev(self):
		self.set (self.current - 1)


class SelectorMode(Mode2):
	def __init__(self, camera):
		super(SelectorMode, self).__init__(camera)
		self.selectedElement = UISelector(None)
		
		self.setButtonTrigger(0, self.capture)
		self.setButtonTrigger(1, self.setPrev)
		self.setButtonTrigger(2, self.setNext)
		self.setButtonTrigger(3, self.selectNext)
		self.setButtonTrigger(4, self.setNextMode)


	def setNext(self):
		self.selectedElement.setNext()
		self.update()

	def setPrev(self):
		self.selectedElement.setPrev()
		self.update()

	def select(self, element, update = True):
		if element in self.UISetters:
			self.selectedElement = element
			self.selectedElement.selected = True

		print "selected ", self.UISetters.index(self.selectedElement)
		
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

class SingleShotMode(SelectorMode):
	def __init__(self, camera):
		super(SingleShotMode, self).__init__(camera)

		exposureSelector = UISelector([0,0,200,200])
		exposureSelector.setValues([('100', 100), ('200', 200), ('300', 300), ('400', 400)])
		self.bind( exposureSelector, "setExposure" )

		self.select(exposureSelector, False)

	def setExposure(self, value):
		print value

	def capture(self):
		self.camera.capture()


