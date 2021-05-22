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
from .common import db, Field, session, T, cache, auth, logger, authenticated, unauthenticated, flash, groups
from py4web.utils.form import Form, FormStyleBulma
from pydal.validators import *
from pydal import *
from . import settings

import jwt
import os
from PIL import Image

import os
USER_STATUS =['Added','Invited', 'Registered']
USER_ROLES=['Owner', 'Admin','Manager', 'User']

class local_auth(object):
    def __init__(self, caller):
        self.client=caller
        self.clients = []
        self.user = auth.get_user()
        
    def get_client_secret(self):
        query = db.registered_clients.client_name == self.client
        rec = db(query).select(db.registered_clients.client_secret).first()
        return rec.client_secret

    def is_authorised(self):
        if not self.user:
            return False
        query = db.client_users.email == self.user['id']
        recs=db(query).select()
        if not recs:
            return False
        else: 
            for rec in recs:
                client={}
                if db.registered_clients[rec.client_id].is_active == True:
                    role = rec.role
                    name = db.registered_clients[rec.client_id].client_name
                    url = db.registered_clients[rec.client_id].client_url
                    client = dict(client=name, role=role, url=url)
                    self.clients.append(client)
                else:
                    continue
            
        res = next((item for item in self.clients if item["client"] == self.client), False)
        if not res == False: #resself.client in self.clients['client']:
            return True
        else:
            return False
    
    def get_role(self):
        res = next((item for item in self.clients if item["client"] == self.client), False)
        return res["role"]
    
    def get_url(self):
        res = next((item for item in self.clients if item["client"] == self.client), False)
        return res["url"]
        
    def __str__(self):
        original_url = request.environ.get("HTTP_ORIGIN") or request.url
        is_authorised = self.is_authorised()
        if is_authorised == False:
            token = 'Unauthorised'
            return token
        else:
            user = self.user
            user['client_id'] = self.client
            user['client_url'] = self.get_url()
            user['role'] = self.get_role()
            user['all'] = self.clients
            secret = self.get_client_secret()
            token = jwt.encode(user, secret, algorithm='HS256')
            return token

@action("sso_logout")
@action.uses(db, session, auth)
def sso_logout():
    auth.session.clear()
    return 'All done'


@authenticated("sso_profile", "profile.html")
@authenticated("sso_profile/<caller>", "profile.html")
def sso_profile(caller=None):
    user = auth.get_user()
    caller = request.query.get('next', None)
    profile = db.auth_user(user["id"]).profile.select().first()

    icon = f"images/{profile.image}"
    # Append the user profile icon to the dict so it prepopulates it with current data
    user.update({"image": profile.image})

    # Get all the required fields out of the 2 tables to display them: Username, Email, First/Last name, and Profile Pic
    form_list = [field for field in db.auth_user if not field.type == "id"] + [
        field for field in db.profile if not field.type == "id"
    ]
    aform = Form(
        form_list,
        record=user,
        csrf_session=session,
        deletable=False,
        formstyle=FormStyleBulma,
    )
    if aform.accepted:
        # Update the auth user
        db.auth_user[user["id"]].update_record(
            username=aform.vars["username"],
            email=aform.vars["email"],
            first_name=aform.vars["first_name"],
            last_name=aform.vars["last_name"],
        )

        # The icon we want to update our profile will always have a default of default.jpg
        update_icon = "default.jpg"

        if not aform.vars["image"] and profile.image == update_icon:
            # We can't delete the default image so we just redirect back to the page.
            redirect(URL("profile"))

        if aform.vars["image"]:
            # If we are setting it equal to a new icon, we set icon to that file name
            update_icon = aform.vars["image"]

        if update_icon != profile.image:
            # If the new icon (which can be default.jpg) isn't the same icon as before, remove the old one and update
            if profile.image != "default.jpg":
                cleanup_image(profile.image)
                resize_image(update_icon)
            profile.update_record(image=update_icon)

        # Once done with everything (Or after doing nothing because the icons are the same), return to the profile page
        if caller:
            redirect(caller)
        else:
            redirect(URL("sso_profile"))
    return dict(icon=icon, aform=aform)


def resize_image(image_path):
    total_path = os.path.join(settings.UPLOAD_PATH, image_path)

    img = Image.open(total_path)
    if img.height > 300 or img.width > 300:
        output_size = (300, 300)
        img.thumbnail(output_size)
        img.save(total_path)


def cleanup_image(image_path):
    total_path = os.path.join(settings.UPLOAD_PATH, image_path)
    os.remove(total_path, dir_fd=None)


@action("index", method=['GET','POST'])
@action.uses(db, auth, session, flash, "index.html")
def index():
    menu_items = []
    message = "SSO Landing Page"
    user=auth.get_user()
    #print ('sso user', user)
    if user:
        grps = groups.get(auth.get_user()['id'])
        if not 'Admin' in grps:
            query = db.client_users.email == user['id']
            recs = db(query).select()
            if not recs:
                flash.set('YOU DONT HAVE ACCESS TO ANY REGISTERED CLIENTS. Please  contact your administrator')
            else:
                menu_items = []
                for rec in recs:
                    menu_items.append(dict(name=db.registered_clients[rec.client_id].client_name,
                                           goto=db.registered_clients[rec.client_id].client_url))    
        else:
            menu_items = [
                dict(name="Manage Groups", goto="../manage_groups"),
                dict(name="Manage Clients", goto="../manage_clients"),
                dict(name="Manage Users", goto="../manage_users")
            ]
    else:
        redirect(URL('auth/login', vars=dict(next = '../index')))
        
    return dict(message=message, menu_items = menu_items)

@action('remove_group/<group_id>', method=['GET','POST'])
@action.uses(db, session, auth, flash, 'generic.html' )
def remove_group(group_id=None):
    if not group_id:
        flash.set('No group ID selected')
    else:    
        db(db.auth_user_tag_groups.id == group_id).delete()
        flash.set('Removed group ')
    redirect(URL('manage_groups'))

@action('edit_group/<group_id>', method=['GET','POST'])
@action.uses(db, session, auth, flash, 'edit_rec.html' )
def edit_group(group_id=None):
    db.auth_user_tag_groups.id.readable =db.auth_user_tag_groups.id.writable = False
    form = Form(db.auth_user_tag_groups, group_id, formstyle=FormStyleBulma)
    if form.accepted:
        flash.set('Updated group details')
        redirect(URL('manage_groups'))
    return dict(form=form)           

@action('manage_groups', method=['GET','POST'])
@action.uses(db, session, auth, flash, 'manage_groups.html' )
def manage_groups():
    page_title = 'STEP 1 >> Manage User Groups'
    back = ''
    menu_items = []
    user = auth.get_user()
    if not user:
        redirect(URL('auth', 'login'))
    #back = mygui.get_button('back', URL('register'), T("Back"), T('Back'))
    menu_items.append(dict(name="Manage Clients", goto="../manage_clients"))
    menu_items.append(dict(name="Manage Users", goto="../manage_users"))
    form=Form(db.auth_user_tag_groups, dbio=False, formstyle=FormStyleBulma)
    if form.accepted:
        db.auth_user_tag_groups.insert(**form.vars)
    groups = db(db.auth_user_tag_groups).select()
    headers = ['#ID', 'Path', 'User', 'Actions']
    return dict(form=form, headers=headers, groups=groups, page_title=page_title, back=back, user=user, menu_items=menu_items)


@action('edit_client/<client_id>', method=['GET','POST'])
@action.uses(db, session, auth, flash, 'edit_rec.html' )
def edit_client(client_id=None):
    db.registered_clients.id.readable =db.registered_clients.id.writable = False
    form = Form(db.registered_clients, client_id, formstyle=FormStyleBulma)
    if form.accepted:
        flash.set('Updated client details')
        redirect(URL('manage_clients'))
    return dict(form=form)           

@action('manage_clients', method=['GET','POST'])
@action.uses(db, session, auth, flash, 'manage_clients.html' )
def register_clients(client_id=None):
    page_title = 'STEP 1 >> Register Your Clients'
    back = ''
    menu_items = []
    user = auth.get_user()
    if not user:
        redirect(URL('auth', 'login'))
    menu_items.append(dict(name="Manage Groups", goto="../manage_groups"))
    menu_items.append(dict(name="Manage Users", goto="../manage_users"))
    form=Form(db.registered_clients, dbio=False, formstyle=FormStyleBulma)
    db.registered_clients.client_secret.readable = db.registered_clients.client_secret.writable = False 
    form=Form(db.registered_clients, dbio=False, formstyle=FormStyleBulma)
    if form.accepted:
        rcid = db.registered_clients.insert(**form.vars)
        cuid = db.client_users.insert(email = user['id'],
                                      client_id = rcid,
                                      role = "Owner",
                                      status = "Registered"
        )  
    clients = db(db.registered_clients).select()
    headers = ['#ID', 'Name', 'URL', 'Key', 'Is Active', 'Actions']
    return dict(form=form, headers=headers, clients=clients, page_title=page_title, back=back, user=user, menu_items=menu_items)

@action('remove_registered_client/<client_id>')
@action.uses(db, session, auth, flash )
def remove_registered_client(client_id):
    user = auth.get_user()
    if not user:
        redirect(URL('auth', 'login'))
    if not client_id:
        flash.set('No client selected ... please seleczt a client to remove')
        redirect(URL('register_clients'))
    else:
        db(db.registered_clients.id == client_id).delete()
        flash.set('Deleted client')
        redirect(URL('register_clients'))


@action('remove_client_user/<user_id>')
@action.uses(db, session, auth, flash )
def remove_clieint_user(user_id):
    user = auth.get_user()
    if not user:
        redirect(URL('auth', 'login'))
    if not user_id:
        flash.set('No user selected ... please seleczt a user to remove')
        redirect(URL('manage_users'))
    else:
        db(db.client_users.id == user_id).delete()
        flash.set('Deleted user')
        redirect(URL('manage_users'))

@action('manage_users', method=['GET','POST'])
@action('manage_users/<user_id>', method=['GET','POST'])
@action.uses(db, session, auth, flash, 'manage_users.html' )
def manage_users(user_id=None):
    page_title = 'STEP 2 >> Invite users'
    back = ''
    edit = False
    menu_items = []
    user = auth.get_user()
    if not user:
        redirect(URL('auth', 'login'))
    #back = mygui.get_button('back', URL('register'), T("Back"), T('Back'))
    menu_items.append(dict(name="Manage Groups", goto="../manage_groups"))
    menu_items.append(dict(name="Manage Clients", goto="../manage_clients"))
    if user_id:
        db.client_users.id.readable =db.client_users.id.writable = False
        form = Form(db.client_users, user_id, formstyle=FormStyleBulma)
        edit = True
        if form.accepted:
            flash.set('Updated user for registered client')
            edit=False
            form = Form(db.client_users, dbio=False, formstyle=FormStyleBulma)
    else:
        form = Form(db.client_users, dbio=False, formstyle=FormStyleBulma)
        edit = False
        if form.accepted:
            db.client_users.insert(**form.vars)
            flash.set('Added a new registered client user')
    headers=['#ID', 'Email', 'Client', 'Role', 'Status', 'Actions']            
    users = db(db.client_users.id > 0).select()
    recs=[]
    for u in users: #.render():
        rec={}
        rec = dict(id=u.id, email=db.auth_user[u.email].email, client=db.registered_clients[u.client_id].client_name, 
                    role=u.role, status=u.status)
        recs.append(rec)

    return dict(form=form, users=recs, headers=headers, page_title=page_title, back=back, edit=edit, menu_items=menu_items, user=user)
