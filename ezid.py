#! /usr/bin/python

import urllib2
import re

server = "http://n2t.net/ezid"
secureServer = "https://n2t.net/ezid"
testUsername = 'apitest'
testPassword = 'apitest'
testShoulder = 'ark:/99999/fk4'
testMetadata = {'_target': 'http://example.org', 'erc.who': 'apitest', 'erc.what': 'A test entry'}

class EzidApiSession ():
    def __init__(self, username=testUsername, password=testPassword):
        if username == testUsername:
            self.test = True
        else:
            self.test = False
        authHandler = urllib2.HTTPBasicAuthHandler()
        authHandler.add_password("EZID", secureServer, username, password)
        self.opener = urllib2.build_opener(authHandler)
 

    def mint(self, shoulder='ark:/99999/fk4', metadata=None):
        method = lambda: 'POST'
        requestUri = secureServer + '/shoulder/' + shoulder
        return self.__callApi(requestUri, method, self.__makeAnvl(metadata))


    def create(self, blade, shoulder='ark:/99999/fk4', metadata=None):
        method = lambda: 'PUT'
        requestUri = secureServer + '/id/' + shoulder + blade
        return self.__callApi(requestUri, method, self.__makeAnvl(metadata))

    
    def modify(self, identifier, name, value):
        method = lambda: 'POST'
        requestUri = secureServer + '/id/' + identifier
        return self.__callApi(requestUri, method, self.__makeAnvl({name : value}))

    
    def getMetadata(self, identifier):
        method = lambda: 'GET'
        requestUri = secureServer + '/id/' + identifier
        return self.__callApi(requestUri, method, None)
                

    def __makeAnvl(self, metadata):
        """ Accepts a dictionary object containing name value pairs 
            Returns an escaped ANVL string for submission to EZID.
        """
        if metadata == None:
            metadata = testMetadata
        #----THIS BLOCK TAKEN WHOLESALE FROM EZID API DOCUMENTATION----#
        # http://n2t.net/ezid/doc/apidoc.html#request-response-bodies
        def escape (s):
            return re.sub("[%:\r\n]", lambda c: "%%%02X" % ord(c.group(0)), s)

        anvl = "\n".join("%s: %s" % (escape(name), escape(value)) for name, value in metadata.items()).encode("UTF-8")
        #----END BLOCK----#

        return anvl


    def __callApi(self, requestUri, requestMethod, requestData):
        request = urllib2.Request(requestUri)
        request.get_method = requestMethod
        request.add_header("Content-Type", "text/plain; charset=UTF-8")
        request.add_data(requestData)
        try:
            response = self.opener.open(request)
        except urllib2.HTTPError as e:
            response = e.read()

        return response.read()


        
