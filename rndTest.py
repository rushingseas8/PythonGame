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

    #print(str(n) + "-length chi-square for \"This is not random\": p=" + str(p))
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

def sample(fun):
    for i in range(baseX - 20, baseX + 20):
        for j in range(baseY - 20, baseY + 20):
            #val = fun(i, j) & 1
            print fun(i, j) & 1,
        print

const9 = 2654435761 * 2654435761 * 2654435761 * 2654435761

# This is a winner!
def hashTest(x, y):
    return (x * x * y * y * const9) >> 32

def randTest(x, y):
    random.seed((long(x) << 16) + y)
    return int(random.random() * 2)

#countTheThing(hashTest)
#countTheThing(randTest)

def testSuite(fun):
    print("Running test suite on \"%s\"." % fun.__name__)
    count = 0
    total = 0

    testStart = time.time()
    random.seed(100)
    for k in range(50):
        baseX = int(-5000 + (random.random() * 10000))
        baseY = int(-5000 + (random.random() * 10000))
        
        # Most randomness issues are clear after hops up to length 5.
        for dx in range(-5, 6):
            for dy in range(-5, 6):
                for i in range(1, 5):
                    p = countNRunDir(fun, baseX, baseY, dx, dy, 100, i)
                    if p > 0.05:
                        count +=1
                    total += 1

    testEnd = time.time()
    if total > 0:
        print("Passed " + str(count) + "/" + str(total) + " tests (" + str(100.0 * count / total) + "%). Took " + str(testEnd - testStart) + "s.")   

testSuite(randTest)
testSuite(hashTest)
