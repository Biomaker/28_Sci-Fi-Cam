## Synopsis

SciFiCam is a Raspberry Pi based camera assembly with a digital camera UI and syncronsation over Wi-Fi.

## Software

The software is written in Python and exploits pycamera overlay system for creting a user interface. It consists of three main components that run on individual threads.

### Camera Thread

Camera thread is responsible for communication to pycamera library and handling user interface. It acts as a Model in an MVC architecture. Camera has several Modes, which acte as Controllers; and each Mode is driven by UIElements, which act as View elements.

Modes have the same meaning as modes on a digital cameras, exposing different aspects of camera settings. So far there are xxx Modes implemented:

* Automatic mode
* Manual mode
* Timelapse mode
* Vide mode

In addition there are two utility modes: ShutdownMode and ErrorMode for rebooting the Pi and displaying error messages.

### Button thread

Button thread allows binding Mode functions to key presses on the 4DPi-24-Hat display.

### OwnCloud thread

OwnCloud thread is responsible for syncronisation of the captured pictures and videos to the OwnCloud server.

## Hardware

SciFiCamera is an assembly of the three off-the shelf-components: Raspberry Pi 3, Raspberry Pi Camera and 4DPi-24-Hat display. The housing can be 3D printed and features a uCube - compatible modular attachment plate, which can be used to customise an optics adapter for the camera.

## Installation, Maintenance and Testing Guide

### Hardware assembly

1. Follow the instructions for 4DPi-24-Hat on how to setup the display.
2. 3D-print both parts of the housing and five buttons.
3. Attach camera to the bottom part of the housing on the inside using four M2x5mm screws.
4. Attach Raspberry Pi to the bottom part of the housing, pins facing up, with four M2.5 spacers.
5. Connect the Raspberry Pi Camera cable to the Raspberry Pi board.
6. Attach display to the Raspberry Pi and secure with two M2.5 screws.
7. Turn the top parth of the housing upside down and insert the buttons into the slots.
8. While keeping the top part upside down slide in the bottom part.

### Software setup

1. Connect to Pi over ssh or attach a keyboard (you will need to open the housing to do so).
2. Install SciFiCam using pip.
3. Run SciFiCam using ... command.
4. You can create a startup sript so the ... command is launched automatically after Pi boots up.

# Requirements

* pyocclient

## License

MIT
