# coding=utf-8

from HTMLParser import HTMLParser
from base64 import *
from cStringIO import StringIO
import xml.etree.ElementTree as ET
import sys, tty, termios, gzip

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

    def handle_starttag(self, tag, attrs) :
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

        self.page += self.get_starttag_text() 
        return 

    def handle_endtag(self, tag) :
        self.page += "</" + tag + ">"
        if self.inOrderTable :
            if tag.lower() == "tr" :
                self.parsedTabRows += 1
                if self.parsedTabRows > 2 :
                    self.passengerList.append(self.passenger)
                self.parsingPassenger = False 
                self.passenger = "" 
                self.passengerField = 0
        return 

    def handle_startendtag(self, tag, attrs):
        self.page += self.get_starttag_text() 
        return 

    def handle_data(self, data) :
        self.page += data 
        if (not self.inOrderTable) :
            if data == "订单信息" :
                self.inOrderTable = True
        else: # parsing ticket order 
            if data.startswith("总票价") :
                self.inOrderTable = False
                self.parsingPassenger = False 
                self.passenger = "" 
                # self.order.amount = data.strip()
                i = 1 
                for p in self.passengerList :
                    print "%2d: %s" % (i, p) 
                    i += 1
                print data.strip() 
            elif self.parsedTabRows >= 2 and self.parsingPassenger :
                if data.strip() != "" :
                    self.passengerField += 1
                    if self.passengerField > 3 :
                        self.passenger += data.replace("\t", "").replace("\r","").replace("\n","").replace(" ","") + ", " 
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
                    return 
        if self.inOrderTable :
            if tag.lower() == "tr" :
                if self.parsedTabRows >= 2 : 
                    self.parsingPassenger = True 

        self.page += self.get_starttag_text() 
        return 

    def gzipPage(self) :
        if self.page == "" :
            return ""
        buf = StringIO() 
        zfile = gzip.GzipFile(mode="wb", fileobj=buf)
        zfile.write(self.page) 
        zfile.close()
        return buf.getvalue()

