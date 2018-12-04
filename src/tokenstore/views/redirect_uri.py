from pyramid.httpexceptions import (
    HTTPForbidden, HTTPFound, HTTPNotFound, HTTPBadRequest
)
from pyramid.view import view_config

from pyramid_oidc.interfaces import IOIDCUtility

from ..models import RefreshToken


@view_config(route_name='tokenstore_redirect_uri', renderer='json',
             request_method='GET')
def redirect_uri(request):
    # TODO: get state from session so that fetch_token can verify it.
    providerid = request.matchdict['provider']
    provider = request.registry.queryUtility(IOIDCUtility, providerid)
    if not provider:
        raise HTTPNotFound()

    # get state from session
    session = request.session
    # state can be used only once ... remove it from session immediately
    state_data = session.pop('state', {})

    # get first key in state
    # FIXME: this may throw a StopIteration in case state was empty
    #        catch if state_data is empty or None?
    try:
        state = next(iter(state_data))
    except StopIteration:
        # no state data available
        raise HTTPBadRequest()

    state_data = state_data[state]

    # trade code for token
    token = provider.fetch_auth_token(request, state=state)

    # validate user_id (in case we have one)
    user_id = request.authenticated_userid
    if (user_id and user_id != state_data['user_id']):
        # We have an authorised user, but it doesn't match the user_id in
        # session state
        raise HTTPForbidden()
    # user valid as far as we can tell
    user_id = state_data['user_id']

    # update refresh_token
    dbsession = request.dbsession
    refresh_token = dbsession.query(RefreshToken).filter_by(
        provider=providerid,
        user_id=state_data['user_id']
    ).one_or_none()
    if refresh_token is None:
        # create a new one
        refresh_token = RefreshToken(
            provider=providerid,
            user_id=state_data['user_id']
        )
        dbsession.add(refresh_token)
    # update refresh_token
    refresh_token.token = token['refresh_token']
    refresh_token.expires_in = token['refresh_expires_in']
    # parse refresh_token
    refresh_token_decoded = provider.validate_token(
        refresh_token.token,
        verify_exp=refresh_token.expires_in != 0
    )
    # TODO: check if there is really a value for 'exp'
    refresh_token.expires_at = refresh_token_decoded['exp']
    # TODO: do some more validation
    #       e.g. match refresh/access token 'aud', 'iss', 'sub'

    # return redirect to referer from state
    # TODO: some sort of success failure state in the url would be nice
    url = state_data['referer']
    return HTTPFound(url)
