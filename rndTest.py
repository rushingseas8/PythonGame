import math
import random
import time
import numpy as np
import scipy.stats as spstats

def length(integer):
    if val == 0:
        return 0
    if val < 1.0:
        return int(math.log10(integer)) - 1
    else:
        return int(math.log10(integer)) + 1

def countNRun(arr, n):
    countDict = {}
    for i in range(len(arr) - n):
        string = ""
        for j in range(i, min(i + n, len(arr))):
            string += str(arr[j])
        if string in countDict:
            countDict[string] += 1
        else:
            countDict[string] = 1

    """
    print (str(n) + "-length run results:"),
    for key in countDict:
        #print key, "(" + str(countDict[key]) + "|" + str(int(((len(arr) - n) / (2 ** n)))) + ")",
        print key, "(E:" + str(int(((len(arr) - n) / (2 ** n)))) + "|A:" + str(countDict[key]) + ")",
    print
    """

    chiSquare = 0
    for key in countDict:
        expect = int((len(arr) - n) / (2 ** n))
        actual = countDict[key]
        chiSquare += ((expect - actual) ** 2) / float(expect)
    degrees = (2 ** n) - 1
    print(str(n) + "-length chi-square results: X^2=" + str(chiSquare) + ", degrees=" + str(degrees))

def countNRunDir(fun, startX, startY, dx, dy, dist, n):
    # Generate values according to the parameter rules.
    vals = []
    for i in range(dist):
        vals.append(fun(startX + (dx * i), startY + (dy * i)) & 1)

    # Go through the generated values and count runs of length n
    countDict = {}
    for i in range(dist - n):
        string = ""
        for j in range(i, min(i + n, dist)):
            string += str(vals[j])

        if string in countDict:
            countDict[string] += 1
        else:
            countDict[string] = 1 

    # Debug: prints the key/vals
    #for key in countDict:
    #    print(key, countDict[key])

    # Chi square test on the data
    chiSquare = 0
    expected = float(len(vals) - n) / (2 ** n)
    for key in countDict:
        actual = countDict[key]
        chiSquare += ((expected - actual) ** 2) / expected

    # Accounting for the values that never showed up
    # (expected - 0)^2 / expected
    for i in range((2 ** n) - len(countDict)):
        chiSquare += expected

    degrees = (2 ** n) - 1
    p = spstats.chi2.sf(chiSquare, degrees)

    #print(str(n) + "-length chi-square, % chance this is random: " + str(p))
    return p

baseX = 1912
baseY = -1923
def countTheThing(fun):
    countFalse = 0
    countTrue = 0
    testArr = []
    startTime = time.time()
    for i in range(baseX - 20, baseX + 20):
        for j in range(baseY - 20, baseY + 20):
            val = fun(i, j)
            val = val & 1
            testArr.append(val)
            if val == 0:
                countFalse += 1
            else:
                countTrue += 1
            #print val,
        #print
    endTime = time.time()
    #print("Num true: " + str(countTrue) + ", num false: " + str(countFalse))
    for i in range(10):
        #countNRun(testArr, (39, 39)), i)
        countNRunDir(fun, baseX, baseY, 1, 0, 100, i)
    print("Elapsed time: " + str(endTime - startTime))

const1 = 1823912412 | 1
const2 = 125672
const3 = 74732422
const4 = 626731 | 1
const5 = 2919999123
const6 = 2669191923
const7 = 982934890   

def hashTest(x, y):
    val = x
    val *= const1
    #val += const2
    #val = (val >> 16) + (val << 16)
    #val ^= const3
    val += y
    val *= const4
    #val += const5
    val = (val >> 16) + (val << 16)
    val ^= const6
    #val *= const7 | 1
    return val

random.seed(120)
def randTest(x, y):
    val = int(random.random() * 2)
    return val

#countTheThing(hashTest)
#countTheThing(randTest)

"""
print("Random baseline.")
randCount = 0
randTotal = 0
for i in range(1, 10):
    p = countNRunDir(randTest, baseX, baseY, 1, 0, 100, i)
    if p < 0.05:
        print("Possibly not random on test (%d, %d, %d, %d, %d, %d) with p=%d", (baseX, baseY, 1, 0, 100, i, p))
    elif p > 0.05:
        randCount += 1
    randTotal += 1
print("Passed " + str(randCount) + "/" + str(randTotal) + " tests. (" + str(100.0 * randCount / randTotal) + "%)")

print("Hash test.")
hashCount = 0
hashTotal = 0
for i in range(1, 10):
    p = countNRunDir(hashTest, baseX, baseY, 1, 0, 100, i)
    if p < 0.05:
        print("Likely not random on (baseX=%d, baseY=%d, dx=%d, dy=%d, cnt=%d, n=%d) with p=%f" % (baseX, baseY, 1, 0, 100, i, p))
    elif p > 0.05:
        hashCount += 1
    hashTotal += 1
print("Passed " + str(hashCount) + "/" + str(hashTotal) + " tests. (" + str(100.0 * hashCount / hashTotal) + "%)")
"""

def testSuite(fun):
    print("Running test suite on \"%s\"." % fun.__name__)
    count = 0
    total = 0

    for dx in range(-10, 11):
        for dy in range(-10, 11):
            for i in range(1, 10):
                p = countNRunDir(fun, baseX, baseY, dx, dy, 100, i)
                if p > 0.05:
                    count +=1
                total += 1

    """
    for i in range(1, 10):
        p = countNRunDir(fun, baseX, baseY, 1, 0, 100, i)
        if p < 0.05:
            print("[%s] Likely not random on (baseX=%d, baseY=%d, dx=%d, dy=%d, cnt=%d, n=%d) with p=%f" % (fun.__name__, baseX, baseY, 1, 0, 100, i, p))
        elif p > 0.05:
            count += 1
        total += 1

    for i in range(1, 10):
        p = countNRunDir(fun, baseX, baseY, 0, 1, 100, i)
        if p < 0.05:
            print("[%s] Likely not random on (baseX=%d, baseY=%d, dx=%d, dy=%d, cnt=%d, n=%d) with p=%f" % (fun.__name__, baseX, baseY, 0, 1, 100, i, p))
        elif p > 0.05:
            count += 1
        total += 1       
    """
    print("Passed " + str(count) + "/" + str(total) + " tests. (" + str(100.0 * count / total) + "%)")   

testSuite(randTest)
testSuite(hashTest)
