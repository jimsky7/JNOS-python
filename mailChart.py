#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
    Read JNOS AX25 log file and chart the stations that were heard
 
   Debugging:
        Set the variable DEBUG to any non-zero value
        Debug messages will appear in the log file 'mailChart.log'
    
    Hints:
    °   If this is run by cron, it must run as 'root' to manipulate files
    °   Suggested to run hourly near the end of the hour
    55 * * * * sudo python3 /PATH_TO/mailChart.py logFile.log chartOutput.txt logOutput.log CALLSIGN lineLimit bucketLimit
"""

# ====================================================================================
# ====================================================================================

print('========================================================')

import logging, os, sys, time, traceback, io
from mailConfig import *
from logging import *

def bucketName(y, m, d, h):
    hh = str(h)
    if(len(hh) < 2):
        hh = "0" + hh
    hh = hh + "00"
    dd = str(d)
    if(len(dd) < 2):
        dd = "0" + dd
    mm = str(m)
    if(len(mm) < 2):
        mm = "0" + mm
    yy = str(y)
    return yy + "-" + mm + "-" + dd + " " + hh

class ExitNow(Exception):
    pass

BBS_CALLSIGN_STR = ""
PATH_LOGS   = '/Users/sky/Dropbox/aa6ax/Packet_radio/Python/jnos/logs/'
logfilename = ""
limit       = 20000000
maxBuckets  = 36

DEBUG = FALSE

# ====================================================================================
# General items
# If set, these will override mailConfig.py settings
# LIVE   = FALSE
# DEBUG  = TRUE

#   Get these from ARGV[]
ls = len(sys.argv)
if (ls < 3 or ls > 7):
    print("USAGE: filename [mycall] [max-lines-to-read] [max-number-buckets]")
    exit(0)
if (ls==3):
    scriptName, filename, chartfilename = sys.argv
if (ls==4):
    scriptName, filename, chartfilename, BBS_CALLSIGN_STR = sys.argv
if (ls==5):
    scriptName, filename, chartfilename, BBS_CALLSIGN_STR, limit = sys.argv
    limit = int(limit)
if (ls==6):
    scriptName, filename, chartfilename, BBS_CALLSIGN_STR, limit, bucketLimit = sys.argv
    limit = int(limit)
    bucketLimit = int(bucketLimit)
if (ls==7):
    scriptName, filename, chartfilename, logfilename, BBS_CALLSIGN_STR, limit, bucketLimit = sys.argv
    limit = int(limit)
    bucketLimit = int(bucketLimit)

ss = "Analyzing JNOS AX25 log file '{}'".format(filename)
print(ss)

BCS = BBS_CALLSIGN_STR.upper() + " "
while len(BCS)<8:
    BCS = BCS + " "

# ====================================================================================
# Set up logging
scriptPath, scriptName = os.path.split(__file__)
scriptName = scriptName.split('.')[0]
if (DEBUG):
    logLevel = logging.DEBUG
else:
    logLevel = logging.INFO
filen = PATH_LOGS + scriptName + DOT_LOG
if (len(logfilename)):
    filen = logfilename
fx = open(filen,"w")
try:
    logFormat = '%(asctime)-15s %(message)s'
    logging.basicConfig(filename=filen, level=logLevel, format=logFormat)
    log = logging.getLogger(scriptName)
    log.info(BCS+'========================================================')
    log.info(BCS+'========================================================')
    log.info(BCS+'Begin AX25 log analysis.')
    print("Logging to {}".format(filen))
except:
    print('Can\'t set up log file {}. Maybe permissions?'.format(filen))
    # NOTE: Continue even if no log was set up.

#   Convert a time+date string into seconds
#   seconds = time.strptime(string)
#   Convert seconds into string
#   string = time.ctime(seconds)


try:
    try:
        fh = open(filename, "r")
        fo = open(scriptName + DOT_CSV, "w")
        foh= open(scriptName + "-buckets" + DOT_CSV, "w")
        fog= open(chartfilename, "w")
    except:
        traceback.print_tb(sys.exc_info()[2])
        print('Exception: {} {}'.format(sys.exc_info()[0], sys.exc_info()[1]))
        raise ExitNow
    n = limit
    i = 0
    byteCount = "bytes"
    bucketCount = 0
    bucketYear  = 0
    bucketMonth = 0
    bucketDay   = 0
    bucketHour  = 0
    bucketMinute= 0
    bucketCalls = {}
    buckets     = {}
    # All callsigns that transmitted
    callsigns   = {}
    # Callsigns transmitted TO, but not heard yet
    callsignssilent = {}
    callsignssilentcount = {}
    sw = FALSE
    rec = {"date":"date", "time_struct":"time_struct", "seconds":"unixtime", "ax25":"FROM->TO"}
    packetLine1 = ""
    packetLine2 = ""
    packetLine3 = ""
    
    print("Limit: {} lines".format(n))
    while (n > 0 and len(buckets) < bucketLimit):
        try:
            s = fh.readline()
            n = n - 1
            i = i + 1
            # EOF is indicated by empty string
            if (s==""):
                if (DEBUG):
                    print("EOF")
                break
            # If blank line, then prepare for start of new data packet
            if (s == "\n"):
                # Remember the position of the first line in new packet
                bookmark = fh.tell()
                # Process accumulated data for the previous packet
                # When sw is TRUE we are reading data lines until we hit
                #   a blank line.
                sw = TRUE
                # print(rec)
                ts = rec["time_struct"]
                if (rec["seconds"]=="unixtime"):
                    ts = "year","month","day","hour","minute","second"
                cs = rec["ax25"].split("->")
                
                if (i>1):
                    # Check for edgy error condition
                    if (len(cs)==1):
                        cs.append('ERROR')
                    # cs[0] is the transmitting callsign
                    try:
                        callsigns[cs[0]] = callsigns[cs[0]] + byteCount
                    except:
                        callsigns[cs[0]] = byteCount
                    try:
                        bucketCalls[cs[0]] = bucketCalls[cs[0]] + byteCount
                    except:
                        bucketCalls[cs[0]] = byteCount
                    # cs[1] is the TO callsign
                    if (callsigns.get(cs[1], None) != None):
                        # TO callsign has already been heard
                        try:
                            callsignssilent.pop(cs[1], None)
                            callsignssilentcount.pop(cs[1], None)
                        except KeyError:
                            if (DEBUG):
                                print("KeyError [1]")
                    else:
                        # TO callsign has not transmitted yet
                        try:
                            callsignssilentcount[cs[1]] = callsignssilentcount[cs[1]] - 1
                            callsignssilent[cs[1]] = cs[0]
                        except:
                            # No problem
                            callsignssilentcount[cs[1]] = -1
                            callsignssilent[cs[1]] = cs[0]

                        
                # print("cs[0]:{} byteCount:{} total this call: {}".format(cs[0], byteCount,bucketCalls[cs[0]]))
                # print(rec["date"])
                fo.writelines("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t'{}'\t'{}'\t{}\n".format(rec["date"], ts[0], ts[1], ts[2], ts[3], ts[4], ts[5], rec["seconds"], cs[0], cs[1], byteCount))
                # If end of bucket
                if (ts[0] != bucketYear or ts[1] != bucketMonth or ts[2] != bucketDay or ts[3] != bucketHour):
                    # Hourly buckets
                    bn = bucketName(ts[0], ts[1], ts[2], ts[3])
                    if (DEBUG):
                        print("New bucket {}".format(bn))
                    foh.writelines("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(bn, ts[0], ts[1], ts[2], ts[3], ts[4], rec["seconds"], bucketCount))
                    if (len(bucketCalls)):    
                        buckets[bn] = bucketCalls
                        if (DEBUG):
                            print(bucketCalls)
                    bucketCount = 0
                    bucketYear  = ts[0]
                    bucketMonth = ts[1]
                    bucketDay   = ts[2]
                    bucketHour  = ts[3]
                    bucketMinute= ts[4]
                    bucketCalls = {}
                # Get ready for next rec
                rec = {"date":"", "time_struct":"", "seconds":0.0, "ax25":""}
                byteCount = 0
                continue
            # First non-empty line in a packet
            if (len(s)>0 and sw):
                packetLine1 = s.replace("\n", "")
                # First line after a blank is the date indicator
                sd = s.split(" - ")
                # sd[0] is the date+time
                # sd[1] is the interface info
                # print(sd[0])
                sti = time.strptime(sd[0])
                # time since unix epoch
                stm = time.mktime(sti)
                # print(time.ctime(stm))
                rec["date"] = sd[0]
                rec["time_struct"] = sti
                rec["seconds"] = stm
                # Read next line, throw away (KISS...)
                s = fh.readline()
                packetLine2 = s.replace("\n", "")
                # Read AX25 line
                s = fh.readline()
                packetLine3 = s.replace("\n", "")
                if (s.startswith("AX25:")):
                    sc = s.split(" ")
                    # "AX25:","call info","other info"
                    rec['ax25'] = sc[1]
 
                    cs = rec["ax25"].split("->")
                    
                    if (len(cs)==0) or ((len(cs) == 1) and (('\r' in cs[0]) or (cs[0] == ''))) or ((len(cs) > 1) and (('\r' in cs[0]) or ('\r' in cs[1]) or (cs[0] == '') or (cs[1] == ''))):
                        rec['ax25'] = "ERROR->ERROR"
                        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\nBad from->to near line {}. \nPacket will be attributed to "ERROR".'.format(i))
                        print('\t'+packetLine1)
                        print('\t'+packetLine2)
                        print('\t'+packetLine3)
                                    
            sw = FALSE
            # While reading a data packet, count up the bytes
            if (len(s)>1):
                sx = s.split(" ", 18)
                if (len(sx)>16):
                    sx18 = sx[18].strip(" ")
                    sx18 = sx18.strip("\n")
                    lsx18= len(sx18)
                    # print(sx18)
                    byteCount = byteCount + lsx18
                    bucketCount = bucketCount + lsx18

        except:
            print('Exception: {} {} {}'.format(sys.exc_info()[0], sys.exc_info()[1],  sys.exc_info()[2]))
            tbo = sys.exc_info()[2]
            traceback.print_tb(tbo)
            
    # Write Google Charts code
    print("Write Google Chart code")
    s = '["Date" '
    # 'callsigns' is a dictionary containing callsigns and their bytecounts
    # 'callsignlist' is alphabetical list of callsigns
    # 'callsignssilent' is a dictionary of callsigns 'not heard' but which
    #  were sent to.
    # Add the 'unheard' callsigns to the legend with special notation
    for callsign in callsignssilent:
        callsigns["_{}* ({},{})".format(callsign, (callsignssilent[callsign]), (-callsignssilentcount[callsign]))] = callsignssilent[callsign]
    # Make an alphabetical callsign list
    callsignlist = list(callsigns)
    list.sort(callsignlist)
    # Create first row of chart (columne names) (alphabetical)
    for callsign in callsignlist:
        s = s + ', "{}"'.format(callsign)
        # print(callsign)
    s = s + " , { role: 'tooltip' }, { role: 'style' } ],"
    fog.writelines(s+"\n")
    if (DEBUG):
        print(s)
    # Create subsequent rows for the chart (done by date)
    # 'buckets' contains data, one hour per bucket
    # Note: sorted() result is sorted by key, which means date in this case.
    #   It's not necessary (Google Charts can take the data in any order), but
    #   is easier to read when debugging or verifying by human.
    for bucket in sorted(buckets):
        byteCount = 0
        # print("{} » {}".format(bucket, buckets[bucket]))
        # print(bucket)
        ba = bucket.split(" ")
        bb = ba[0].split("-")
        # print(ba)
        # print(bb)
        # Note: month needs to be zero-based
        s = "[ new Date({},{},{},{}),".format(bb[0], int(bb[1])-1, bb[2], int(int(ba[1])/100))
        b = buckets[bucket]
        for callsign in callsignlist:
            # print("Trying: "+callsign)
            try:
                s = s + str(b[callsign]) + ", "
                byteCount = byteCount + b[callsign]
            except:
                s = s + "0, "
        s = s + "'{}', 'color:grey'],".format(byteCount)
        if (DEBUG):
            print(s)
        fog.writelines(s+"\n")
    print(             "{} buckets were processed.".format(len(buckets)))        
    logging.info(BCS + "{} buckets were processed.".format(len(buckets)))                    
            
    fh.close()
    fo.close()
    fog.close()
except ExitNow:
    print('Exiting')
except:
    traceback.print_tb(sys.exc_info()[2])
    print('Exception: {} {}'.format(sys.exc_info()[0], sys.exc_info()[1]))
# ====================================================================================        
# ====================================================================================
      
print(             'All done.')
logging.info(BCS + 'All done.')
print(             '========================================================')
logging.info(BCS + '========================================================')



