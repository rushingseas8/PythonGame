###
### This file contains helper methods used in generation and runtime.
###

from constants import *
from noise import snoise2

# Optimized version of float to char conversion.
# Turns a float in the range [-1.0, 1.0) to a char using the lookup tables.
#
# WR2 is the water ratio moved to the [-1.0, 1.0] range;
# WR3 is the ratio to normalize [WR2, 1.0] -> [-1.0, 1.0]. 
#   This is * by len(charLookup) to save a multiplication.
#
# Note for further optimization: The if statements provide some overhead,
# and the "else" statement is the slowest single statement.
WR2 = (waterRatio * 2.0) - 1.0
WR3 = len(charTuple) / (1.0 - WR2)
def floatToCharLand(flt):
    if flt < WR2:
        return "~"
    else:
        return charTuple[int((flt - WR2) * WR3)]

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
# Use biomeLookupByTP() when possible to avoid extra computation.
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
        return termColorsList[colorsList[biome][charDict[char]]]
    except:
        print("Color lookup failed; invalid biome value or character given.")
        raise


# (Experimental) How we store the data per display cell.
def getData(x, y, string):
    return 0
