"""
This file defines actions, i.e. functions the URLs are mapped into
The @action(path) decorator exposed the function at URL:

    http://127.0.0.1:8000/{app_name}/{path}

If app_name == '_default' then simply

    http://127.0.0.1:8000/{path}

If path == 'index' it can be omitted:

    http://127.0.0.1:8000/

The path follows the bottlepy syntax.

@action.uses('generic.html')  indicates that the action uses the generic.html template
@action.uses(session)         indicates that the action uses the session
@action.uses(db)              indicates that the action uses the db
@action.uses(T)               indicates that the action uses the i18n & pluralization
@action.uses(auth.user)       indicates that the action requires a logged in user
@action.uses(auth)            indicates that the action requires the auth object

session, db, T, auth, and tempates are examples of Fixtures.
Warning: Fixtures MUST be declared with @action.uses({fixtures}) else your app will result in undefined behavior
"""

from py4web import action, request, abort, redirect, URL
from yatl.helpers import A
from .common import db, session, T, cache, auth, settings, logger, authenticated, unauthenticated, flash
from .._sso_server.controllers import local_auth, sso_logout
import jwt
@action("login", method=['GET', 'POST'])
@action.uses("generic.html", auth, db, session)
def login():
    caller = request.app_name
    cas_server = settings.SSO_SERVER
    next = URL('index', scheme=True)
    redirect(cas_server+'/auth/login?next=%s' % next)

@action("change_password", method=['GET', 'POST'])
@action.uses("generic.html", auth, db, session)
def change_password():
    cas_server = settings.SSO_SERVER
    caller = URL('index', scheme=True)
    redirect(cas_server+'/auth/change_password?next=%s' % caller)

@action("profile", method=['GET', 'POST'])
@action.uses("generic.html", auth, db, session)
def profile():
    cas_server = settings.SSO_SERVER
    caller = URL('index', scheme=True)
    redirect(cas_server+'/sso_profile?next=%s' % caller)

@action("logout", method=['GET', 'POST'])
@action.uses("generic.html", auth, db, session)
def logout():
    caller = request.app_name
    sso_logout()
    auth.session.clear()
    request.app_name = caller
    redirect(URL('index'))

@action("index", method=['GET', 'POST'])
@action.uses(db, session, "index.html")
def index():
    other_clients=[]
    user=session.get('user', None)
    caller = request.app_name
    message='Welcome to %s' % caller
    if not user:
        token = str(local_auth(caller))
        if not token == 'Unauthorised':
            token_decoded = jwt.decode(token, settings.CLIENT_SECRET, algorithms=['HS256'])
            session['user'] =  token_decoded
            user=session.get('user', None)
            all_clients = session['user']['all']
            for client in all_clients:
                if client['client'] != caller:
                    other_clients.append(client)
                else:
                    continue
        else:
            message = 'You are NOT authorised to be here. Please log in with valid credentials'
    else:
        all_clients = session['user']['all']
        for client in all_clients:
            if client['client'] != caller:
                other_clients.append(client)
    request.app_name = caller
    return dict(message=message, user=user, other_clients=other_clients)
