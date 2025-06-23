from authlib.integrations.flask_client import OAuth

oauth = OAuth()

def init_oauth(app):
    """Initialize OAuth client.""" 
    global oauth
    if not app.config.get("ENABLE_OIDC", False):
        return  

    oauth.init_app(app)
    oauth.register(
        name = "oidc",
        client_id = app.config["OIDC_CLIENT_ID"],
        client_secret = app.config["OIDC_CLIENT_SECRET"],
        server_metadata_url = f"{app.config["OIDC_AUTHORITY"]}/.well-known/openid-configuration",
        client_kwargs = {
            "scope": "openid email profile"
        }
    )

    return
