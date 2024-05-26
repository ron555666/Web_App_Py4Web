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

import time

from py4web import action, request, abort, redirect, URL
from yatl.helpers import A

from py4web.utils.form import Form, FormStyleBulma
from .common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash
from py4web.utils.url_signer import URLSigner
from .models import get_user_email

url_signer = URLSigner(session)
MAX_RETURNED_USERS = 20  # Our searches do not return more than 20 users.
MAX_RESULTS = 20  # Maximum number of returned meows.

# for all the variable and function: load_contact is equal to the meaning of load_imageBox
@action('index')
@action.uses('index.html', db, auth.user, session, url_signer)
def index():
    post = db(db.post.user_email == get_user_email()).select()
    selected_color = session.get('selectedColor', 'no-color')
    set_add_status_url = URL('set_add_status', signer=url_signer)
    mark_contact_url = URL('mark_contact', signer=url_signer)
    return dict(
        load_contacts_url=URL('load_contacts', signer=url_signer),
        add_contact_url=URL('add_contact', signer=url_signer),
        delete_contact_url=URL('delete_contact', signer=url_signer),
        edit_contact_url=URL('edit_contact', signer=url_signer),
        upload_thumbnail_url=URL('upload_thumbnail', signer=url_signer),
        post=post,
        my_callback_url=URL('my_callback', signer=url_signer),
        get_users_url=URL('get_users', signer=url_signer),
        follow_url=URL('set_follow', signer=url_signer),
        selectedColor=selected_color,
        set_add_status_url=set_add_status_url,
        mark_contact_url = mark_contact_url,
    )

@action('my_callback')
@action.uses(url_signer.verify())
def my_callback():
    post = db(db.post).select(orderby=~db.post.id)
    for p in post:
        comments = db(db.comment.post_id == p.id).select(orderby=db.comment.id)
        p.comments = comments
    return dict(post=post)

@action('add', method=['GET', 'POST'])
@action.uses(db, session, auth.user, 'add.html')
def addpost():
    form = Form(db.post, csrf_session=session, formstyle=FormStyleBulma)
    if form.accepted:
        redirect(URL('index'))
    return dict(form=form)

@action('edit/<post_id:int>', method=['GET', 'POST'])
@action.uses(db, session, auth.user, 'edit.html')
def editpost(post_id=None):
    assert post_id is not None
    p = db.post[post_id]
    if p is None:
        redirect(URL('index'))
    form = Form(db.post, record=p, deletable=False, csrf_session=session, formstyle=FormStyleBulma)
    if form.accepted:
        redirect(URL('index'))
    return dict(form=form)

@action('delete/<post_id:int>')
@action.uses(db, session, auth.user, 'delete.htmls')
def deletepost(post_id=None):
    assert post_id is not None
    db(db.post.id == post_id).delete()
    redirect(URL('index'))

# This is our very first API function.
@action('load_contacts')
@action.uses(url_signer.verify(), db)
def load_contacts():
    rows = db(db.contact).select().as_list()
    return dict(rows=rows)

@action('add_contact', method="POST")
@action.uses(url_signer.verify(), db, auth)
def add_contact():
    first_name = auth.current_user.get('first_name')  # Get the logged-in user's first name
    id = db.contact.insert(
        first_name=first_name,
        title=request.json.get('title'),
        caption=request.json.get('caption'),
        thumbnail=request.json.get('thumbnail'),
        color=request.json.get('color'),
    )
    session['selectedColor'] = request.json.get('color')
    return dict(id=id, first_name=first_name)  # Include the first name in the response


@action('delete_contact')
@action.uses(url_signer.verify(), db)
def delete_contact():
    id = request.params.get('id')
    assert id is not None
    db(db.contact.id == id).delete()
    return "ok"

@action('edit_contact', method="POST")
@action.uses(url_signer.verify(), db)
def edit_contact():
    # Updates the db record.
    id = request.json.get("id")
    field = request.json.get("field")
    value = request.json.get("value")
    print(id, field, value)
    db(db.contact.id == id).update(**{field: value})
    if field == 'color':
        session['selectedColor'] = value  # Store the selected color in the session
    time.sleep(1) # debugging
    return "ok"

@action('upload_thumbnail', method="POST")
@action.uses(url_signer.verify(), db)
def upload_thumbnail():
    contact_id = request.json.get("contact_id")
    thumbnail = request.json.get("thumbnail")
    db(db.contact.id == contact_id).update(thumbnail=thumbnail)
    return "ok"

@action('set_follow', method='POST')
@action.uses(auth.user, url_signer.verify(), db)
def set_follow():
    user_id = request.json.get('user_id')
    follow = request.json.get('follow')

    if follow:
        db.follow.insert(user_id=auth.current_user.get('id'), follows_id=user_id)
    else:
        db((db.follow.user_id == auth.current_user.get('id')) & (db.follow.follows_id == user_id)).delete()
    return 'ok'

@action('set_add_status', method='POST')
@action.uses(url_signer.verify(), session)
def set_add_status():
    selected_color = request.json.get('selected_color')
    session['selectedColor'] = selected_color
    return "ok"

@action('comments/<post_id:int>')
@action.uses(db, auth.user, 'comments.html')
def comments(post_id=None):
    assert post_id is not None
    return dict(post_id=post_id)

@action('mark_contact', method='POST')
@action.uses(url_signer.verify(), db)
def mark_contact():
    contact_id = request.json.get('contact_id')
    mark = request.json.get('mark')
    contact = db.contact[contact_id]
    if contact:
        contact.update_record(mark=mark)
        marked_contact_ids = [c.id for c in db(db.contact.mark == True).select()]
        print("Marked Contact IDs:", marked_contact_ids)  # 打印被标记为 True 的所有 contact id
        return "ok"
    else:
        abort(404, "Contact not found")



@action('fav')
@action.uses('fav.html', db, auth.user, session, url_signer)
def fav():
    post = db(db.post.user_email == get_user_email()).select()
    selected_color = session.get('selectedColor', 'no-color')
    set_add_status_url = URL('set_add_status', signer=url_signer)
    mark_contact_url = URL('mark_contact', signer=url_signer)
    return dict(
        load_contacts_url=URL('load_contacts', signer=url_signer),
        add_contact_url=URL('add_contact', signer=url_signer),
        delete_contact_url=URL('delete_contact', signer=url_signer),
        edit_contact_url=URL('edit_contact', signer=url_signer),
        upload_thumbnail_url=URL('upload_thumbnail', signer=url_signer),
        post=post,
        my_callback_url=URL('my_callback', signer=url_signer),
        get_users_url=URL('get_users', signer=url_signer),
        follow_url=URL('set_follow', signer=url_signer),
        selectedColor=selected_color,
        set_add_status_url=set_add_status_url,
        mark_contact_url = mark_contact_url,
    )




