from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound, HTTPCreated, HTTPNotFound

from pyramid_oidc.interfaces import IOIDCUtility
from openapi_core.schema.media_types.exceptions import InvalidMediaTypeValue


# on GET this returns with a redirect on POST with a 201 and a Location header
@view_config(route_name='tokenstore_authorize', renderer='json',
             request_method=('GET', 'POST'), permission='view', cors=True)
def authorize(request):

    try:
        params = request.oas.validate_params()
        providerid = params.parameters.get('path', {}).get('provider')
        referer = (params.parameters.get('query', {}).get('referer') or
                   params.body and params.body.referer)
    except InvalidMediaTypeValue:
        # workaround openapi-core not correctly validating empty request body
        providerid = request.matchdict['provider']
        referer = request.params.get('referer')

    provider = request.registry.queryUtility(IOIDCUtility, providerid)
    if not provider:
        raise HTTPNotFound()

    url, state = provider.get_auth_url(request)

    # store session state
    session = request.session
    session['state'] = {
        state: {
            'user_id': request.authenticated_userid,
            'referer': (referer or request.referer or request.url),
            'provider': providerid,
        }
    }

    # Redirect to authorization endpoint and state session state cookie
    if request.method == 'GET':
        return HTTPFound(url)
    else:
        return HTTPCreated(headers={'Location': url})
