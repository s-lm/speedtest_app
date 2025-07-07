from flask import current_app, redirect, session, request
from flask.helpers import url_for
from authlib.jose import jwt, JoseError
from authlib.integrations.base_client.errors import MismatchingStateError
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


def oidc_required(f):
    """Decorator to require OIDC only if enabled."""
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if current_app.config.get("ENABLE_OIDC", False):
            if "token" not in session or is_token_expired():
                reset_session()
                return redirect(url_for(".login", state=request.url))
        return f(*args, **kwargs)
    return wrapper


def is_token_expired() -> bool:
    """Check if the token is expired."""
    token = session.get("token", {}).get("id_token", None)
    if not token:
        return True
    try:
        jwk_set = oauth.oidc.fetch_jwk_set()
        claims = jwt.decode(token, jwk_set, claims_options={"exp": {"essential": True}})
        claims.validate()
    except JoseError:
        current_app.logger.warning("Token validation failed or token is expired.")
        return True
    return False


def do_login():
    redirect_uri = url_for(".auth_callback", _external=True)
    nonce = base64.urlsafe_b64encode(os.urandom(16)).decode("utf-8")
    state = request.args.get("state") or url_for(".show")
    return oauth.oidc.authorize_redirect(redirect_uri, state=state)


def callback():
    try:
        token = oauth.oidc.authorize_access_token()
        userinfo = oauth.oidc.parse_id_token(token, nonce=nonce)
        session["token"] = token
        current_app.logger.debug(f"Token: {token}")
        current_app.logger.info(f"User {userinfo['preferred_username']} logged in successfully.")
        return redirect(request.args.get("state") or url_for(".show"))
    except MismatchingStateError as e:
        current_app.logger.info(f"OAuth MismatchingStateError during callback: {e}")
        return redirect(url_for(".logout", error="CSRF Warning! State not equal in request and response. Please try again."))


def reset_session() -> None:
    session.clear()


def get_username() -> str:
    """Get the username from the session."""
    if "token" not in session or "userinfo" not in session["token"]:
        return "unknown"
    return session["token"]["userinfo"].get("preferred_username", "unknown")

