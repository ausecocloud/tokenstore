from datetime import datetime
from urllib.parse import urlparse, parse_qs

import requests_mock

from .common import FunctionalTestCase, PROVIDER, gen_jwt


class TestAuthorizations(FunctionalTestCase):

    def test_authorize_get_noauth(self):
        self.testapp.get('/api/v1/no_provider/authorize', status=403)

    def test_authorize_post_noauth(self):
        self.testapp.post_json('/api/v1/no_provider/authorize', status=403)

    def test_authorize_get_404(self):
        self.testapp.authorization = ('Bearer', self._user_token())
        self.testapp.get('/api/v1/no_provider/authorize', status=404)

    def test_authorize_get(self):
        self.testapp.authorization = ('Bearer', self._user_token())
        res = self.testapp.get('/api/v1/provider/authorize', status=302)
        self.assertIn('Set-Cookie', res.headers)
        self.assertTrue(res.headers['Location'].startswith('{}/auth'.format(PROVIDER)))

    def test_authorize_post_404(self):
        self.testapp.authorization = ('Bearer', self._user_token())
        self.testapp.post_json('/api/v1/no_provider/authorize', status=404)

    def test_authorize_post(self):
        self.testapp.authorization = ('Bearer', self._user_token())
        res = self.testapp.post_json('/api/v1/provider/authorize', status=201)
        self.assertIn('Set-Cookie', res.headers)
        self.assertTrue(res.headers['Location'].startswith('{}/auth'.format(PROVIDER)))

    def test_authorize_referer_post(self):
        self.testapp.authorization = ('Bearer', self._user_token())
        res = self.testapp.post_json('/api/v1/provider/authorize', {'referer': 'https://referer.example.com'}, status=201)
        auth_url = res.headers['Location']
        redirect_uri = parse_qs(urlparse(auth_url).query)['redirect_uri'][0]
        state = parse_qs(urlparse(auth_url).query)['state'][0]
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
            res = self.testapp.get(redirect_uri, {'code': 'code', 'state': state}, status=302)
        self.assertEqual(res.headers['Location'], 'https://referer.example.com')
        res = self.testapp.get('/api/v1/authorizations', status=200)
        data = res.json
        self.assertEqual(len(data), 1)
        self.assertTrue(data[0]['active'])

    def test_authorize_referer_get(self):
        self.testapp.authorization = ('Bearer', self._user_token())
        res = self.testapp.get('/api/v1/provider/authorize', {'referer': 'https://referer.example.com'}, status=302)
        auth_url = res.headers['Location']
        redirect_uri = parse_qs(urlparse(auth_url).query)['redirect_uri'][0]
        state = parse_qs(urlparse(auth_url).query)['state'][0]
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
            res = self.testapp.get(redirect_uri, {'code': 'code', 'state': state}, status=302)
        self.assertEqual(res.headers['Location'], 'https://referer.example.com')
        res = self.testapp.get('/api/v1/authorizations', status=200)
        data = res.json
        self.assertEqual(len(data), 1)
        self.assertTrue(data[0]['active'])
