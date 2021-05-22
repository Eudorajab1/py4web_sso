"""
This file defines the database models
"""
from .common import db, Field, auth, settings
from pydal.validators import *
import uuid
from datetime import datetime
from py4web.utils.form import Form, FormStyleBulma

db.auth_user._format = '%(email)s'    

USER_STATUS =['Added','Invited', 'Registered']
USER_ROLES=['Owner', 'Admin','Manager', 'User']

secret_key = lambda: str(uuid.uuid4())

def get_time():
    return datetime.datetime.utcnow()

def get_download_url(picture):
    return f"images/{picture}"

def get_user():
    return auth.current_user.get("id") if auth.current_user else None

db.define_table('registered_clients',
                Field('client_name', requires=IS_NOT_IN_DB(db, 'registered_clients.client_name'),unique=True),
                Field('client_url', requires=IS_NOT_IN_DB(db, 'registered_clients.client_url'), unique=True),
                Field('client_secret', readable=True, writable=False, default=secret_key),
                Field('is_active', 'boolean', default=False),
                format='%(client_name)s'
                )
db.registered_clients._singular = 'Registered Client'
db.registered_clients._plural = 'Registered Clients'

db.define_table('client_users',
                Field('email','reference auth_user',
                    requires=IS_IN_DB(db, 'auth_user.id', 'auth_user.email')),
                Field('client_id', 'reference registered_clients',
                    requires=IS_IN_DB(db, 'registered_clients.id', 'registered_clients.client_name')),
                Field('role', label="Role", requires = IS_IN_SET(USER_ROLES)),
                Field('status', requires= IS_IN_SET(USER_STATUS), default='Invited'),
                )
db.client_users._singular = 'Client User'
db.client_users._plural = 'Client Users'

db.define_table(
    "profile",
    Field("user", "reference auth_user", readable=False, writable=False),
    Field(
        "image",
        "upload",
        default="default.jpg",
        uploadfolder=settings.UPLOAD_PATH,
        download_url=get_download_url, label="Profile Picture",
    ),
)
db.commit()