from .common import FunctionalTestCase


class TestAuthorizations(FunctionalTestCase):

    def test_authorizations_noauth(self):
        self.testapp.get('/api/v1/authorizations', status=403)

    def test_authorizations(self):
        self.testapp.authorization = ('Bearer', self._user_token())
        res = self.testapp.get('/api/v1/authorizations', status=200)
        data = res.json
        self.assertEqual(len(data), 1)
        self.assertFalse(data[0]['active'])
        self.assertEqual(data[0]['name'], 'Provider')
