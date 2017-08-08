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

class CaptureMode:
	def __init__(self, camera):
		self.camera = camera
		self.buttonFunction = [
			RefreshOverlayMethod(self.camera, "restart"),
			RefreshOverlayMethod(self.camera, "changeBrightness", 10),
			RefreshOverlayMethod(self.camera, "changeBrightness", -10),
			RefreshOverlayMethod(self.camera, "foo"),
			RefreshOverlayMethod(self.camera, "capture"),
		]
		self.stencils = [ 	NumberOfPhotosStencil([0, 0, 200, 200], self.camera),
							BrightnessStencil([0, self.camera.camera.resolution[1]-200, 200, self.camera.camera.resolution[1] ], self.camera) ]
