from operator import itemgetter

### A file containing methods that help with logging debugging information.

# The current count of strings in the percentLog
currentCount = 0

# A list containing tuples of (message, time) for percent logging
percentLog = []

def addPercentString(msg, val):
    global currentCount
    global percentLog

    percentLog.append((msg, val))
    currentCount += 1

def dump(stdscr, infoDict):
    global currentCount
    global percentLog

    total_time = infoDict["total_time"]

    # Sort the log based on the amount of time each element took
    percentLog = sorted(percentLog, key=itemgetter(1), reverse=True)

    # Record the sum of all times recorded
    sumTimes = 0
    for i in range(len(percentLog)):
        msg = percentLog[i][0]
        val = percentLog[i][1]
        sumTimes += val
        stdscr.addstr(
            i,
            0,
            "[%s] " % "{:06.2%}".format(val/total_time) + msg + " %.4f" % val)

    # Print out "unmeasured time" (any difference between sum of all times and the total time), and total time.
    stdscr.addstr(
        len(percentLog),
        0,
        ("[%s] " % "{:06.2%}".format((total_time - sumTimes) / total_time) +
        " Unmeasured " +
        "%.4f" % (total_time - sumTimes)))

    stdscr.addstr(len(percentLog) + 1,0,"[100.0%] Total" + " %.4f" % total_time)

    # Clear the log for next time.
    percentLog = []
    currentCount = 0
