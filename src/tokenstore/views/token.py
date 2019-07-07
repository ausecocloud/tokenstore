from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest

from oauthlib.oauth2.rfc6749.errors import InvalidGrantError
from pyramid_oidc.interfaces import IOIDCUtility

from ..models import RefreshToken


@view_config(route_name='tokenstore_token', renderer='json',
             request_method='GET', permission='view', cors=True)
def token(request):

    providerid = request.matchdict['provider']
    provider = request.registry.queryUtility(IOIDCUtility, providerid)
    if not provider:
        raise HTTPNotFound()

    user_id = request.authenticated_userid

    # check if we have a refresh token
    dbsession = request.dbsession
    refresh_token = dbsession.query(RefreshToken).filter_by(
        provider=providerid,
        user_id=user_id,
    ).one_or_none()
    if refresh_token is None:
        # FIXME: need an error messages, client not authorized or refresh
        #        token expired?
        return HTTPBadRequest()

    # we fetch a new access_token in any case
    cur_token = request.registry['tokenstore.crypto'].decrypt(refresh_token.token)
    oauth = provider.get_oauth2_session(
        request,
        token={'refresh_token': cur_token}
    )
    try:
        # TODO: move this into OIDCUtitlity?
        oauth.refresh_token(
            provider.token_endpoint,
            auth=(provider.client_id, provider.client_secret),
        )
    except InvalidGrantError as e:
        # usually an expired refresh token
        # TODO: are there constants for errors?

        # if e.error == 'invalid_grant':
        raise HTTPBadRequest(str(e))

    # parse refresh_token
    refresh_token_decoded = provider.validate_token(
        oauth.token['refresh_token'],
        verify_exp=oauth.token['refresh_expires_in'] != 0
    )
    # update refresh token
    refresh_token.token = request.registry['tokenstore.crypto'].encrypt(oauth.token['refresh_token'])
    refresh_token.expires_in = oauth.token['refresh_expires_in']
    # TODO: check if there is really a value for 'exp'
    refresh_token.expires_at = refresh_token_decoded['exp']

    return {
        'access_token': oauth.token['access_token'],
        'expires_in': oauth.token['expires_in'],
        'token_type': oauth.token['token_type'],
        'expires_at': oauth.token['expires_at'],
        # 'scope': token['scope'],
    }
