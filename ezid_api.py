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

    
    def get(self, identifier):
        method = lambda: 'GET'
        requestUri = secureServer + '/id/' + identifier
        return self.__callApi(requestUri, method, None)
                

    # Public utility functions
    def changeProfile(self, identifier, profile):
        ''' Accepts an identifier string and a profile string where the profile string 
            is one of 'erc', 'datacite', or 'dc'.
            Sets default viewing profile for the identifier as indicated.
        '''
        # profiles = ['erc', 'datacite', 'dc']        
        self.modify(identifier, '_profile', profile) 


    def recordModify(self, identifier, meta, clear=False):
        ''' Accepts an identifier string, a dictionary object containing name-value pairs
            for metadata, and a boolean flag ('clear').
            Writes name value pairs to the EZID record. If clear flag is true, deletes 
            (i.e. sets to '') all names not assigned a value in the record passed in. 
            Internal EZID metadata is ignored by the clear process so, eg. '_target' or 
            '_coowner' must be overridden manually.
            Returns the record, same as get().
            
            Note: Because the EZID API offers no interface for full record updates, this 
            method makes an api call--through modify()--for each name-value pair updated.
        '''
        if clear:
            #TODO: code in clear old metadata
            oldMeta = self.get(identifier)
        for k in meta.keys():
            self.modify(identifier, k, meta[k])
        return self.get(identifier)


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
    
    
    def __parseRecord(self, ezidResponse):
        print ezidResponse
        record = {}
        parts = ezidResponse.split('\n')
        # first item is 'success: [identifier]'
        identifier = parts[0].split(': ')[1]
        metadata = {}
        if len(parts) > 1:
            for p in parts[1:]:
                pair = p.split(': ')
                if len(pair) == 2:
                    metadata[str(pair[0])] = pair[1]
            record = {'identifier' : identifier, 'metadata' : metadata}
        else:
            record = identifier
        return record


    def __callApi(self, requestUri, requestMethod, requestData):
        request = urllib2.Request(requestUri)
        request.get_method = requestMethod
        request.add_header("Content-Type", "text/plain; charset=UTF-8")
        request.add_data(requestData)
        try:
            response = self.__parseRecord(self.opener.open(request).read())
        except urllib2.HTTPError as e:
            response = e.mint()

        return response
