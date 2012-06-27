import urllib2
import re
from os.path import join

version = '0.1'
apiVersion = 'EZID API, Version 2'

secureServer = "https://n2t.net/ezid"
testUsername = 'apitest'
testPassword = 'apitest'
schemes = {'ark': 'ark:/', 'doi': "doi:"}
private = "reserved"
public = "public"
unavail = "unavailable"
testShoulder = {schemes['ark'] : '99999/fk4', schemes['doi'] : '10.5072/FK2'}
testMetadata = {'_target': 'http://example.org/opensociety', 'erc.who': 'Karl Popper', 'erc.what': 'The Open Society and Its Enemies', 'erc.when' : '1945'}


class ApiSession ():
    ''' The ApiSession optionally accepts an EZID API username and password. 

    Also accepts a scheme (either "ark" or "doi"), and a assigning authority number.
    Defaults to test account on with scheme and prefix: ark:/99999/fk4
    '''
    def __init__(self, username=testUsername, password=testPassword, scheme="ark", naa=''):
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
        self.setScheme(scheme[0:3])
        # if we are testing, use the test shoulder for the given scheme
        if self.test == True:
            naa = testShoulder[self.scheme]
        self.setNAA(naa)
 
    # Core api calls
    def mint(self, metadata={}):
        ''' Generates and registers a random identifier using the id scheme and name assigning authority already set.
        Optionally, metadata can be passed to the 'metadata' prameter as a dictionary object of names & values.
        Minted identifiers are always created with a status of "reserved".
        '''
        shoulder = self.scheme + self.naa
        metadata['_status'] = private
        method = lambda: 'POST'
        requestUri = join(secureServer, 'shoulder', shoulder)
        return self.__callApi(requestUri, method, self.__makeAnvl(metadata))


    def create(self, identifier, metadata={}):
        '''
        Optionally, metadata can be passed to the 'metadata' prameter as a dictionary object of names & values.
        '''
        if not "_status" in metadata:
            metadata["_status"] = private
        method = lambda: 'PUT'
        if not identifier.startswith(schemes['doi']) and not identifier.startswith(schemes['ark']):
            identifier = self.scheme + self.naa + identifier
        requestUri = join(secureServer, 'id', identifier)

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

    def delete(self, identifier):
        method = lambda: 'DELETE'
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

    def getStatus(self, identifier):
        return self.get(identifier)['metadata']['_status']
        
    def makePublic(self, identifier):
        return self.modify(identifier, '_status', public)

    def makeUnavailable(self, identifier):
        return self.modify(identifier, '_status', unavail)

    def getTarget(self, identifier):
        return self.get(identifier)['metadata']['_target']
    
    def changeTarget(self, identifier, target):
        ''' Deprecated: currently an alias for modifyTarget()
        '''
        self.modifyTarget(identifier, target)

    def modifyTarget(self, identifier, target):
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
            #TODO: clear old metadata
            oldMeta = self.get(identifier)
        for k in meta.keys():
            self.modify(identifier, k, meta[k])
        return self.get(identifier)

    def setScheme(self, scheme):
        self.scheme = schemes[scheme]
            
    def setNAA(self, naa):
        self.naa = naa

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
            response = e.read()

        return response

class InvalidIdentifier(Exception):
    pass
    
    
