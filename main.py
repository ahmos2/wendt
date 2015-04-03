#!/usr/bin/python
# -*- coding: utf-8 -*-
from pycanopen import *
from datetime import *
from urllib2 import *
from argparse import *

def parse16(array, offset):
    return (array[offset + 1] << 8) + array[offset]

def parse32(array, offset):
    return (parse16(array, offset + 2) << 16) + parse16(array, offset)

def pack16(data):
    return [data & 255, data >> 8]

def pack32(data):
    return pack16(data & 0xffff) + pack16(data >> 16)

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
    if pkg.data.length<>6:
        sendError(args.company,args.ship,args.controller,args.instance,"Timestamp data length error")
        return
    dayL = list(pkg.data.data)
    daysSince84 = parse16(dayL, 4)

    global prevDS84
    if daysSince84 < prevDS84:
        sendError(args.company,args.ship,args.controller,args.instance,"Timestamp days reduced #nodelorean")
        return
    if daysSince84 > prevDS84 + 1:
        sendError(args.company,args.ship,args.controller,args.instance,"Timestamp day skipped #nodelorean")
        return
    dayL.reverse()
    msSinceMidnight = parse32(pkg.data.data, 0)

    global prevMsm
    if msSinceMidnight < prevMsm and daysSince84 == prevDS84:
        sendError(args.company,args.ship,args.controller,args.instance,"Timestamp millis reduced without day-change #nodelorean")
        return
        
    prevDS84=daysSince84
    prevMsm=msSinceMidnight
    

    sendAlive(args.company,args.ship,args.controller,args.instance,daysSince84,msSinceMidnight)

def httpGet(url):
    try:
        print '<',url
        resp=urllib2.urlopen(url)
        print '> ',resp
        resp.close()
    except urllib2.URLError as error:
        print 'URLError',error,'requesting',url

def sendAlive(company,ship,controller,instance,day,ms):
    url=config.remotescheme+'://'+config.remotehost+':'+config.remoteport+'/Alive?company='+str(company)+'&ship='+str(ship)+'&controller='+str(controller)+'&instance='+str(instance)+'&day='+str(day)+'&ms='+str(ms)
    httpGet(url)

def sendError(company,ship,controller,instance,error):
    url=config.remotescheme+'://'+config.remotehost+':'+config.remoteport+'/Error?company='+str(company)+'&ship='+str(ship)+'&controller='+str(controller)+'&instance='+str(instance)+'&error='+error
    httpGet(url)


parser = ArgumentParser()
parser.add_argument("--remotescheme", default="https")
parser.add_argument("--remotehost", default="128.39.165.228")
parser.add_argument("--remoteport", default="8080")

parser.add_argument("--input",help="Ingoing canbus to sensor", default="vcan0")
parser.add_argument("--output",help="Outgoing canbus to network", default="vcan0")

parser.add_argument("--company", type=int, default=0)
parser.add_argument("--ship", type=int, default=0)
parser.add_argument("--controller", type=int, default=0)
parser.add_argument("--instance", type=int, default=0)

parser.add_argument("--nodeid", type=int, default=99)

config=parser.parse_args()

inputBus=CANopen(config.input)
outputBus=CANopen(config.output)

while True:
    try:
        frame = inputBus.read_frame()
    except Exception, inst:
        print ('Exception in read_frame:', inst.args)
    if frame:
        if int(frame.id & 127) == 0 and frame.function_code == 2:
            handleTimeStampMsg(frame)
        if int(frame.id & 127) == canid or (int(frame.id&127==0) and frame.function_code==0 and frame.data.data[1]==config.nodeid):
            print 'ALERT', frame, frame.id & 127, frame.function_code
            sendError(args.company,args.ship,args.controller,args.instance,'MJOW')
			
