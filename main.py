#!/usr/bin/python
# -*- coding: utf-8 -*-
from pycanopen import *
import datetime,urllib2

input = CANopen('vcan0')
output = CANopen('can0')


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
    dsL = pack16((datetime.datetime.now() - datetime.datetime(1984, 1,
                 1)).days)
    dsL.reverse()
    daysSince84 = dsL
    return timeSinceMN + daysSince84


def ArrayToCuint8(array):
    retVal = (c_uint8 * 8)()
    for i in range(6):
        retVal[i] = array[i]
    return retVal

def sendAlive(company,ship,controller,instance,day,ms):
    url='http://128.39.165.228:8080/Alive?company='+str(company)+'&ship='+str(ship)+'&controller='+str(controller)+'&instance='+str(instance)+'&day='+str(day)+'&ms='+str(ms)
    print '<',url
    resp=urllib2.urlopen(url)
    print '> ',resp
    resp.close()

while True:
    try:
        frame = input.read_frame()
    except Exception, inst:
        print ('Exception in read_frame:', inst.args)
    if frame:
        if int(frame.id & 127) == 0 and frame.function_code == 2:
            dayL = list(frame.data.data)
            daysSince84 = parse16(dayL, 4)
            dayL.reverse()
            msSinceMidnight = parse32(frame.data.data, 0)
            sendAlive(0,0,0,0,daysSince84,msSinceMidnight)
            payload = CANopenPayload(data=ArrayToCuint8(calcTsArray()))
            frame2send = CANopenFrame(function_code=2, id=99,data_len=6, data=payload, type=1)
            print '<', frame2send
            output.send_frame(frame2send)
        if int(frame.id & 127) == 99:
            print 'ALERT', frame, frame.id & 127, frame.function_code

			
