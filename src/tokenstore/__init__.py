from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.settings import aslist

from pyramid_oidc import build_oidc_utility, IOIDCUtility, parse_setting
from pyramid_oidc.authentication import OIDCBearerAuthenticationPolicy
from pyramid_oidc.authentication.keycloak import keycloak_callback

from .resources import Root
from .utilities import CryptoTool


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    with Configurator(settings=settings, root_factory=Root) as config:
        # setup OIDC auth
        config.include('pyramid_oidc', route_prefix='/oidc')
        # add openapi support
        config.include('pyramid_openapi')
        # add cors support
        config.include('pyramid_cors')
        config.add_cors_preflight_handler()

        config.include('.models')
        config.include('.routes')

        # set up authentication
        authn_policy = OIDCBearerAuthenticationPolicy(
            # probably don't need callback, as we don't need any roles
            callback=keycloak_callback,
        )
        config.set_authentication_policy(authn_policy)
        config.set_authorization_policy(ACLAuthorizationPolicy())

        config.registry['tokenstore.crypto'] = CryptoTool(config)

        # setup apps
        # newline / space separated list of providers key to look for.
        providers = parse_setting(settings, 'oidc.', 'providers',
                                  conv=aslist, envvar=True) or []
        for provider in providers:
            prefix = 'oidc.{}.'.format(provider)
            utility = build_oidc_utility(settings, prefix)
            utility.redirect_route = 'tokenstore_redirect_uri'
            utility.redirect_route_params = {'provider': provider}
            utility.metadata = {}
            metadata_prefix = prefix + 'metadata.'
            for key in settings:
                if not key.startswith(metadata_prefix):
                    continue
                utility.metadata[key[len(metadata_prefix):]] = settings[key]
            config.registry.registerUtility(utility, IOIDCUtility, name=provider)

        config.scan('.views')

        return config.make_wsgi_app()
