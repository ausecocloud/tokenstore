# define some constants to be used in unittests
from datetime import datetime
import unittest

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from jose import jwt
from jose.constants import ALGORITHMS
from jose.backends import RSAKey
from pyramid import testing
import requests_mock


# A testing request enhanced with some WebOb properties
class DummyRequest(testing.DummyRequest):

    @property
    def authorization(self):
        authorization = self.headers.get('Authorization')
        try:
            from webob.descriptors import parse_auth
            return parse_auth(authorization)
        except Exception:
            pass
        return None


# create an encoded jwt with keys from this module
def gen_jwt(claims):
    return jwt.encode(claims, PRIVKEY, ALGORITHMS.RS256)


# help to generate random keys
def gen_new_keys():
    key = rsa.generate_private_key(65537, 2048, default_backend())
    pem = key.private_bytes(encoding=serialization.Encoding.PEM,
                            format=serialization.PrivateFormat.PKCS8,
                            encryption_algorithm=serialization.NoEncryption())
    privkey = RSAKey(pem, ALGORITHMS.RS256).to_dict()
    privkey['id'] = 'keyid'
    for k in privkey:
        if isinstance(privkey[k], bytes):
            privkey[k] = privkey[k].decode('utf-8')
    pkey = key.public_key()
    pem = pkey.public_bytes(encoding=serialization.Encoding.PEM,
                            format=serialization.PublicFormat.PKCS1)
    pubkey = RSAKey(pem, ALGORITHMS.RS256).to_dict()
    pubkey['id'] = 'keyid'
    for k in pubkey:
        if isinstance(pubkey[k], bytes):
            pubkey[k] = pubkey[k].decode('utf-8')
    return privkey, pubkey


PRIVKEY, PUBKEY = gen_new_keys()

JWKS = {
    "keys": [PUBKEY]
}


ISSUER = 'https://example.com'
PROVIDER = 'https://provider.example.org'
WELL_KNOWN_OIDC_CONFIG = {
    ISSUER: {
        'issuer': ISSUER,
        'authorization_endpoint': '{}/auth'.format(ISSUER),
        'token_endpoint': '{}/token'.format(ISSUER),
        'token_introspection_endpoint': '{}/introspect'.format(ISSUER),
        'userinfo_endpoint': '{}/userinfo'.format(ISSUER),
        'jwks_uri': '{}/jwks'.format(ISSUER),
    },
    PROVIDER: {
        'issuer': PROVIDER,
        'authorization_endpoint': '{}/auth'.format(PROVIDER),
        'token_endpoint': '{}/token'.format(PROVIDER),
        'token_introspection_endpoint': '{}/introspect'.format(PROVIDER),
        'userinfo_endpoint': '{}/userinfo'.format(PROVIDER),
        'jwks_uri': '{}/jwks'.format(PROVIDER),
    }
}


USER_ID = 'example_user_id'

class FunctionalTestCase(unittest.TestCase):

    def setUp(self):
        from tokenstore import main

        from sqlalchemy.pool import StaticPool

        with requests_mock.mock() as m:
            m.get('{}/.well-known/openid-configuration'.format(ISSUER),
                  json=WELL_KNOWN_OIDC_CONFIG[ISSUER])
            m.get('{}/jwks'.format(ISSUER), json=JWKS)

            m.get('{}/.well-known/openid-configuration'.format(PROVIDER),
                  json=WELL_KNOWN_OIDC_CONFIG[PROVIDER])
            m.get('{}/jwks'.format(PROVIDER), json=JWKS)

            app = main(
                {},
                **{
                    'sqlalchemy.url': 'sqlite://',
                    'sqlalchemy.connect_args': {'check_same_thread': False},
                    'sqlalchemy.poolclass': StaticPool,

                    'oidc.issuer': ISSUER,
                    'oidc.client_id': 'example_client_id',

                    'oidc.providers': 'provider',
                    'oidc.provider.issuer': PROVIDER,
                    'oidc.provider.client_id': 'provider_client_id',
                    'oidc.provider.client_secret': 'provider_secret',
                    'oidc.provider.metadata.name': 'Provider',

                    'session.factory': 'pyramid_oidc.session.SessionFactory',
                    'session.secret': 'session_secret',
                    'session.cookie_opts.secure': 'False',
                    'session.cookie_opts.httponly': 'False',
                    'session.dogpile_opts.backend': 'dogpile.cache.memory',
                    'session.dogpile_opts.expiration_timeout': '1200',

                    'openapi.spec': 'tokenstore:openapi.yaml',
                }
            )

        from ..models.meta import Base
        Base.metadata.create_all(app.registry['dbsession_factory']().bind)

        from webtest import TestApp
        self.testapp = TestApp(app)

    def _user_token(self, exp=300, aud='example_client_id'):
        return gen_jwt({
            'iss': 'https://example.com',
            'exp': int(datetime.utcnow().timestamp()) + exp,
            'aud': aud,
            'sub': USER_ID,
            'resource_access': {
                'token': {
                    'roles': ['user']
                }
            }
        })

