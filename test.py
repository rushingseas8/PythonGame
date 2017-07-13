# Perlin noise module
#from noise import snoise2

# Curses module for full terminal control
import curses
from curses import wrapper

# Used for debugging timing
import time

# Used for control over random seeds for perlin noise
import random

# Used to detect command line arguments
import sys

# Local imports
from constants import *
import helper
import debug

# Should we enable debug timing and logging? Set on program start.
DEBUG = False

def move(stdscr, deltaX, deltaY):
    width = curses.COLS
    height = curses.LINES

    global xOffset
    global yOffset
    global scale

    # Because of the various conversions, Y needs to be divided by ratio
    # and X needs to be multiplied by 2 to catch up.
    # Specifically, Y needs to move slower per pixel to avoid stretching,
    # and X moves twice as fast to visually keep up with Y pixel motion.
    #yOffset = yOffset + (deltaY * movementSpeed / ratio)
    #xOffset = xOffset + (deltaX * movementSpeed)

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
    if DEBUG == True:
        shiftStart = time.time()
        """
        for i in range(srtY, endY, dirY):
            iTimes = i * width
            for j in range(srtX, endX, dirX):
                index = iTimes + j
                newIndex = index + deltaX + deltaWidth
                landStorage[index] = landStorage[newIndex]
                tempStorage[index] = tempStorage[newIndex]
                biomeStorage[index] = biomeStorage[newIndex]
        """
        if deltaX > 0:
            """
            for index in range((width * height) - deltaX):
                newIndex = index + deltaX
                landStorage[index] = landStorage[newIndex]
                tempStorage[index] = tempStorage[newIndex]
                biomeStorage[index] = biomeStorage[newIndex]
            """
            # By being clever, you can attain O(1) performance on this. 
            # Shifting left/right corresponds to a rotate left/right by N,
            # which a collections.deque can do in O(1).
            # Shifting up/down is a rotate left/right by (width * N); still not bad.
            #
            # However, this slows down random access to O(n), or O(n^3) average
            # for every element in the array. Maybe it's time for two data structures?
            #
            # A deque of deques is also an option- O(1) shifts in all directions, but
            # O(2n) access time worst case.
            for i in range(deltaX):
                landStorage.append(landStorage.pop(0))
                tempStorage.append(tempStorage.pop(0))
                biomeStorage.append(biomeStorage.pop(0))
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
                landStorage[index] = helper.heightLookup(x, y)
                tempStorage[index] = helper.tempLookup(x, y)
                biomeStorage[index] = helper.biomeLookupByTP(tempStorage[index], 0)

        for i in range(genSrtY, genEndY):
            iTimes = i * width
            for j in range(width):
                index = iTimes + j
                x = xOffset + ((j - width / 2) / scale)
                y = yOffset + ((i - height / 2) / scale / ratio)

                landStorage[index] = helper.heightLookup(x, y)
                tempStorage[index] = helper.tempLookup(x, y)
                biomeStorage[index] = helper.biomeLookupByTP(tempStorage[index], 0)
        genEnd = time.time()

        shiftTime = shiftEnd - shiftStart
        genTime = genEnd - genStart

        #TODO: use module 'debug'
        debug.addPercentString("Shift time", shiftTime)
        debug.addPercentString("Generate time", genTime)
    else:
        for i in range(srtY, endY, dirY):
            iTimes = i * width
            for j in range(srtX, endX, dirX):
                index = iTimes + j
                newIndex = index + deltaX + deltaWidth
                landStorage[index] = landStorage[newIndex]
                tempStorage[index] = tempStorage[newIndex]
                biomeStorage[index] = biomeStorage[newIndex]

        for i in range(height):
            iTimes = i * width
            for j in range(genSrtX, genEndX):
                index = iTimes + j
                x = xOffset + ((j - width / 2) / scale)
                y = yOffset + ((i - height / 2) / scale / ratio)

                #TODO add precip to biome
                landStorage[index] = helper.heightLookup(x, y)
                tempStorage[index] = helper.tempLookup(x, y)
                biomeStorage[index] = helper.biomeLookupByTP(tempStorage[index], 0)

        for i in range(genSrtY, genEndY):
            iTimes = i * width
            for j in range(width):
                index = iTimes + j
                x = xOffset + ((j - width / 2) / scale)
                y = yOffset + ((i - height / 2) / scale / ratio)

                landStorage[index] = helper.heightLookup(x, y)
                tempStorage[index] = helper.tempLookup(x, y)
                biomeStorage[index] = helper.biomeLookupByTP(tempStorage[index], 0)

    # Redraw
    drawTimes = simpleRedraw(stdscr)

#TODO: make zooming more efficient by sampling data points into new array,
# then (background?) generate the actual values later. For now, brute force
def zoom(stdscr, mult):
    width = curses.COLS
    height = curses.LINES

    global scale
    global xOffset
    global yOffset

    #if (mult > 1.0 and scale < maxScale) or (mult < 1.0 and scale > minScale):
    scale = scale * mult
    movementSpeed = movementScale / scale

    #scale *= mult

    for i in range(height):
        for j in range(width):
            index = (i * width) + j
            x = xOffset + ((j - width / 2) / scale)
            y = yOffset + ((i - height / 2) / scale / ratio)
            landStorage[index] = helper.heightLookup(x, y)
            tempStorage[index] = helper.tempLookup(x, y)
            biomeStorage[index] = helper.biomeLookupByTP(tempStorage[index], 0)

    simpleRedraw(stdscr)

#TODO: Add precip and biomes to their own lookup tables
def simpleRedraw(stdscr):
    width = curses.COLS
    height = curses.LINES

    if DEBUG == True:
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
                dispChar = helper.floatToCharLand(zValue)
                #dispChar = "#"
                end2 = time.time()
                time2 = time2 + (end2 - start2)

                start3 = time.time()
                color = helper.colorLookup(biome, dispChar)
                #color = curses.color_pair(0)
                #color = 768
                end3 = time.time()
                time3 = time3 + (end3 - start3)

                # Note: Use 'insch' rather than 'addch' to print last column
                start4 = time.time()
                stdscr.insch(i, j, dispChar, color)
                end4 = time.time()
                time4 = time4 + (end4 - start4)
     
        debug.addPercentString("Memory lookup - land", time1)
        debug.addPercentString("Memory lookup - temp", time1b)
        debug.addPercentString("Memory lookup - biome", time1c)
        debug.addPercentString("Float to Char conversion", time2)
        debug.addPercentString("Char color lookup", time3)
        debug.addPercentString("Drawing chars to screen", time4)

    else:
        for i in range(height):
            for j in range(width):
                index = (i * width) + j
                zValue = landStorage[index]
                temp = tempStorage[index]
                biome = helper.biomeLookupByTP(temp, 0)
                dispChar = helper.floatToCharLand(zValue)
                color = helper.colorLookup(biome, dispChar)
                stdscr.insch(i, j, dispChar, color)

    # Here we draw some debugging information in the top-left
    currentWorldX = landXOffset + xOffset
    currentWorldY = landYOffset + yOffset

    currentHeight = helper.heightLookup(xOffset, yOffset)
    currentTemp = helper.tempLookup(xOffset, yOffset)
    currentBiome = helper.biomeLookup(xOffset, yOffset)

    stdscr.addstr(0, 0, "World pos: (" + str(currentWorldX) + ", " + str(currentWorldY) + ") Map pos: (" + str(xOffset * maxScale) + ", " + str(yOffset * maxScale / ratio) + ") Scale: " + str(scale) + "x")
    stdscr.addstr(1, 0, "Height: " + str(currentHeight))
    stdscr.addstr(2, 0, "Biome: " + biomeNames[currentBiome])
    stdscr.addstr(3, 0, "Temperature: " + str(currentTemp))

    # The player in the middle.
    stdscr.addch(height / 2, width / 2, "X")

    # We move the cursor so it's out of the way
    curses.curs_set(0)   
    stdscr.refresh()

def main(stdscr):
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
        #termColorsList[i] = curses.color_pair(i)
        termColorsList.append(curses.color_pair(i))

    #movementSpeed = scale / width / 10

    # Initial setup of the land, temp, biome, and TODO precip storage.    
    for i in range(height):
        for j in range(width):
            x = xOffset + ((j - width / 2) / scale)
            y = yOffset + ((i - height / 2) / scale / ratio)

            index = (i * width) + j
            
            landStorage.append(helper.heightLookup(x, y))
            tempStorage.append(helper.tempLookup(x, y))
            biomeStorage.append(helper.biomeLookupByTP(tempStorage[index], 0))

    # First time drawing to screen.
    simpleRedraw(stdscr)

    # todo: eventually move to a library that supports key pressed/released
    # events to support multiple keys at once working properly
    start_time = 0
    while True:
        # Record any debugging information before waiting. 
        # This is the last possible moment of the previous frame.

        elapsed_time = time.time() - start_time
    
        if DEBUG == True:
            debug.dump(stdscr, {"total_time": elapsed_time})
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
            #TODO: zoom is a bit buggy when moving around a lot
            zoom(stdscr, 2.0)
        elif keyPressed == "-":
            zoom(stdscr, 0.5)
        elif keyPressed == "q":
            break

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if str(sys.argv[1]).lower() == "debug":
            DEBUG = True
    wrapper(main)
