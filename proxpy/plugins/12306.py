# coding=utf-8

from http import * 
from urlparse import *
from cStringIO import StringIO
import zlib

from sinorail import * 

def proxy_mangle_request(req):
    isTargetReq = False
    host, port = req.getHost()
    if host.endswith("12306.cn") :
        # if req.getMethod() == HTTPRequest.METHOD_GET :
            # print "REQ #%d: GET %s:%d %s" % (req.uid, host, port, req.getPath())
        if req.getMethod() == HTTPRequest.METHOD_POST :
            print "************************************************************"
            print "REQ #%d: POST %s:%d %s" % (req.uid, host, port, req.getPath())
            path = urlparse(req.getPath()).path
            action = path[path.rfind("/")+1:]
            reqParams = req.getParams() 
            if action == "loginAction.do" and reqParams['method'] == 'login': 
                print "User name: %s" % reqParams['loginUser.user_name'] 
                print "Password: ******" 
            elif action == "querySingleAction.do" and reqParams["method"] == "submutOrderRequest" :
                print "Train NO: %s" % reqParams["station_train_code"]
                print "From %s (%s) to %s (%s)" % (reqParams["from_station_telecode_name"],
                                                   reqParams["from_station_telecode"],
                                                   reqParams["to_station_name"], 
                                                   reqParams["to_station_telecode"]
                                                   )
                print "Date: %s, departure at %s, arrive at %s" % (reqParams["train_date"], 
                                                                   reqParams["train_start_time"], 
                                                                   reqParams["arrive_time"]
                                                                   )
            elif action == "confirmPassengerAction.do" and reqParams["method"] == "confirmSingleForQueueOrder" :
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
            elif action == "confirmPassengerAction.do" and reqParams["method"] == "payOrder" :
                isTargetReq = True
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
            elif action == "myOrderAction.do" and reqParams["method"] == "laterEpay":
                isTargetReq = True 
                print "Order sequence NO: %s" % reqParams["orderSequence_no"]
            # for (k, v) in req.getParams().items() : 
            #     print "\t %s = %s" % (k, v)
            print "************************************************************"
    return (req, isTargetReq)

def proxy_mangle_response(res):
    data = cStringIO.StringIO(res.serialize())
    line = data.readline() 
    while line != HTTPMessage.EOL :
        line = data.readline() 
    if res.isChunked() :
        chunklen = int(data.readline().strip(), 16)
        # print "Chunk length: %d" % chunklen
        chunk = data.read(chunklen)
        page = zlib.decompress(chunk, 16+zlib.MAX_WBITS)
        parser = RailParser() 
        parser.feed(page) 
    else : 
        page = data.read()
        parser = RailParser()
        parser.feed(page) 
    return res
