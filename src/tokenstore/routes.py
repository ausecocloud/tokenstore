def includeme(config):

    # TODO: once we get the redirect uri changed in coesra we can add {provider}
    #       to the redirect_uri endpoint as well and remove it from session state
    #       or just keep it in session state for validation?
    # TODO: rename routes, they are too similar to pyramid_oidc pkg
    config.add_route(name='tokenstore_redirect_uri', pattern='/api/v1/{provider}/redirect_uri')
    config.add_route(name='tokenstore_authorize', pattern='/api/v1/{provider}/authorize')
    config.add_route(name='tokenstore_token', pattern='/api/v1/{provider}/token')
    config.add_route(name='tokenstore_revoke', pattern='/api/v1/{provider}/revoke')
    config.add_route(name='tokenstore_authorizations', pattern='/api/v1/authorizations')

    #config.add_static_view('static', 'static', cache_max_age=3600)
    #config.add_route('home', '/')

