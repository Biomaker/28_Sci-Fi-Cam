from PIL import Image, ImageDraw, ImageFont
import numpy as np

class Stencil(object):
	def __init__(self, box, camera):
		self.box 		= box
		self.camera 	= camera

	def _drawBox(self, imgDraw):
		imgDraw.rectangle(self.box, fill = (128, 128, 128, 128))
	
	def getValue(self):
		return "Null"

	def _drawText(self, imgDraw):
		boxWidth 		= self.box[2] - self.box[0]
		boxHeight		= self.box[3] - self.box[1]

		fontSize  	= 1
		font 		= ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeMono.ttf", fontSize)

		value 		= str(self.getValue()) 

		while font.getsize(value)[0] < boxWidth * 0.8:
			fontSize += 1
			font 	= ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeMono.ttf", fontSize)

		textSize = font.getsize(value)

		textX = (boxWidth 	- textSize[0]) * 0.5 + self.box[0]
		textY = (boxHeight 	- textSize[1] * 1.25) * 0.5 + self.box[1]

		imgDraw.text((textX, textY), value, fill = (255, 255, 255, 255), font = font)

	def draw(self, overlay):
		img = Image.fromarray(overlay)
		imgDraw = ImageDraw.Draw(img)

		self._drawBox(imgDraw)
		self._drawText(imgDraw)

		overlay = np.array(img)
		return overlay

class NumberOfPhotosStencil(Stencil):
	def getValue(self):
		counter = self.camera._getSetting('counter')
		if not counter:
			counter = 0
		return counter

class BrightnessStencil(Stencil):
	def getValue(self):
		return self.camera.camera.brightness