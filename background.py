#---------------------------------------------------------------------------------------
# Purpose: Windows will not allow a multi-monitor environment to to cycle through
#     backgrounds individually for each screen.
#
# Usage:
#   - No parameters
#   - Libraries required to download:
#       - PIL (Python Image Library)
#       - enum
#   - Create two folders, named hb (horizontal background) and vb (vertical background).
#     Put all landscape backgrounds in hb, and all portrait backgrounds in vb
#     The Script will automatically determine if each screen is horizontal or vertical.
#     For landscape screens, portrait backgrounds will NOT be used.
#
# TODO:
#   - Find a way to save a screenshot into memory in order to eliminate the created
#     current_wallpaper.jpg
#   - Have a scrolling wallpaper option
#   - Support gifs
#   - Detect new screens (and modified screens) to change wallpapers immediately
#---------------------------------------------------------------------------------------

import ctypes
import os
import time
import imghdr
import random
from PIL import Image
from enum import Enum
import StringIO
user = ctypes.windll.user32

def GetNumOfMonitors():
    SM_CMONITORS = 80
    return user.GetSystemMetrics(SM_CMONITORS)

def ChangeBackground(imagePath):
    SPI_SETDESKWALLPAPER = 20
    user.SystemParametersInfoA(SPI_SETDESKWALLPAPER, 0, imagePath, 1)

class Orientation(Enum):
    landscape = 1
    portrait = 2

# RECT implementation for python
class RECT(ctypes.Structure):
    _fields_ = [
        ('left', ctypes.c_long),
        ('top', ctypes.c_long),
        ('right', ctypes.c_long),
        ('bottom', ctypes.c_long)]
    def dump(self):
        return map(int, (self.left, self.top, self.right, self.bottom))

# MONITORINFO implementation for python
class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ('cbSize', ctypes.c_long),
        ('rcMonitor', RECT),
        ('rcWork', RECT),
        ('dwFlags', ctypes.c_long)]

class MonitorWrapper:
    def __init__(self, monitorInfo):
        self.x = monitorInfo[1][0]
        self.y = monitorInfo[1][1]
        self.width = monitorInfo[1][2] - self.x
        self.height = monitorInfo[1][3] - self.y
        self.view = Orientation.landscape
        if self.width < self.height:
            self.view = Orientation.portrait
        self.fullImageLibrary = self.findImages()   # fullImageLibrary is always constant.  currentImageLibrary will delete each picture
        self.currentImageLibrary = []
        for image in self.fullImageLibrary:
            self.currentImageLibrary.append(image)  # that will be used as a background, and reset to rullImageLibrary when empty
        random.shuffle(self.currentImageLibrary)

    def findImages(self):
        workingDir = os.getcwd()                # gets current working directory of script
        if self.view == Orientation.landscape:
            workingDir = workingDir + '\\hb'
        else:
            workingDir = workingDir + '\\vb'
        dirFilesList = os.listdir(workingDir)   # gets all files in current working directory
        retval = []
        for dirFile in reversed(dirFilesList):  # parse out everything that's not an image
            if dirFile.find('.') == -1:
                dirFilesList.remove(dirFile)    # No permissions to access folders
            elif imghdr.what(workingDir + '\\' + dirFile) == None:
                dirFilesList.remove(dirFile)
            else:
                retval.append(workingDir + '\\' + dirFile)
        return retval

    def popImage(self):
        if not self.fullImageLibrary:           # There are no appropriate images, so return a black background
            return Image.new("RGB", (100, 100), "black")
        if not self.currentImageLibrary:        # Repopulate currentImageLibrary if empty
            for image in self.fullImageLibrary:
                self.currentImageLibrary.append(image)
            random.shuffle(self.currentImageLibrary)
        imageDir = self.currentImageLibrary.pop()
        retval = Image.open(imageDir)           # Open next picture to be used as background
        return retval.resize((self.width, self.height)) # Resize picture to size of current screen

# Gets size of all monitors by using EnumDisplayMonitors (see MSDN)
def get_monitors():
    retval = []
    CBFUNC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_long, ctypes.c_long, ctypes.POINTER(RECT), ctypes.c_double)
    def cb(hMonitor, hdcMonitor, lprcMonitor, dwData):
        r = lprcMonitor.contents
        data = [hMonitor]
        data.append(r.dump())
        retval.append(data)
        return 1
    cbfunc = CBFUNC(cb)
    temp = user.EnumDisplayMonitors(0, 0, cbfunc, 0)
    return retval

def monitor_areas():
    retval = []
    monitors = get_monitors()
    for hMonitor, extents in monitors:
        data = [hMonitor]
        mi = MONITORINFO()
        mi.cbSize = ctypes.sizeof(MONITORINFO)
        mi.rcMonitor = RECT()
        mi.rcWork = RECT()
        res = user.GetMonitorInfoA(hMonitor, ctypes.byref(mi))
        data.append(mi.rcMonitor.dump())
        data.append(mi.rcWork.dump())
        retval.append(data)
    return retval

if __name__ == "__main__":
    monitorList = []
    for monitor in monitor_areas():
        monitorList.append(MonitorWrapper(monitor))

    # Creating a new image for background
    def canvasSize():
        left = monitorList[0].x
        right = monitorList[0].x + monitorList[0].width
        top = monitorList[0].y
        bottom = monitorList[0].y + monitorList[0].height
        for i in range(len(monitorList) - 1):
            if monitorList[i+1].x < left:
                left = monitorList[i+1].x
            if monitorList[i+1].x + monitorList[i+1].width > right:
                right = monitorList[i+1].x + monitorList[i+1].width
            if monitorList[i+1].y < top:
                top = monitorList[i+1].y
            if monitorList[i+1].y + monitorList[i+1].height > bottom:
                bottom = monitorList[i+1].y + monitorList[i+1].height
        return (left, top, right - left, bottom - top)
    temp = canvasSize()
    referencePoint = temp[0:2]
    canvas = Image.new("RGB", temp[2:4], "black")

    while True:
        for monitor in monitorList:
            canvas.paste(monitor.popImage(), (monitor.x-temp[0], monitor.y-temp[1]))

        #currentBackground = StringIO.StringIO()
        #canvas.save(currentBackground, 'JPEG')
        #contents = currentBackground.getvalue()
        #print contents
        #ChangeBackground(contents)
        #time.sleep(2)

        canvas.save('Current_background.jpg')
        ChangeBackground(os.getcwd() + '\\' + 'Current_background.jpg')
        time.sleep(0.5)
