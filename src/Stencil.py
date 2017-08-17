from PIL import Image, ImageDraw, ImageFont
import numpy as np

class Stencil(object):
	def __init__(self, box, controller, selectable = False):
		self.box 		= box
		self.controller = controller
		self.selected	= False
		self.selectable = selectable

		self.color		= (128, 128, 128, 128)
		self.selectedColor	= (150, 150, 150, 128)

	def _drawBox(self, imgDraw):
		if self.selected and self.selectable:
			imgDraw.rectangle(self.box, fill = self.selectedColor)
		else:
			imgDraw.rectangle(self.box, fill = self.color)
	
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

