import urllib2
import re
from os.path import join

version = '0.1'
apiVersion = 'EZID API, Version 2'

secureServer = "https://n2t.net/ezid"
testUsername = 'apitest'
testPassword = 'apitest'
ark = 'ark:/'
doi = 'doi:'
testShoulder = ark + '99999/fk4'
testMetadata = {'_target': 'http://example.org/opensociety', 'erc.who': 'Karl Popper', 'erc.what': 'The Open Society and Its Enemies', 'erc.when' : '1945'}


class ApiSession ():
    ''' The ApiSession optionally accepts an EZID API username and password. If none are
    provided, the instance will provide an interface to the test account, providing a default shoulder and metadata.
    '''
    def __init__(self, username=testUsername, password=testPassword):
        if username == testUsername:
            password = testPassword
            self.test = True
        else:
            self.test = False
        authHandler = urllib2.HTTPBasicAuthHandler()
        authHandler.add_password("EZID", secureServer, username, password)
        self.opener = urllib2.build_opener(authHandler)
        # TODO: check login before returning?
        # TODO: what happens if no connection?
 
    # Core api calls
    def mint(self, shoulder=testShoulder, metadata=None):
        ''' Generates and registers a random identifier.
        Accepts a 'shoulder' consisting of a scheme prefix, an assigning authority number, and any other prefix strings.
        eg. 'ark:/99999/osu'
            'doi:10.1959/osu'
        In the case that no scheme prefix is supplied, the 'ark:/' prefix is automatically appendend.
        eg. '99999/osu' -> 'ark:/99999/osu'
        
        If using the apitest account, call as mint() to automatically use the appropriate shoulder.
        
        Optionally, metadata can be passed to the 'metadata' prameter as a dictionary object of names & values.
        '''
        if shoulder == testShoulder and (not self.test):
            raise InvalidIdentifier("Must supply a 'shoulder' identifier prefix when not using the EZID test API.")
        elif not (shoulder.startswith(ark) or shoulder.startswith(doi)):
            shoulder = ark + shoulder
        method = lambda: 'POST'
        requestUri = join(secureServer, 'shoulder', shoulder)
        return self.__callApi(requestUri, method, self.__makeAnvl(metadata))


    def create(self, identifier, metadata=None):
        '''
        Optionally, metadata can be passed to the 'metadata' prameter as a dictionary object of names & values.
        '''
        method = lambda: 'PUT'
        if identifier[0:4] == doi or identifier[0:5] == ark:
            requestUri = join(secureServer, 'id', identifier)
        elif self.test:
            requestUri = join(secureServer, 'id', testShoulder + identifier)
        else:
            raise InvalidScheme('ID scheme must be "' + doi + '" or "' + ark + '".')
        return self.__callApi(requestUri, method, self.__makeAnvl(metadata))

    
    def modify(self, identifier, name, value):
        ''' Accepts an identifier string, a name string and a value string. Writes the name and value as metadata to the provided identifer. 

        The EZID system will store any name/value pair as metadata, but certian names have specific meaning to the system. Some names fit in the metadata profiles explicitly supported by the system, others are reserved as internal data fields.

        Reserved data fields control how EZID manages an identifer. These fields begin with an '_'. More here: http://n2t.net/ezid/doc/apidoc.html#internal-metadata

        To write to the standard EZID metadata fields use name strings of the form [profile].[field] where [profile] is one of 'erc', 'dc', or 'datacite'.
        Example name strings:
          'erc.who'
          'erc.what'
          'erc.when'
          'dc.creator'
          'dc.title'
          'datacite.creator'
          'datacite.title'
          'datacite.publicationyear'
        '''
        method = lambda: 'POST'
        requestUri = join(secureServer, 'id', identifier)
        return self.__callApi(requestUri, method, self.__makeAnvl({name : value}))

    
    def get(self, identifier):
        method = lambda: 'GET'
        requestUri = join(secureServer, 'id', identifier)
        return self.__callApi(requestUri, method, None)
                

    # Public utility functions
    def changeProfile(self, identifier, profile):
        ''' Accepts an identifier string and a profile string where the profile string 
            is one of 'erc', 'datacite', or 'dc'.
            Sets default viewing profile for the identifier as indicated.
        '''
        # profiles = ['erc', 'datacite', 'dc']        
        self.modify(identifier, '_profile', profile) 

    
    def changeTarget(self, identifier, target):
        ''' Accepts an identifier string and a target string.
            Changes the target url for the identifer to the string provided.
        '''
        self.modify(identifier, '_target', target)


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


    def stripIdentifier(self, identifier):
        return identifier

    
    def stripShoulder(self, shoulder):
        return shoulder


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

    
    def __buildId(self, identifier):
        pass


    def __callApi(self, requestUri, requestMethod, requestData):
        request = urllib2.Request(requestUri)
        request.get_method = requestMethod
        request.add_header("Content-Type", "text/plain; charset=UTF-8")
        request.add_data(requestData)
        try:
            response = self.__parseRecord(self.opener.open(request).read())
        except urllib2.HTTPError as e:
            response = e

        return response

class InvalidIdentifier(Exception):
    pass
