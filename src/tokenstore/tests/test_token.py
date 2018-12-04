from datetime import datetime

import requests_mock

from .common import FunctionalTestCase, USER_ID, PROVIDER, gen_jwt


class TestToken(FunctionalTestCase):

    def setUp(self):
        super().setUp()
        from ..models import RefreshToken

        dbsession = self.testapp.app.registry['dbsession_factory']()
        dbsession.add(RefreshToken(
            provider='provider',
            token=gen_jwt({
                'iss': PROVIDER,
                'exp': int(datetime.utcnow().timestamp()) + 3600,
                'aud': 'provider_client_id',
                'sub': 'provider_user_id',
            }),
            expires_in=0,
            expires_at=datetime.utcnow().timestamp() + 3600,
            user_id=USER_ID,
        ))
        dbsession.commit()

    def test_token_noauth(self):
        self.testapp.get('/api/v1/provider/token', status=403)

    def test_token_404(self):
        self.testapp.authorization = ('Bearer', self._user_token())
        self.testapp.get('/api/v1/no_provider/token', status=404)

    def test_token(self):
        self.testapp.authorization = ('Bearer', self._user_token())
        with requests_mock.mock() as m:
            refresh_token = gen_jwt({
                'iss': PROVIDER,
                'exp': int(datetime.utcnow().timestamp()) + 3600,
                'aud': 'provider_client_id',
                'sub': 'provider_user_id',
            })
            m.post('{}/token'.format(PROVIDER), json={
                'access_token': 'at',
                'token_type': 'Bearer',
                'refresh_token': refresh_token,
                'expires_in': 300,
                'expires_at': datetime.utcnow().timestamp() + 300,
                'refresh_expires_in': 3600,
                # 'id_token': 'it',
            })

            res = self.testapp.get('/api/v1/provider/token', status=200)
        data = res.json
        self.assertIn('access_token', data)
        self.assertEqual(data['access_token'], 'at')
