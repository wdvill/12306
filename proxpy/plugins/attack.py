# coding=utf-8

from http import * 
from urlparse import *
from cStringIO import StringIO
import zlib
# import sys, tty, termios

from sinorail import * 

def proxy_mangle_request(req):
    isTargetReq = False
    host, port = req.getHost()
    if host.endswith("12306.cn") :
        if req.getMethod() == HTTPRequest.METHOD_POST :
            path = urlparse(req.getPath()).path
            action = path[path.rfind("/")+1:]
            reqParams = req.getParams() 
            if action == "confirmPassengerAction.do" and reqParams["method"] == "payOrder" :
                isTargetReq = True
                print "************************************************************"
                print "Capture target request (REQ #%d)" % req.uid
                print "POST %s:%d %s" % (host, port, req.getPath())
                print "Order sequence NO: %s" % reqParams["orderSequence_no"]
                print "Train NO: %s" % reqParams["orderRequest.station_train_code"]
                print "From %s (%s) to %s (%s)" % (reqParams["orderRequest.from_station_name"],
                                                   reqParams["orderRequest.from_station_telecode"],
                                                   reqParams["orderRequest.to_station_name"], 
                                                   reqParams["orderRequest.to_station_telecode"]
                                                   )
                print "Date: %s, departure at %s, arrive at %s" % (reqParams["orderRequest.train_date"], 
                                                                   reqParams["orderRequest.start_time"], 
                                                                   reqParams["orderRequest.end_time"]
                                                                   )
                i = 1
                while ("passenger_"+str(i)+"_name") in reqParams :
                    prefix = "passenger_"+str(i)
                    print "Passenger %d: %s, %s, %s" % (i, 
                                                        reqParams[prefix+"_name"],
                                                        reqParams[prefix+"_cardno"],
                                                        seat_type(reqParams[prefix+"_seat"])
                                                        )
                    i = i+1
                print "************************************************************"
            elif action == "myOrderAction.do" and reqParams["method"] == "laterEpay":
                isTargetReq = True 
                print "************************************************************"
                print "Capture target request (REQ #%d): POST %s:%d %s" % (req.uid, host, port, req.getPath())
                print "Order sequence NO: %s" % reqParams["orderSequence_no"]
                print "************************************************************"
    return (req, isTargetReq)

def proxy_mangle_response(res):
    data = StringIO(res.serialize())
    newdata = "" 
    line = data.readline() 
    while line != HTTPMessage.EOL :
        # print line
        newdata += line
        line = data.readline() 
    newdata += line
    if res.isChunked() :
        chunklen = int(data.readline().strip(), 16)
        # print "Chunk length: %d" % chunklen
        chunk = data.read(chunklen)
        page = zlib.decompress(chunk, 16+zlib.MAX_WBITS)
        parser = RailActiveParser() 
        parser.feed(page) 
        gzipPage = parser.gzipPage()
        newdata += "%x" % len(gzipPage) + HTTPMessage.EOL
        newdata += gzipPage + HTTPMessage.EOL
        newdata += "0" + HTTPMessage.EOL + HTTPMessage.EOL
    else : 
        page = data.read()
        parser = RailActiveParser()
        parser.feed(page) 
        newdata += parser.page 
    
    return newdata
