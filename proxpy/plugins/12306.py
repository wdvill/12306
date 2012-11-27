# coding=utf-8

from http import * 
from urlparse import *

def seat_type(no) :
    if no == "0" :
        return "二等座"
    if no == "1" :
        return "硬座"
    if no == "3" :
        return "硬卧"
    if no == "4" :
        return "软卧"
    if no == "9" :
        return "商务座"
    if no == "M" :
        return "一等座"

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
                print "Password: %s" % reqParams['user.password'] 
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
            # for (k, v) in req.getParams().items() : 
            #     print "\t %s = %s" % (k, v)
            print "************************************************************"
    return (req, isTargetReq)

def proxy_mangle_response(res):
    return res
