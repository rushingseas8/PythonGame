from noise import snoise2

from math import floor

import time

import curses
from curses import wrapper

from operator import itemgetter

import random
import logging

###
### Global variables used in this program
###

# Constant lookup tables
#global charLookup
global charDict
global colorBasic
global colorDesert
global colorHeatmap
global colorsList
global biomeNames

# It's faster to lookup the chars in a dict than from a string.
charDict = {'~':0, '.':1, ',':2, '-':3, '=':4, '+':5, '*':6, '#':7, '%':8, '@':9}
# int -> char lookup. Use like charTuple[2].
charTuple = tuple(list("~.,-=+*#%@"))


"""
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
global tempStorage
global biomeStorage
global precipStorage

ratio = 9.0 / 16.0
scale = 64.0
minScale = 32.0
maxScale = 4096.0
movementScale = 1.0
movementSpeed = movementScale / scale
termColorsList = []
landStorage = []
tempStorage = []
biomeStorage = []
precipStorage = {}

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
#class Debug:
#    currentCount = 0
#    log = []
#
#    # Adds an arbitrary number of objects as a string to the debug stack.
#    def addString(strings):
#        finalString = ""
#        for s in strings:
#            finalString = finalString + str(s)
#        log.append(finalString)

##TODO: move to a module 'debug'
##TODO: add a heirarchy system; something like Draw.Memory.Land should be 
## displayed as nested inwards. Furthermore, something like Draw should then
## hold the sum of its parts, and should also be displayed separately.
global currentCount
global log
currentCount = 0
log = []

# Adds a new percent string to the debug logger.
# Accepts a descriptive message and a time value- will display a percentage
# of the total time this task took out of all the time between frames.
def addPercentString(msg, val):
    global currentCount
    global log
    log.append((msg, val))
    currentCount += 1

# Prints every debug percentage string we have right now
def dump(stdscr, total_time):
    global currentCount
    global log

    # Sort the log based on the amount of time each element took
    log = sorted(log, key=itemgetter(1), reverse=True)

    # Record the sum of all times recorded
    sumTimes = 0
    for i in range(len(log)):
        msg = log[i][0]
        val = log[i][1]
        sumTimes += val
        stdscr.addstr(i, 0, "[%s] " % "{:06.2%}".format(val / total_time) + str(msg) + " %.4f" % val)

    # Print out "unmeasured time" (any difference between sum of all times and the total time), and total time.
    stdscr.addstr(len(log), 0, "[%s] " % "{:06.2%}".format((total_time - sumTimes) / total_time) + "Unmeasured" + " %.4f" % (total_time - sumTimes))
    stdscr.addstr(len(log) + 1, 0, "[100.0%] Total" + " %.4f" % total_time)

    # Clear the log for next time.
    log = []
    currentCount = 0

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
#def byteToChar(bte):
#    if bte < 0:
#        return "~"
#    return charLookup[int(floor((len(charLookup) - 1) * bte / 255.0))]

# Turns a [-1.0, 1.0) float to an appropriate greyscale character.
#def floatToChar(flt):
#    return byteToChar(floatToByte(flt))

# Turns a [-1.0, 1.0) float to a character, using the land adjustments.
#def floatToCharLand(flt):
#    return byteToChar(floatToByteLand(flt))

# Optimized version of float to char conversion.
# WR2 is the water ratio moved to the [-1.0, 1.0] range;
# WR3 is the ratio to normalize [WR2, 1.0] -> [-1.0, 1.0]. 
#   This is * by len(charLookup) to save a multiplication.
# Note for further optimization: The if statements provide some overhead,
# and the "else" statement is the slowest single statement.
WR2 = (waterRatio * 2.0) - 1.0
WR3 = len(charTuple) / (1.0 - WR2)
def floatToCharLand(flt):
    if flt < WR2:
        return "~"
    #elif flt < -1.0:
        #return charLookup[0]
    #    return "~"
    #elif flt > 1.0:
        #return charLookup[-1]
    #    return "@"
    else:
        return charTuple[int((flt - WR2) * WR3)]
        #return charTuple[int(8 * (flt - WR2) * WR3)]

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
        #return termColorsList[colorsList[biome][charLookup.find(char)]]
        #return 256 * colorsList[biome][charLookup.find(char)]
        #return colorsListExp[(biome * 10) + charLookup.find(char)] << 8
        return termColorsList[colorsList[biome][charDict[char]]]
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

            # First time drawing, set up the initial storage dicts
            if first:
                #landStorage.insert((j * width) + i, zValue)
                landStorage[(j * width) + i] = zValue
                tempStorage[(j * width) + i] = temp
                biomeStorage[(j * width) + i] = biome

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

def move(stdscr, deltaX, deltaY):
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

    srtY = 0
    endY = height - deltaY
    dirY = 1
    genSrtY = height - deltaY
    genEndY = height
    deltaWidth = deltaY * width

    if deltaX < 0:
        srtX = width - 1
        endX = -deltaX - 1
        dirX = -1
        genSrtX = 0
        genEndX = -deltaX

    if deltaY < 0:
        srtY = height - 1
        endY = -deltaY - 1
        dirY = -1
        genSrtY = 0
        genEndY = -deltaY

    # Shift over old values
    shiftStart = time.time()
    for i in range(srtY, endY, dirY):
        iTimes = i * width
        for j in range(srtX, endX, dirX):
            index = iTimes + j
            newIndex = index + deltaX + deltaWidth
            landStorage[index] = landStorage[newIndex]
            tempStorage[index] = tempStorage[newIndex]
            biomeStorage[index] = biomeStorage[newIndex]
    shiftEnd = time.time()

    # Generate new values
    genStart = time.time()
    for i in range(height):
        iTimes = i * width
        for j in range(genSrtX, genEndX):
            index = iTimes + j
            x = xOffset + ((j - width / 2) / scale)
            y = yOffset + ((i - height / 2) / scale / ratio)

            #TODO add precip to biome
            landStorage[index] = heightLookup(x, y)
            tempStorage[index] = tempLookup(x, y)
            biomeStorage[index] = biomeLookupByTP(tempStorage[index], 0)

    for i in range(genSrtY, genEndY):
        iTimes = i * width
        for j in range(width):
            index = iTimes + j
            x = xOffset + ((j - width / 2) / scale)
            y = yOffset + ((i - height / 2) / scale / ratio)

            landStorage[index] = heightLookup(x, y)
            tempStorage[index] = tempLookup(x, y)
            biomeStorage[index] = biomeLookupByTP(tempStorage[index], 0)
    genEnd = time.time()

    shiftTime = shiftEnd - shiftStart
    genTime = genEnd - genStart

    #TODO: use module 'debug'
    addPercentString("Shift time", shiftTime)
    addPercentString("Generate time", genTime)

    # Redraw
    drawTimes = simpleRedraw(stdscr)

#TODO: Add precip and biomes to their own lookup tables
def simpleRedraw(stdscr):
    width = curses.COLS - 1
    height = curses.LINES

    time1 = 0
    time1b = 0
    time1c = 0
    time2 = 0
    time3 = 0
    time4 = 0
    for i in range(height):
        iTimes = i * width
        for j in range(width):
            index = iTimes + j
            #zValue = landStorage[hashScreen(i, j)]

            start1 = time.time()
            zValue = landStorage[index]
            end1 = time.time()
            time1 = time1 + (end1 - start1)

            start1b = time.time()
            temp = tempStorage[index]
            end1b = time.time()
            time1b = time1b + (end1b - start1b)

            start1c = time.time()
            #biome = biomeLookupByTP(temp, 0)
            biome = biomeStorage[index]
            end1c = time.time()
            time1c = time1c + (end1c - start1c)           

            start2 = time.time()
            dispChar = floatToCharLand(zValue)
            #dispChar = "#"
            end2 = time.time()
            time2 = time2 + (end2 - start2)

            start3 = time.time()
            color = colorLookup(biome, dispChar)
            #color = curses.color_pair(0)
            #color = 768
            end3 = time.time()
            time3 = time3 + (end3 - start3)

            start4 = time.time()
            stdscr.addch(i, j, dispChar, color)
            end4 = time.time()
            time4 = time4 + (end4 - start4)

    #TODO: use module 'debug'
    #dump(stdscr)
 
    addPercentString("Memory lookup - land", time1)
    addPercentString("Memory lookup - temp", time1b)
    addPercentString("Memory lookup - biome", time1c)
    addPercentString("Float to Char conversion", time2)
    addPercentString("Char color lookup", time3)
    addPercentString("Drawing chars to screen", time4)

    """
    for i in range(height):
        for j in range(width):
            index = (i * width) + j
            zValue = landStorage[index]
            temp = tempStorage[index]
            biome = biomeLookupByTP(temp, 0)
            dispChar = floatToCharLand(zValue)
            color = colorLookup(biome, dispChar)
            stdscr.addch(i, j, dispChar, color)
    """

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

    f = open("log", "w")

    # Initialize terminal colors and save them for faster lookup later
    for i in range(0, curses.COLORS):
        curses.init_pair(i + 1, i, -1)
        f.write(str(curses.color_pair(i)) + "\n")
        #termColorsList[i] = curses.color_pair(i)
        termColorsList.append(curses.color_pair(i))

    f.close()

    #movementSpeed = scale / width / 10

    for i in range(width):
        for j in range(height):
            landStorage.append(0)
            tempStorage.append(0)
            biomeStorage.append(0)

    redraw(stdscr, True)

    # todo: eventually move to a library that supports key pressed/released
    # events to support multiple keys at once working properly
    start_time = 0
    while True:
        # Record any debugging information before waiting. 
        # This is the last possible moment of the previous frame.

        elapsed_time = time.time() - start_time

        dump(stdscr, total_time=elapsed_time)
        stdscr.addstr(10, 0, "FPS: " + str(1.0 / elapsed_time))
        #stdscr.addstr(10, 0, "Time taken: " + str(elapsed_time))

        keyPressed = stdscr.getkey()

        start_time = time.time()
        if keyPressed == "w":
            #yOffset = yOffset - (movementSpeed * ratio)
            yOffset = yOffset - movementSpeed / ratio
            #move(stdscr, 0, -1)
            move(stdscr, 0, -1)
            #redraw(stdscr)
        elif keyPressed == "s":
            #yOffset = yOffset + (movementSpeed * ratio)
            yOffset = yOffset + movementSpeed / ratio
            #move(stdscr, 0, 1)
            move(stdscr, 0, 1)
            #redraw(stdscr)
        elif keyPressed == "a":
            xOffset = xOffset - movementSpeed * 2.0
            #moveLeftN(stdscr, -1)
            move(stdscr, -2, 0)
            #redraw(stdscr)
        elif keyPressed == "d":
            xOffset = xOffset + movementSpeed * 2.0
            #moveRightN(stdscr, 1)
            move(stdscr, 2, 0)
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
