from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotFound, HTTPOk

from pyramid_oidc.interfaces import IOIDCUtility

from ..models import RefreshToken


@view_config(route_name='tokenstore_revoke', renderer='json',
             request_method='POST', permission='view', cors=True)
def revoke(request):

    providerid = request.matchdict['provider']
    provider = request.registry.queryUtility(IOIDCUtility, providerid)
    if not provider:
        raise HTTPNotFound()

    user_id = request.authenticated_userid

    # delete the refresh token
    dbsession = request.dbsession
    # We don't really care whether a refresh_token exists or not
    dbsession.query(RefreshToken).filter_by(
        provider=providerid,
        user_id=user_id,
    ).delete()

    return HTTPOk()
