import unittest
import ezid_api

creator = 'ezid_api.py tests'

class EzidApiTests(unittest.TestCase):
    
    def setUp(self):
        self.arkSession = ezid_api.ApiSession()
        self.doiSession = ezid_api.ApiSession(scheme='doi')
        self.ark = self.arkSession.mint()
        self.doi = self.doiSession.mint()
        # store any ids we make so we can be sure to delete them later
        self.ids = [self.ark, self.doi]

    def test_mint(self):
        ark = self.arkSession.mint()
        self.ids.append(ark)
        self.assertTrue(ark.startswith(ezid_api.schemes['ark']))
        doi = self.doiSession.mint()
        self.ids.append(doi)
        self.assertTrue(doi.startswith(ezid_api.schemes['doi']))

    def test_create(self):
        tail = 'PYEZID'
        ark = self.arkSession.create(tail)
        self.ids.append(ark)
        self.assertEqual(ark, ezid_api.schemes['ark'] + ezid_api.testShoulder[ezid_api.schemes['ark']] + tail)
        doi = self.doiSession.create(tail)
        self.ids.append(doi)
        self.assertTrue(doi.startswith(ezid_api.schemes['doi'] + ezid_api.testShoulder[ezid_api.schemes['doi']] + tail))

    def test_delete(self):
        ark = self.arkSession.mint()
        deleteArk = self.arkSession.delete(ark)
        self.assertEqual(deleteArk, ark)

    def test_get(self):
        arkGet = self.arkSession.get(self.ark)
        self.assertEqual(arkGet['identifier'], self.ark)
        self.assertTrue('metadata' in arkGet)

    def test_modify(self):
        arkGet = self.arkSession.get(self.ark)
        updated = arkGet['metadata']['_updated']
        self.arkSession.modify(self.ark, 'dc.creator', creator)
        arkGet = self.arkSession.get(self.ark)
        self.assertTrue(arkGet['metadata']['_updated'] > updated)
        self.assertEqual(arkGet['metadata']['dc.creator'], creator)
        

    def test_scheme_setter(self):
        self.assertEqual(self.arkSession.scheme, ezid_api.schemes['ark'])
        self.arkSession.setScheme('doi')
        self.assertEqual(self.arkSession.scheme, ezid_api.schemes['doi'])
        self.arkSession.setScheme('ark')
        self.assertEqual(self.arkSession.scheme, ezid_api.schemes['ark'])

    def test_naa_setter(self):
        self.assertEqual(self.arkSession.naa, ezid_api.testShoulder[ezid_api.schemes['ark']])
        self.arkSession.setNAA(ezid_api.testShoulder[ezid_api.schemes['doi']])
        self.assertEqual(self.arkSession.naa, ezid_api.testShoulder[ezid_api.schemes['doi']])
        self.arkSession.setNAA(ezid_api.testShoulder[ezid_api.schemes['ark']])
        self.assertEqual(self.arkSession.naa, ezid_api.testShoulder[ezid_api.schemes['ark']])

    def tearDown(self):
        for i in self.ids:
            try:
                self.arkSession.delete(i)
            except:
                pass

if __name__ == '__main__':
    unittest.main()
        
