import unittest

from geniusweb.party.Party import Party


class PartyTest(unittest.TestCase):

    def testPartyDefined(self):
        import random.party
        clas = party.party()
        self.assertTrue(issubclass(clas, Party))
