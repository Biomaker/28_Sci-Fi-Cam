from Mode import *
from Stencil import *

class ModeProperty(Object):
	def __init__(self, mode):
		self.mode = mode
		self.values = []
		self.currentValue = -1

	def getValue(self):
		return self.values[self.currentValue]

	def setValues(self, values):	
		self.values = values
		self.currentValue = 0

	def setNext(self):
		if currentValue + 1 < len(self.values):
			self.currentValue += 1

	def setPrev(self):
		if currentValue > 0:
			self.currentValue -= 1

class PropertyStencil(Stencil):
	def __init__(self, box, modeProperty, selectable = False):
		super(PropertyStencil, self).__init__(box, modeProperty, selectable)

	def getValue(self):
		return str(self.controller.getValue())

class ProperyMode(Mode):
	def __init__(self, camera):
		super(PropertyMode, self).__init__(camera)
		self.properties = []
		self.buttonFunction = [
			RefreshOverlayMethod(self.camera, "capture"),
			RefreshOverlayMethod(self, "selectStencil"),
			RefreshOverlayMethod(self.selectedPropery, "setNext"),
			RefreshOverlayMethod(self.selectedPropery, "setPrev"),
			RefreshOverlayMethod(self.camera, "foo")
		]
	
	def addProperty(self, modeProperty, stencilBox = None, selectable = True):
		self.properties.append(modeProperty)
		if stencilBox:
			self.stencils.append( propertyStencil(stencilBox, modeProperty, selectable) )


class SingleShotMode(PropertyMode):
	def __init__(self, camera):
		super(SingleShotMode, self).__init__(camera)
		self.addProperty(  )