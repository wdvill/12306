# coding=utf-8

from http import * 
from urlparse import *

def proxy_mangle_request(req):
    isTargetReq = False
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
    return (req, isTargetReq)

def proxy_mangle_response(res):
    return res
