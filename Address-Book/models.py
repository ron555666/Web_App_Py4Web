"""
This file defines the database models
"""
import datetime

from . common import db, Field, auth, T, session
from pydal.validators import *

### Define your table below
#
# db.define_table('thing', Field('name'))
#
## always commit your models to avoid problems later
#
# db.commit()
#

def get_created_by():
    return auth.current_user.get('email') if auth.current_user else None

def get_time():
    return datetime.datetime.utcnow()

from .settings import APP_FOLDER
import os
JSON_FILE = os.path.join(APP_FOLDER, "data", "table.json")

db.define_table(
    'contact',
    #Field('id',),
    Field('firstName', requires=IS_NOT_EMPTY()),
    Field('lastName', requires=IS_NOT_EMPTY()),
    Field('created_by', default=get_created_by),
    #Field('created_by', 'reference auth_user', default=lambda: session.user_id)
)

db.contact.id.readable = db.contact.id.writable = False
db.contact.created_by.readable = db.contact.created_by.writable = False

db.contact.firstName.label = T('First Name')
db.contact.lastName.label = T('Last Name')
db.contact.created_by.label = T('Created By')

db.define_table(
    'phone',
    Field('contact_id', 'reference contact', ondelete='CASCADE'),
    Field('phone_number', 'string', requires=IS_NOT_EMPTY()),
    Field('phone_name', 'string', requires=IS_NOT_EMPTY()),
)

db.phone.contact_id.readable = db.phone.contact_id.writable = False

db.commit()


