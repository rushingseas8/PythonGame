from operator import itemgetter

### A file containing methods that help with logging debugging information.

# A list containing tuples of (message, time) for percent logging
percentLog = []

# A list of all regular information strings.
infoLog = []

def addInfoString(msg):
    global infoLog
    infoLog.append(msg)

def addPercentString(msg, val):
    global percentLog

    percentLog.append((msg, val))

# Dump all of the current strings to the provided output window.
# @param infoDict: a dictionary containing data needed to draw the debug info.
#   Current required data is below:
#   - "total_time": elapsed time in the last update
def dump(stdscr, infoDict):
    global infoLog
    global percentLog

    total_time = infoDict["total_time"]

    # Display the info first.
    rowCount = 0
    for i in range(len(infoLog)):
        stdscr.addstr(rowCount, 0, infoLog[i])
        rowCount += 1

    if len(infoLog) > 0:
        rowCount += 1

    # Sort the log based on the amount of time each element took
    percentLog = sorted(percentLog, key=itemgetter(1), reverse=True)

    # Record the sum of all times recorded
    sumTimes = 0
    for i in range(len(percentLog)):
        msg = percentLog[i][0]
        val = percentLog[i][1]
        sumTimes += val
        stdscr.addstr(
            rowCount,
            0,
            "[%s] " % "{:06.2%}".format(val/total_time) + msg + " %.4f" % val)
        rowCount += 1

    # Print out "unmeasured time" (any difference between sum of all times and the total time), and total time.
    stdscr.addstr(
        rowCount,
        0,
        ("[%s] " % "{:06.2%}".format((total_time - sumTimes) / total_time) +
        " Unmeasured " +
        "%.4f" % (total_time - sumTimes)))
    rowCount += 1

    stdscr.addstr(rowCount,0,"[100.0%] Total" + " %.4f" % total_time)

    # Clear the log for next time.
    infoLog = []
    percentLog = []
