import math
import random
import time

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
        countNRun(testArr, i)
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

countTheThing(hashTest)
countTheThing(randTest)
