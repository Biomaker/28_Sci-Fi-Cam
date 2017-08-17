from Stencil import NumberOfPhotosStencil, BrightnessStencil

class RefreshOverlayMethod():
	def __init__(self, camera, function, *args, **kwargs):
		self.camera 	= camera
		self.function 	= function
		self.args 		= args
		self.kwargs 	= kwargs

	def __call__(self):
		function = getattr(self.camera, self.function)
		function(*self.args, **self.kwargs)
		self.camera._refreshOverlay()


class Mode(Object):
	def __init__(self, camera):
		self.camera				= camera
		self.nButtons			= self.camera.nButtons
		self.buttonFunctions	= [ None for i in self.nButtons ]
		self.stencils			= []
		