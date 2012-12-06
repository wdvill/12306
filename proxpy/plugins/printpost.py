# coding=utf-8

from http import * 
from urlparse import *
from cStringIO import StringIO
from HTMLParser import HTMLParseError
import zlib, string

from sinorail import * 

def proxy_mangle_request(req):
    host, port = req.getHost()
    # if host.endswith("12306.cn") :
        # if req.getMethod() == HTTPRequest.METHOD_GET :
            # print "REQ #%d: GET %s:%d %s" % (req.uid, host, port, req.getPath())
    if req.getMethod() == HTTPRequest.METHOD_POST :
        print "************************************************************"
        print "REQ #%d: POST %s:%d %s" % (req.uid, host, port, req.getPath())
        path = urlparse(req.getPath()).path
        action = path[path.rfind("/")+1:]
        print "\t Action: %s" % action
        reqParams = req.getParams() 
        for (k, v) in reqParams.items() : 
            print "\t %s = %s" % (k, v)
        print "************************************************************"
    return req

def proxy_mangle_response(reqres):
    req, res = reqres.request, reqres.response
    print req
    if is12306(req) and not isTarget(req) :
        return remove_https(res) 
    else :
        return res.serialize() 

# def remove_https(res) :
#     data = StringIO(res.serialize())
#     gzipped, isPage = False, False
#     line = data.readline() 
#     newdata = line 
#     while line != HTTPMessage.EOL :
#         line = data.readline() 
#         newdata += line
#         if line != HTTPMessage.EOL :
#             sep = line.find(':')
#             headname, headcont = line[:sep], line[sep+1:].strip().lower()
#             if headname.strip().lower() == "content-encoding" and headcont.find("gzip") >= 0 :
#                 gzipped = True
#             if headname.strip().lower() == "content-type" and headcont.find("text/html") >= 0 :
#                 isPage = True
#     if not isPage :
#         return res.serialize()
#     if res.isChunked() :
#         chunklen = int(data.readline().strip(), 16)
#         # print "Chunk length: %d" % chunklen
#         chunk = data.read(chunklen)
#         if gzipped :
#             page = zlib.decompress(chunk, 16+zlib.MAX_WBITS)
#         else : 
#             page = chunk
#         parser = RailHttpsParser() 
#         try :
#             parser.feed(page) 
#             if gzipped :
#                 resPage = parser.gzipPage() 
#             else :
#                 resPage = parser.page
#             newdata += "%x" % len(resPage) + HTTPMessage.EOL
#             newdata += resPage + HTTPMessage.EOL
#             newdata += "0" + HTTPMessage.EOL + HTTPMessage.EOL
#         except HTMLParseError as pe :
#             lines = page.split("\n") 
#             print "HTMLParseError: %s, at line %d, column %d" % (pe.msg, pe.lineno, pe.offset) 
#             if pe.lineno > 2 :
#                 i = pe.lineno - 2
#                 for line in lines[pe.lineno-2 : pe.lineno+2] :
#                     print "%4d: %s" % (i, line)
#                     i += 1
#             else: 
#                 i = 0 
#                 for line in lines[0 : pe.lineno+2] :
#                     print "%4d: %s" % (i, line)
#                     i += 1
#             newdata += "%x" % chunklen + HTTPMessage.EOL
#             newdata += chunk + HTTPMessage.EOL
#             newdata += "0" + HTTPMessage.EOL + HTTPMessage.EOL
#     else : 
#         page = data.read()
#         parser = RailHttpsParser()
#         try :
#             parser.feed(page) 
#             newdata += parser.page
#         except HTMLParseError as pe :
#             lines = page.split("\n") 
#             print "HTMLParseError: %s, at line %d, column %d" % (pe.msg, pe.lineno, pe.offset) 
#             if pe.lineno > 2 :
#                 i = pe.lineno - 2
#                 for line in lines[pe.lineno-2 : pe.lineno+2] :
#                     print "%4d: %s" % (i, line)
#                     i += 1
#             else: 
#                 i = 0 
#                 for line in lines[0 : pe.lineno+2] :
#                     print "%4d: %s" % (i, line)
#                     i += 1
#             newdata += page
#     return newdata
