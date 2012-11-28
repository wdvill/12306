from http import * 

def proxy_mangle_request(req):
    # if req is None :
    #     return 
    host, port = req.getHost()
    if host.endswith("12306.cn") :
        # if req.getMethod() == HTTPRequest.METHOD_GET :
            # print "REQ #%d: GET %s:%d %s" % (req.uid, host, port, req.getPath())
        if req.getMethod() == HTTPRequest.METHOD_POST :
            print "************************************************************"
            print "REQ #%d: POST %s:%d %s" % (req.uid, host, port, req.getPath())
            # print req.body
            for (k, v) in req.getParams().items() : 
                print "\t %s = %s" % (k, v)
            print "************************************************************"
    return req

def proxy_mangle_response(res):
    # print res
    return res
