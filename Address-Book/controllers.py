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

import uuid

"""
from py4web import action, request, abort, redirect, URL, Field
from py4web.utils.form import Form, FormStyleBulma
from py4web.utils.url_signer import URLSigner

from yatl.helpers import A
from . common import db, session, T, cache, auth, signed_url
"""

from py4web import action, request, abort, redirect, URL
from yatl.helpers import A
from .common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash, Field
from py4web.utils.url_signer import URLSigner
from .models import get_created_by
from py4web.utils.form import Form, FormStyleBulma, SPAN

url_signer = URLSigner(session)

# The auth.user below forces login.
@action('index')
@action.uses('index.html', db, auth.user, url_signer)
def index():
    rows = db(db.contact.created_by == get_created_by()).select().as_list()
    for row in rows:
        phones = db(db.phone.contact_id == row['id']).select().as_list()
        phone_numbers = []
        for phone in phones:
            phone_numbers.append(f"{phone['phone_number']} ({phone['phone_name']})")
        row['phone_numbers'] = ", ".join(phone_numbers)

    return dict(rows=rows, url_signer=url_signer)


@action('capitalize/<contact_id:int>')
def capitalize(contact_id=None):
    assert contact_id is not None
    contact = db.contact[contact_id]
    db(db.contact.id == contact_id).update(contact_name=contact.contact_name.capitalize())

@action('add_contact', method = ["GET", "POST"])
@action.uses('add_contact.html', url_signer, db, session, auth.user)
def add_contact():
    form = Form(db.contact, csrf_session = session, formstyle=FormStyleBulma)

    if form.accepted:
        redirect(URL('index'))
    return dict(form = form, url_signer=url_signer)

@action('edit_contact/<contact_id:int>', method=["GET", "POST"])
@action.uses('edit_contact.html', url_signer, db, session, auth.user)
def edit_contact(contact_id=None):
    assert contact_id is not None

    p = db.contact[contact_id]
    #print(p.created_by)
    #print(auth.current_user.get('email'))

    if p.created_by != auth.current_user.get('email'):
        redirect(URL('index'))
    if p is None:
        redirect(URL('index'))

    form = Form(db.contact, record=p, deletable=False, csrf_session = session, formstyle=FormStyleBulma)
    if form.accepted:
        redirect(URL('index'))
    return dict(form = form)

@action('delete_contact/<contact_id:int>')
@action.uses(db, session, auth.user, url_signer.verify())
def delete_contact(contact_id=None):
    assert contact_id is not None
    db(db.contact.id == contact_id).delete()
    redirect(URL('index'))

@action('edit_phones/<contact_id:int>')
@action.uses('edit_phones.html', url_signer, db, session, auth.user)
def edit_phones(contact_id=None):
    assert contact_id is not None

    phones = db(db.phone.contact_id == contact_id).select()
    #contacts = db(db.contact).select(db.contact.firstName, db.contact.lastName)

    p = db.contact[contact_id]
    first = p.firstName
    last = p.lastName
    if p is None:
        redirect(URL('index'))

    form = Form([Field('phone'), Field('kind')], csrf_session=session,
                formstyle=FormStyleBulma)

    return dict(form=form, rows = p, phones=phones, first=first, last=last, url_signer=url_signer)

@action('add_phone/<contact_id:int>', method = ["GET", "POST"])
@action.uses('add_phone.html', url_signer, db, session, auth.user)
def add_phone(contact_id=None):
    contact = db.contact[contact_id]
    rows = db.contact[contact_id]
    #phone = db.phone[phone_id]

    if not contact:
        redirect(URL('index'))

    first = contact.firstName
    last = contact.lastName

    form = Form([Field('phone'), Field('kind')], csrf_session=session,
                formstyle=FormStyleBulma)

    if form.accepted:
        db.phone.insert(contact_id=contact.id, phone_number=form.vars['phone'], phone_name=form.vars['kind'])
        redirect(URL('edit_phones', contact_id))
    return dict(form=form, rows = rows, first=first, last=last)

@action('edit_phone/<contact_id:int>/<phone_id:int>', method = ["GET", "POST"])
@action.uses('edit_phone.html', url_signer, db, session, auth.user)
def edit_phone(contact_id=None, phone_id=None):

    assert contact_id is not None
    p = db.phone[phone_id]
    con = db.contact[contact_id]
    first = con.firstName
    last = con.lastName

    form = Form([Field('phone'), Field('kind')],
                record=dict(phone=p.phone_number, kind=p.phone_name),
                deletable=False,
                csrf_session=session,
                formstyle=FormStyleBulma)

    if form.accepted:
        db(db.phone.id == phone_id).update(phone_number=form.vars['phone'], phone_name=form.vars['kind'])
        redirect(URL('edit_phones', contact_id))

    return dict(form=form, url_signer=url_signer, first=first, last=last)

@action('delete_phone/<contact_id:int>/<phone_id:int>')
@action.uses(db, session, auth.user, url_signer.verify())
def delete_phone(contact_id=None, phone_id=None):
    print("delete phone id: ", phone_id)
    assert contact_id is not None
    assert phone_id is not None
    db(db.phone.id == phone_id).delete()

    redirect(URL('edit_phones', contact_id))


