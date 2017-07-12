## A class containing all sorts of constants and variables used throughout the program.

import random

## Constant lookup tables
# It's faster to lookup the chars in a dict than from a string.
charDict = {'~':0, '.':1, ',':2, '-':3, '=':4, '+':5, '*':6, '#':7, '%':8, '@':9}

# int -> char lookup. Use like charTuple[2].
charTuple = tuple(list("~.,-=+*#%@"))

colorBasic   = (40, 179, 95, 23, 29, 41, 47, 248, 232, 190)
colorDesert  = (46, 95, 173, 179, 215, 216, 217, 218, 95, 35)
colorSnow    = (112, 240, 248, 249, 251, 253, 254, 232, 190, 184)
colorHeatmap = (23, 35, 47, 107, 185, 179, 173, 167, 161, 166)
colorsList = (colorBasic, colorDesert, colorSnow)
biomeNames = ["Plains", "Desert", "Snow"]

## Variables needed for controlling major game mechanics
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
xOffset = 0
yOffset = 0
