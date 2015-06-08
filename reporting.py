def httpGet(url, sign = True):
    try:
        if sign:
            global signature
            signature=hmac.new(config.privatekey, signature, hashlib.sha512).hexdigest()
            url+='&signature='+signature
        print '<', url
        req=Request(url)
        req.add_header("Authorization", "Basic %s" % (base64.b64encode(config.username+":"+config.password)))
        resp=urlopen(req, cafile="../certificate/rootCA.pem")
        str=resp.read()
        print '> ', str
        resp.close()
        return True
    except URLError as error:
        print 'URLError', error, 'requesting', url
        return False

def sendAlive(company, ship, controller, instance, day, ms):
    if not errorReportFailed:
        url=config.remotescheme+'://'+config.remotehost+':'+config.remoteport+'/Alive?company='+str(company)+'&ship='+str(ship)+'&controller='+str(controller)+'&instance='+str(instance)+'&day='+str(day)+'&ms='+str(ms)
        if not httpGet(url):
            sendError(company, ship, controller, instance, "One or more alive-reports failed")
    else:
        sendError(company, ship, controller, instance, "One or more error-reports failed")

def sendReset(company, ship, controller, instance):
    if not errorReportFailed:
        url=config.remotescheme+'://'+config.remotehost+':'+config.remoteport+'/Reset?company='+str(company)+'&ship='+str(ship)+'&controller='+str(controller)+'&instance='+str(instance)
        if not httpGet(url):
            sendError(company, ship, controller, instance, "Unable to reset")
    else:
        sendError(company, ship, controller, instance, "One or more error-reports failed")

def sendError(company, ship, controller, instance, error):
    global errorReportFailed
    errorReportFailed=True
    url=config.remotescheme+'://'+config.remotehost+':'+config.remoteport+'/Alert?company='+str(company)+'&ship='+str(ship)+'&controller='+str(controller)+'&instance='+str(instance)+'&error='+urllib.quote_plus(error)
    errorReportFailed=not httpGet(url)