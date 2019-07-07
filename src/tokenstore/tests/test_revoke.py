from datetime import datetime
from .common import FunctionalTestCase, USER_ID


class TestRevoke(FunctionalTestCase):

    def setUp(self):
        super().setUp()
        from ..models import RefreshToken

        registry = self.testapp.app.registry
        dbsession = registry['dbsession_factory']()
        dbsession.add(RefreshToken(
            provider='provider',
            token=registry['tokenstore.crypto'].encrypt('broken token'),
            expires_in=0,
            expires_at=datetime.utcnow().timestamp() + 3600,
            user_id=USER_ID,
        ))
        dbsession.commit()

    def test_revoke_noauth(self):
        self.testapp.post('/api/v1/provider/revoke', status=403)

    def test_revoke_404(self):
        self.testapp.authorization = ('Bearer', self._user_token())
        self.testapp.post('/api/v1/no_provider/revoke', status=404)

    def test_revoke(self):
        self.testapp.authorization = ('Bearer', self._user_token())
        res = self.testapp.get('/api/v1/authorizations')
        data = res.json
        self.assertEqual(len(data), 1)
        self.assertTrue(data[0]['active'])
        res = self.testapp.post('/api/v1/provider/revoke', status=200)
        res = self.testapp.get('/api/v1/authorizations')
        data = res.json
        self.assertEqual(len(data), 1)
        self.assertFalse(data[0]['active'])

    def test_revoke_again(self):
        self.testapp.authorization = ('Bearer', self._user_token())
        res = self.testapp.get('/api/v1/authorizations')
        data = res.json
        self.assertEqual(len(data), 1)
        self.assertTrue(data[0]['active'])
        res = self.testapp.post('/api/v1/provider/revoke', status=200)
        res = self.testapp.post('/api/v1/provider/revoke', status=200)
        res = self.testapp.get('/api/v1/authorizations')
        data = res.json
        self.assertEqual(len(data), 1)
        self.assertFalse(data[0]['active'])
