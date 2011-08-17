#! /usr/bin/python

import urllib2
import re

version = '0.1'
apiVersion = 'EZID API, Version 2'

server = "http://n2t.net/ezid"
secureServer = "https://n2t.net/ezid"
testUsername = 'apitest'
testPassword = 'apitest'
testShoulder = 'ark:/99999/fk4'
testMetadata = {'_target': 'http://example.org/opensociety', 'erc.who': 'Karl Popper', 'erc.what': 'The Open Society and Its Enemies', 'erc.when' : '1945'}

class Api ():
    def __init__(self, username=testUsername, password=testPassword):
        if username == testUsername:
            password = testPassword
            self.test = True
        else:
            self.test = False
        authHandler = urllib2.HTTPBasicAuthHandler()
        authHandler.add_password("EZID", secureServer, username, password)
        self.opener = urllib2.build_opener(authHandler)
 
    # Core api calls
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
                

    # Public utility functions
    def changeProfile(self, identifier, profile):
        # profiles = ['erc', 'datacite', 'dc']
        try:
            self.modify(identifier, '_profile', profile) 
        except:
            raise


    # Private utility functions
    def __makeAnvl(self, metadata):
        """ Accepts a dictionary object containing name value pairs 
            Returns an escaped ANVL string for submission to EZID.
        """
        if metadata == None and self.test == True:
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
            response = e

        return response.read()
