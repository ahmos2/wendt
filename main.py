#!/usr/bin/python
# -*- coding: utf-8 -*-
from pack2parse import *
from argumentHandler import *
from reporting import *
from personality import *
from pycanopen import *
from datetime import *

def calcTsArray():
    now = datetime.datetime.now()
    midnight = datetime.datetime(now.year, now.month, now.day)
    timeSinceMN = pack32(int((now - midnight).total_seconds() * 1000))
    dsL = pack16((datetime.datetime.now() - datetime.datetime(1984, 1, 1)).days)
    dsL.reverse()
    daysSince84 = dsL
    return timeSinceMN + daysSince84

def ArrayToCuint8(array):
    retVal = (c_uint8 * 8)()
    for i in range(6):
        retVal[i] = array[i]
    return retVal

def handleTimeStampMsg(pkg):
    if pkg.data_len<>6:
        sendError(config.company, config.ship, config.controller, config.instance, "Timestamp data length error")
        return
    dayL = list(pkg.data.data)
    daysSince84 = parse16(dayL, 4)

    global prevDS84, prevMsm
    msSinceMidnight = parse32(pkg.data.data, 0)
    print daysSince84, msSinceMidnight

    if prevDS84 <> 0:
        if daysSince84 < prevDS84:
            sendError(config.company, config.ship, config.controller, config.instance, "Timestamp days reduced #nodelorean")
            return
        if daysSince84 > prevDS84 + 1:
            sendError(config.company, config.ship, config.controller, config.instance, "Timestamp day skipped #nodelorean")
            return
        global prevMsm
        if msSinceMidnight < prevMsm and daysSince84 == prevDS84:
            sendError(config.company, config.ship, config.controller, config.instance, "Timestamp millis reduced without day-change #nodelorean")
            return
        if msSinceMidnight == prevMsm and daysSince84 == prevDS84:
            sendError(config.company, config.ship, config.controller, config.instance, "Timestamp duplicated frame")
            return
 
    prevDS84=daysSince84
    prevMsm=msSinceMidnight
    
    sendAlive(config.company, config.ship, config.controller, config.instance, daysSince84, msSinceMidnight)

def checkNodeIdIsMine(frame, nodeid):
    return int(frame.id & 127) == nodeid

def checkNmtRegardsMe(frame, nodeid):
    if frame.function_code<>0 or int(frame.id&127) <> 0:
        return False
    return int(frame.data.data[1])&127==nodeid&127

prevDS84, prevMsm, previousPkgSendTime, max, pos, lfsSeenCount, lastFrameSent = 0, 0, 0, 0, 0, 0, 0

print "Config", config

inputBus=CANopen(config.input)
outputBus=CANopen(config.output)
print "inputBus", inputBus, "outputBus", outputBus

sendReset(config.company, config.ship, config.controller, config.instance) # Bootup message
while True:
    if (max not in range(len(personality))) or not pos in range(max):
        pos=0
        max=random.choice(personalityLengths)
    if previousPkgSendTime==0:
        previousPkgSendTime=datetime.now()
        print "ppst reset"
    if (datetime.now()-previousPkgSendTime).total_seconds()>=1:
        previousPkgSendTime=datetime.now()
        lastFrameSent=personality[pos]
        lastFrameSent.type=1 # Extended
        lastFrameSent.id=(lastFrameSent.function_code<<7)+0x7b8000+config.nodeid

        outputBus.send_frame(lastFrameSent)
        if config.verbose:
            print "Send",lastFrameSent
        lfsSeenCount=0
        pos+=1
    try:
        frame = inputBus.read_frame()
        if config.verbose:
            print "Recv",frame
    except Exception, inst:
        print ('Exception in read_frame:', inst.args)
        sys.exit(-1)
    if frame:
        if int(frame.id & 127) == 0 and frame.function_code == 2:
            handleTimeStampMsg(frame)
        if frame == lastFrameSent:
            lfsSeenCount+=1
        if (frame == lastFrameSent and lfsSeenCount>1) or \
         (frame<>lastFrameSent and 
          (checkNodeIdIsMine(frame, config.nodeid) or
           checkNmtRegardsMe(frame, config.nodeid))):
            print 'ALERT', frame, frame == lastFrameSent, checkNodeIdIsMine(frame, config.nodeid)
            sendError(config.company, config.ship, config.controller, config.instance, 'MJOW')


