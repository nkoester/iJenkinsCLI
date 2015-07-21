import unittest


class JenkinsJobBrowserTest(unittest.TestCase):

    def testSomething(self):
        # TODO
        self.assertEqual(True, True)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(JenkinsJobBrowser))
    return suite
