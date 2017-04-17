from unittest import TestCase, TestSuite, main, makeSuite
from fakeclient import FakeClient, GranularityFakeClient, TestError
import os
from datetime import datetime
from oaipmh import common, metadata, validation

directory = os.path.dirname(__file__)
fake1 = os.path.join(directory, 'fake1')
fakeclient = FakeClient(fake1)

fakeclient.getMetadataRegistry().registerReader(
    'oai_dc', metadata.oai_dc_reader)

class ClientTestCase(TestCase):
    
    def test_getRecord(self):
        header, metadata, about = fakeclient.getRecord(
            metadataPrefix='oai_dc', identifier='hdl:1765/315')
        self.assertEqual(
            'hdl:1765/315',
            header.identifier())
        self.assertEqual(
            ['2:7'],
            header.setSpec())
        self.assertTrue(not header.isDeleted())
        
    def test_getMetadata(self):
        metadata = fakeclient.getMetadata(
            metadataPrefix='oai_dc', identifier='hdl:1765/315')
        self.assertEqual(metadata.tag,
                          '{http://www.openarchives.org/OAI/2.0/oai_dc/}dc')

        
    def test_identify(self):
        identify = fakeclient.identify()
        self.assertEqual(
            'Erasmus University : Research Online',
            identify.repositoryName())
        self.assertEqual(
            'http://dspace.ubib.eur.nl/oai/',
            identify.baseURL())
        self.assertEqual(
            '2.0',
            identify.protocolVersion())
        self.assertEqual(
            ['service@ubib.eur.nl'],
            identify.adminEmails())
        self.assertEqual(
            'no',
            identify.deletedRecord())
        self.assertEqual(
            'YYYY-MM-DDThh:mm:ssZ',
            identify.granularity())
        self.assertEqual(
            ['gzip', 'compress', 'deflate'],
            identify.compression())

    def test_listIdentifiers(self):
        headers = fakeclient.listIdentifiers(from_=datetime(2003, 0o4, 10),
                                             metadataPrefix='oai_dc')
        # lazy, just test first one
        headers = list(headers)
        
        header = headers[0]
        self.assertEqual(
            'hdl:1765/308',
            header.identifier())
        self.assertEqual(
            datetime(2003, 4, 15, 10, 18, 51),
            header.datestamp())
        self.assertEqual(
            ['1:2'],
            header.setSpec())
        self.assertTrue(not header.isDeleted())
        self.assertEqual(16, len(headers))


    def test_listIdentifiers_until_none(self):
        # test listIdentifiers with until argument as None explicitly
        headers = fakeclient.listIdentifiers(from_=datetime(2003, 0o4, 10),
                                             until=None,
                                             metadataPrefix='oai_dc')
        self.assertEqual(16, len(list(headers)))

    def test_listIdentifiers_from_none(self):
        # test listIdentifiers with until argument as None explicitly

        # XXX unfortunately a white box test relying on particular
        # exception behavior of the fake server. We do verify whether
        # from or from_ doesn't appear in the request args though
        try:
            headers = fakeclient.listIdentifiers(from_=None,
                                                 metadataPrefix='oai_dc')
        except KeyError as e:
            self.assertEqual('metadataPrefix=oai_dc&verb=ListIdentifiers',
                              e.args[0])
            
    def test_listIdentifiers_argument_error(self):
        self.assertRaises(
            validation.BadArgumentError,
            fakeclient.listIdentifiers,
            foo='bar')
        
    def test_listRecords(self):
        records = fakeclient.listRecords(from_=datetime(2003, 0o4, 10),
                                         metadataPrefix='oai_dc')
        records = list(records)
        # lazy, just test first one
        header, metadata, about = records[0]
        self.assertEqual(
            'hdl:1765/308',
            header.identifier())
        self.assertEqual(
            datetime(2003, 4, 15, 10, 18, 51),
             header.datestamp())
        self.assertEqual(
            ['1:2'],
            header.setSpec())
        self.assertTrue(not header.isDeleted())
        # XXX need to extend metadata tests
        self.assertEqual(
            ['Kijken in het brein: Over de mogelijkheden van neuromarketing'],
            metadata.getField('title'))
            
    def test_listMetadataFormats(self):
        formats = fakeclient.listMetadataFormats()
        metadataPrefix, schema, metadataNamespace = formats[0]
        self.assertEqual(
            'oai_dc',
            metadataPrefix)
        self.assertEqual(
            'http://www.openarchives.org/OAI/2.0/oai_dc.xsd',
            schema)
        self.assertEqual(
            'http://www.openarchives.org/OAI/2.0/oai_dc/',
            metadataNamespace)

    def test_listSets(self):
        expected = [
            ('3', 'Erasmus MC (University Medical Center Rotterdam)', None),
            ('3:5', 'EUR Medical Dissertations', None),
            ]
        # lazy, just compare first two sets..
        sets = fakeclient.listSets()
        sets = list(sets)
        compare = [sets[0], sets[1]]
        self.assertEqual(
            expected,
            compare)

    def test_day_granularity(self):
        fakeclient = GranularityFakeClient(granularity='YYYY-MM-DDThh:mm:ssZ')
        fakeclient.updateGranularity()
        try:
            fakeclient.listRecords(from_=datetime(2003, 0o4, 10, 14, 0),
                                   metadataPrefix='oai_dc')
        except TestError as e:
            self.assertEqual('2003-04-10T14:00:00Z', e.kw['from'])
        fakeclient = GranularityFakeClient(granularity='YYYY-MM-DD')
        fakeclient.updateGranularity()
        try:
            fakeclient.listRecords(from_=datetime(2003, 0o4, 10, 14, 0),
                                   until=datetime(2004, 0o6, 17, 15, 30),
                                   metadataPrefix='oai_dc')
        except TestError as e:
            self.assertEqual('2003-04-10', e.kw['from'])
            self.assertEqual('2004-06-17', e.kw['until'])
            
def test_suite():
    return TestSuite((makeSuite(ClientTestCase), ))

if __name__=='__main__':
    main(defaultTest='test_suite')
