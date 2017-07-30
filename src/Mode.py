from Stencil import NumberOfPhotosStencil

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
			RefreshOverlayMethod(self.camera, "capture"),
			RefreshOverlayMethod(self.camera, "capture"),
			RefreshOverlayMethod(self.camera, "capture"),
			RefreshOverlayMethod(self.camera, "capture"),
			RefreshOverlayMethod(self.camera, "capture"),
		]
		self.stencils = [ NumberOfPhotosStencil([0, 0, 200, 200], self.camera) ]
