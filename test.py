#coding: utf-8
from noise import pnoise2
from noise import snoise2

from math import floor

import time

import curses
from curses import wrapper

import random

###
### Global variables used in this program
###

# Constant lookup tables
global charLookup
global colorBasic
global colorDesert
global colorHeatmap
global colorsList
global biomeNames

charLookup = "~.,-=+*#%@"
colorBasic   = [40, 179, 95, 23, 29, 41, 47, 248, 232, 190]
colorDesert  = [46, 95, 173, 179, 215, 216, 217, 218, 95, 35]
colorSnow    = [112, 240, 248, 249, 251, 253, 254, 232, 190, 184]
colorHeatmap = [23, 35, 47, 107, 185, 179, 173, 167, 161, 166]
colorsList = [colorBasic, colorDesert, colorSnow]

"""
colorBasic   = (40, 179, 95, 23, 29, 41, 47, 248, 232, 190)
colorDesert  = (46, 95, 173, 179, 215, 216, 217, 218, 95, 35)
colorSnow    = (112, 240, 248, 249, 251, 253, 254, 232, 190, 184)
colorHeatmap = (23, 35, 47, 107, 185, 179, 173, 167, 161, 166)
colorsList = (colorBasic, colorDesert, colorSnow)
"""
biomeNames = ["Plains", "Desert", "Snow"]

# Used to store information about the world (to prevent constant recomputation)
global worldHeight
global worldTemp
global worldPrecip

worldHeight = []
worldTemp = []
worldPrecip = []

# Variables needed for controlling major game mechanics
global ratio
global scale
global minScale
global maxScale
global movementScale
global movementSpeed
global termColorsList
global landStorage

ratio = 9.0 / 16.0
scale = 64.0
minScale = 32.0
maxScale = 4096.0
movementScale = 1.0
movementSpeed = movementScale / scale
termColorsList = {}
landStorage = {}

# World generation details
global randomSeed
global landXOffset
global landYOffset
global tempXOffset
global tempXOffset
global wetYOffset
global wetYOffset
global waterRatio

randomSeed = 10
random.seed(randomSeed)
landXOffset = random.random() * 10000
landYOffset = random.random() * 10000
tempXOffset = random.random() * 10000
tempYOffset = random.random() * 10000
wetXOffset = random.random() * 10000
wetYOffset = random.random() * 10000
waterRatio = 0.45

# Player-specific statistics
global xOffset
global yOffset

xOffset = 0
yOffset = 0

###
### Helper functions generally used in this program
### (these don't typically rely on changing variables)
###

## Debug class.
## TODO: Make some sensical way of keeping track of strings on the screen;
## this means updating them with values that change (fps, position, etc)
## as well as ensuring they stay in the same order between updates.
## The contract should state that the order is arbitrary but consistent.
class Debug:
    log = []

    # Adds an arbitrary number of objects as a string to the debug stack.
    def addString(strings):
        finalString = ""
        for s in strings:
            finalString = finalString + str(s)
        log.append(finalString)

    # Prints all the debug strings to the provided screen.
    def dump(stdscr):
        for i in range(len(log)):
            stdscr.addstr(i, 0, log[i])

# Converts a float in the range [-1.0, 1.0] to a byte in the range [0, 255].
def floatToByte(flt):
    flt = (flt + 1.0) / 2.0
    if flt > 1.0:
        return 255
    return floor(flt * 256.0)

# Converts a float in the range [-1.0, 1.0] to a byte in the range [0, 255].
# Additionally, all floats with a normalized range below "waterRatio" will
# return -1 with this method- this is used to color water separately.
#
# All values in the norm. range [waterRatio, 1.0) are stretched to the range
# [0, 1.0) before being turned into a byte as normal.
def floatToByteLand(flt):
    # Normalize into range [0, 1.0)
    flt = (flt + 1.0) / 2.0
    if flt < waterRatio:
        return -1

    # Normalize [waterRatio, 1.0) -> [0, 1.0)
    flt = (flt - waterRatio) / (1 - waterRatio)

    # Return [0, 255] range
    if flt > 1.0:
        return 255
    return floor(flt * 256.0)

# Looks up a byte's value in the character greyscale table.
# That is to say, values near 0 map to " "; near 255 map to "@", etc.
def byteToChar(bte):
    if bte < 0:
        return "~"
    return charLookup[int(floor((len(charLookup) - 1) * bte / 255.0))]

# Turns a [-1.0, 1.0) float to an appropriate greyscale character.
def floatToChar(flt):
    return byteToChar(floatToByte(flt))

# Turns a [-1.0, 1.0) float to a character, using the land adjustments.
#def floatToCharLand(flt):
#    return byteToChar(floatToByteLand(flt))

# Optimized version of float to char conversion.
# WR2 is the water ratio moved to the [-1.0, 1.0] range;
# WR3 is the ratio to normalize [WR2, 1.0] -> [-1.0, 1.0].
# Note for further optimization: The if statements provide some overhead,
# and the "else" statement is the slowest single statement.
WR2 = (waterRatio * 2.0) - 1.0
WR3 = 1.0 / (1.0 - WR2)
def floatToCharLand(flt):
    if flt < WR2:
        return "~"
    elif flt < -1.0:
        return charLookup[0]
    elif flt > 1.0:
        return charLookup[-1]
    else:
        return charLookup[int(len(charLookup) * (flt - WR2) * WR3)]

# This runs several iterations of perlin noise and sums the values.
def octaves(x, y, iterations=1, scale=1.0, pers=2.0, normalize=True):
    value = 0
    maxValue = 0
    amp = 1.0
    for i in range(int(iterations)):
        value = value + (snoise2(x * scale, y * scale) * amp)
        maxValue = maxValue + amp
        amp = amp / pers
        scale = scale * 2.0

    if normalize:
        return value / (maxValue / 1.33)
    else:
        return value

# Returns the height of the land given any (x, y) coordinate.
def heightLookup(x, y):
    return octaves(landXOffset + x, landYOffset + y, iterations=8)

# Given an (x, y) coordinate, returns the temperature of that area.
def tempLookup(x, y):
    return octaves(tempXOffset + x, tempYOffset + y, iterations=1, scale=1/4.0, pers=2, normalize=True)

# Given an (x, y) coordinate, returns the precipitation of that area.
def precipLookup(x, y):
    return 0

# Returns the biome found at the given (x, y) coordinate.
def biomeLookup(x, y):
    temp = tempLookup(x, y)
    precip = precipLookup(x, y)
    return biomeLookupByTP(temp, precip)

# Returns an integer representing the biome, given temp. and percip.
def biomeLookupByTP(temp, percip):
    if temp < 0:
        return 2
    elif temp > 0.5:
        return 1
    else:
        return 0

# Provides the appropriate color given a biome and character.
# This looks up biome -> colorscheme; colorscheme -> color.
# Note on optimization: try/except is faster when expected to succeed.
# An if/else would always check, so ends up giving a significant penalty here.
def colorLookup(biome, char):
    try:
        #index = charLookup.find(char)
        #index = 0
        #return curses.color_pair(colorsList[biome][charLookup.find(char)])
        return termColorsList[colorsList[biome][charLookup.find(char)]]
    except:
        print("Color lookup failed; invalid biome value or character given.")
        raise

# Creates a hash value to access a screen (x, y) coordinate in the dict
def hashScreen(x, y):
    return str(x) + "#" + str(y)

###
### Main methods used in the program. These depend on above variables/methods
###

def redraw(stdscr, first=False):
    width = curses.COLS - 1
    height = curses.LINES

    global scale

    for i in range(width):
        for j in range(height):
            x = xOffset + ((i - width / 2) / scale)
            y = yOffset + ((j - height / 2) / scale / ratio)

            zValue = heightLookup(x, y)
            temp = tempLookup(x, y)
            biome = biomeLookupByTP(temp, 0)

            # First time drawing, set up the dict
            if first:
                #landStorage[hashScreen(i, j)] = zValue
                landStorage[(j * width) + i] = zValue

            # TODO: move the array and only update the values that are new
            # on the very edges. Don't update the entire 2D array every time
            #arrayIndex = (y * width) + x

            dispChar = floatToCharLand(zValue)
            #dispChar = floatToChar(temp)
            color = colorLookup(0, dispChar)

            stdscr.addch(j, i, dispChar, color)
            #stdscr.addch(j, i, floatToChar(snoise2((xOffset + i) / scale, (yOffset + j) / ratio / scale)), curses.color_pair(1))

    # Here we draw some debugging information in the top-left
    currentWorldX = landXOffset + xOffset
    currentWorldY = landYOffset + yOffset

    currentHeight = heightLookup(xOffset, yOffset)
    currentTemp = tempLookup(xOffset, yOffset)
    currentBiome = biomeLookup(xOffset, yOffset)

    stdscr.addstr(0, 0, "World pos: (" + str(currentWorldX) + ", " + str(currentWorldY) + ") Map pos: (" + str(xOffset * maxScale) + ", " + str(yOffset * maxScale / ratio) + ") Scale: " + str(scale) + "x")
    stdscr.addstr(1, 0, "Height: " + str(currentHeight))
    stdscr.addstr(2, 0, "Biome: " + biomeNames[currentBiome])
    stdscr.addstr(3, 0, "Temperature: " + str(currentTemp))

    # The player in the middle.
    stdscr.addch(height / 2, width / 2, "X")

    # We move the cursor so it's out of the way
    curses.curs_set(0)

    stdscr.refresh()

def moveRightN(stdscr, deltaX):
    width = curses.COLS - 1
    height = curses.LINES

    global xOffset
    global yOffset
    global scale

    shiftStart = time.time()
    # Shift values over
    deltaWidth = deltaX * width
    for i in range(0, width - deltaX):
        for j in range(height):
            index = (j * width) + i
            #landStorage[hashScreen(i, j)] = landStorage[hashScreen(i + deltaX, j)]
            landStorage[index] = landStorage[deltaWidth + index]
    shiftEnd = time.time()

    genStart = time.time()
    # Generate new values
    for i in range(width - deltaX, width):
        for j in range(height):
            index = (j * width) + i
            x = xOffset + ((i - width / 2) / scale)
            y = yOffset + ((j - height / 2) / scale / ratio)

            #landStorage[hashScreen(i, j)] = heightLookup(x, y)
            landStorage[index] = heightLookup(x, y)
    genEnd = time.time()

    drawStart = time.time()
    simpleRedraw(stdscr)
    drawEnd = time.time()

    stdscr.addstr(0, 0, "Shift time: " + str(shiftEnd - shiftStart))
    stdscr.addstr(1, 0, "Generate time: " + str(genEnd - genStart))
    stdscr.addstr(2, 0, "Draw time: " + str(drawEnd - drawStart))

def moveLeftN(stdscr, deltaX):
    width = curses.COLS - 1
    height = curses.LINES

    global xOffset
    global yOffset
    global scale

    shiftStart = time.time()
    # Shift values over
    for i in range(width, -deltaX, -1):
        for j in range(height):
            landStorage[(j * width) + i] = landStorage[(j * width) + i + deltaX]
    shiftEnd = time.time()

    genStart = time.time()
    # Generate new values
    for i in range(0, -deltaX):
        for j in range(height):
            x = xOffset + ((i - width / 2) / scale)
            y = yOffset + ((j - height / 2) / scale / ratio)

            landStorage[(j * width) + i] = heightLookup(x, y)

    simpleRedraw(stdscr)

## TODO: moving left broke for some reason; add in moving vertically
def moveX(stdscr, deltaX):
    width = curses.COLS - 1
    height = curses.LINES

    global xOffset
    global yOffset
    global scale

    srtX = 0
    endX = width - deltaX
    dirX = 1
    genSrtX = width - deltaX
    genEndX = width
    deltaWidth = deltaX * width

    if deltaX < 0:
        srtX = width
        endX = 0#-deltaX
        dirX = -1
        genSrtX = 0
        genEndX = 0#deltaX

    # Shift over old values
    shiftStart = time.time()
    for i in range(srtX, endX, dirX):
        #iTimes = i * height
        for j in range(height):
            #index = iTimes + j
            index = (j * width) + i
            landStorage[index] = landStorage[index + deltaX]
    shiftEnd = time.time()

    # Generate new values
    genStart = time.time()
    for i in range(genSrtX, genEndX):
        #iTimes = i * height
        for j in range(height):
            #index = iTimes + j
            index = (j * width) + i
            x = xOffset + ((i - width / 2) / scale)
            y = yOffset + ((j - height / 2) / scale / ratio)

            landStorage[index] = heightLookup(x, y)
    genEnd = time.time()

    # Redraw
    drawStart = time.time()
    simpleRedraw(stdscr)
    drawEnd = time.time()

    stdscr.addstr(0, 0, "Shift time: " + str(shiftEnd - shiftStart))
    stdscr.addstr(1, 0, "Generate time: " + str(genEnd - genStart))
    stdscr.addstr(2, 0, "Draw time: " + str(drawEnd - drawStart))

def simpleRedraw(stdscr):
    width = curses.COLS - 1
    height = curses.LINES

    # Below is debugging code with times for everything
    """
    time1 = 0
    time2 = 0
    time3 = 0
    time4 = 0
    for i in range(width):
        iTimes = i * width
        for j in range(height):
            index = iTimes + j
            #zValue = landStorage[hashScreen(i, j)]

            start1 = time.time()
            zValue = landStorage[index]
            end1 = time.time()
            time1 = time1 + (end1 - start1)

            start2 = time.time()
            dispChar = floatToCharLand(zValue)
            #dispChar = "#"
            end2 = time.time()
            time2 = time2 + (end2 - start2)

            start3 = time.time()
            color = colorLookup(0, dispChar)
            end3 = time.time()
            time3 = time3 + (end3 - start3)

            start4 = time.time()
            stdscr.addch(j, i, dispChar, color)
            end4 = time.time()
            time4 = time4 + (end4 - start4)

    stdscr.addstr(2, 0, "Draw time: " + str(time1 + time2 + time3 + time4))
    stdscr.addstr(3, 0, "\t Memory lookup: " + str(time1))
    stdscr.addstr(4, 0, "\t Float to disp char: " + str(time2))
    stdscr.addstr(5, 0, "\t Color lookup: " + str(time3))
    stdscr.addstr(6, 0, "\t Actual drawtime: " + str(time4))
    """

    for i in range(width):
        #iTimes = i * width
        for j in range(height):
            #index = iTimes + j
            index = (j * width) + i
            zValue = landStorage[index]
            dispChar = floatToCharLand(zValue)
            color = colorLookup(0, dispChar)
            stdscr.addch(j, i, dispChar, color)

def main(stdscr):
    #snoise2 is what we need to use
    #ideal ratio is roughly 1.9:1, but 16:9 works well

    global ratio
    global scale
    global xOffset
    global yOffset
    global movementSpeed

    width = curses.COLS
    height = curses.LINES

    curses.start_color()
    curses.use_default_colors()

    # Initialize terminal colors and save them for faster lookup later
    for i in range(0, curses.COLORS):
        curses.init_pair(i + 1, i, -1)
        termColorsList[i] = curses.color_pair(i)

    #movementSpeed = scale / width / 10

    redraw(stdscr, True)

    # todo: eventually move to a library that supports key pressed/released
    # events to support multiple keys at once working properly
    start_time = 0
    while True:
        elapsed_time = time.time() - start_time
        stdscr.addstr(8, 0, "FPS: " + str(1.0 / elapsed_time))
        keyPressed = stdscr.getkey()
        start_time = time.time()
        if keyPressed == "w":
            yOffset = yOffset - movementSpeed * ratio
            #move(stdscr, 0, -1)
            redraw(stdscr)
        elif keyPressed == "s":
            yOffset = yOffset + movementSpeed * ratio
            #move(stdscr, 0, 1)
            redraw(stdscr)
        elif keyPressed == "a":
            xOffset = xOffset - movementSpeed
            moveLeftN(stdscr, -1)
            #moveX(stdscr, -1)
            #redraw(stdscr)
        elif keyPressed == "d":
            xOffset = xOffset + movementSpeed
            #moveRightN(stdscr, 1)
            moveX(stdscr, 1)
            #redraw(stdscr)
        elif keyPressed == "=":
            if scale < maxScale:
                scale = scale * 2.0
                movementSpeed = movementScale / scale
                redraw(stdscr)
        elif keyPressed == "-":
            if scale > minScale:
                scale = scale / 2.0
                movementSpeed = movementScale / scale
                redraw(stdscr)
        elif keyPressed == "q":
            break

if __name__ == "__main__":
    wrapper(main)
