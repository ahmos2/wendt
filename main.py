#!/usr/bin/python
# -*- coding: utf-8 -*-
from pycanopen import *
from datetime import *
from urllib2 import *
from argparse import *
import urllib,hmac,hashlib

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
    if pkg.data_len<>6:
        sendError(config.company,config.ship,config.controller,config.instance,"Timestamp data length error")
        return
    dayL = list(pkg.data.data)
    daysSince84 = parse16(dayL, 4)

    global prevDS84, prevMsm
    msSinceMidnight = parse32(pkg.data.data, 0)
    print daysSince84,msSinceMidnight

    if prevDS84 <> 0:
        if daysSince84 < prevDS84:
            sendError(config.company,config.ship,config.controller,config.instance,"Timestamp days reduced #nodelorean")
            return
        if daysSince84 > prevDS84 + 1:
            sendError(config.company,config.ship,config.controller,config.instance,"Timestamp day skipped #nodelorean")
            return
        global prevMsm
        if msSinceMidnight < prevMsm and daysSince84 == prevDS84:
            sendError(config.company,config.ship,config.controller,config.instance,"Timestamp millis reduced without day-change #nodelorean")
            return
        if msSinceMidnight == prevMsm and daysSince84 == prevDS84:
            sendError(config.company,config.ship,config.controller,config.instance,"Timestamp duplicated frame")
            return        

    prevDS84=daysSince84
    prevMsm=msSinceMidnight
    

    sendAlive(config.company,config.ship,config.controller,config.instance,daysSince84,msSinceMidnight)

def httpGet(url,sign=True):
    try:
        if sign:
            global signature
            signature=hmac.new(config.privatekey, signature, hashlib.sha512).hexdigest()
            url+='&signature='+signature
        print '<',url
        resp=urlopen(url,cafile="/home/pi/certificate/rootCA.pem")
        str=resp.read()
        print '> ',str
        resp.close()
        return True
    except URLError as error:
        print 'URLError',error,'requesting',url
        return False

def sendAlive(company,ship,controller,instance,day,ms):
    if not errorReportFailed:
        url=config.remotescheme+'://'+config.remotehost+':'+config.remoteport+'/Alive?company='+str(company)+'&ship='+str(ship)+'&controller='+str(controller)+'&instance='+str(instance)+'&day='+str(day)+'&ms='+str(ms)
        if not httpGet(url):
            sendError(company,ship,controller,instance,"One or more alive-reports failed")
    else:
        sendError(company,ship,controller,instance,"One or more error-reports failed")

def sendReset(company,ship,controller,instance):
    if not errorReportFailed:
        url=config.remotescheme+'://'+config.remotehost+':'+config.remoteport+'/Alert?company='+str(company)+'&ship='+str(ship)+'&controller='+str(controller)+'&instance='+str(instance)+'&error=reset'
        if not httpGet(url):
            sendError(company,ship,controller,instance,"Unable to reset")
    else:
        sendError(company,ship,controller,instance,"One or more error-reports failed")

def sendError(company,ship,controller,instance,error):
    global errorReportFailed
    errorReportFailed=True
    url=config.remotescheme+'://'+config.remotehost+':'+config.remoteport+'/Alert?company='+str(company)+'&ship='+str(ship)+'&controller='+str(controller)+'&instance='+str(instance)+'&error='+urllib.quote_plus(error)
    errorReportFailed=not httpGet(url)
def checkNodeIdIsMine(frame,nodeid):
    return int(frame.id & 127) == nodeid

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

parser.add_argument("--privatekey",default="Never gonna give you up")
parser.add_argument("--signature",default="Never gonna let you down")

config=parser.parse_args()

errorReportFailed,prevDS84,prevMsm,signature,previousPkgSendTime,max,pos,lfsSeenCount,lastFrameSent=0,0,0,config.signature,0,0,0,0,0

nmtECData=(c_uint8*8)()
nmtECData[:]=[5,0,0,0,0,0,0,0]
pdo1Data=(c_uint8*8)()
pdo1Data[:]=[0xdb,0x11,0x64,1,0,0,0,0]
personality=[CANopenFrame(function_code=0xe,data=CANopenPayload(data=nmtECData),data_len=1),\
             CANopenFrame(function_code=0x2,data=CANopenPayload(data=pdo1Data),data_len=8),\
             CANopenFrame(function_code=0x2,data=CANopenPayload(data=pdo1Data),data_len=8)]
personalityLengths=[2,3]
print "Config",config

inputBus=CANopen(config.input)
outputBus=CANopen(config.output)
print "inputBus",inputBus,"outputBus",outputBus

sendReset(config.company,config.ship,config.controller,config.instance) # Bootup message
while True:
    if (max not in range(len(personality))) or not pos in range(max):
        pos=0
        max=random.choice(personalityLengths)
    if previousPkgSendTime==0:
        previousPkgSendTime=datetime.now()
        print "ppst reset"
    if (datetime.now()-previousPkgSendTime).total_seconds()>=1:
        print previousPkgSendTime,datetime.now()
        previousPkgSendTime=datetime.now()
        lastFrameSent=personality[pos]
        print (lastFrameSent.function_code<<7)+0x7b8000+config.nodeid
        lastFrameSent.id=(lastFrameSent.function_code<<7)+0x7b8000+config.nodeid
        print lastFrameSent
        outputBus.send_frame(lastFrameSent)
        lfsSeenCount=0
    try:
        frame = inputBus.read_frame()
    except Exception, inst:
        print ('Exception in read_frame:', inst.args)
    if frame:
        if int(frame.id & 127) == 0 and frame.function_code == 2:
            handleTimeStampMsg(frame)
        if (frame == lastFrameSent and lfsSeenCount<>0) or \
         (frame<>lastFrameSent and 
          (checkNodeIdIsMine(frame,config.nodeid))):
            print 'ALERT', frame
            sendError(config.company,config.ship,config.controller,config.instance,'MJOW')
			


