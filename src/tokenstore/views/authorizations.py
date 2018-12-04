from pyramid.view import view_config

from pyramid_oidc.interfaces import IOIDCUtility

from ..models import RefreshToken


@view_config(route_name='tokenstore_authorizations', renderer='json',
             request_method='GET', permission='view', cors=True)
def authorizations(request):
    res = []
    user_id = request.authenticated_userid
    dbsession = request.dbsession
    active_providers = {
        row.provider for row in
        dbsession.query(RefreshToken.provider).filter_by(user_id=user_id)
    }
    for name, utility in request.registry.getUtilitiesFor(IOIDCUtility):
        if not name:
            # skip unnamed utilities
            continue

        authorization = {
            'active': name in active_providers,
            'provider': name,
            'authorize': request.route_url('tokenstore_authorize', provider=name),
            'token': request.route_url('tokenstore_token', provider=name),
            'revoke': request.route_url('tokenstore_revoke', provider=name),
        }
        authorization.update(utility.metadata)
        res.append(authorization)
    return res
