"""
This file defines the database models
"""

import datetime
from .common import db, Field, auth
from pydal.validators import *


def get_user_email():
    return auth.current_user.get('email') if auth.current_user else None

def get_time():
    return datetime.datetime.utcnow()


### Define your table below
#
# db.define_table('thing', Field('name'))
#
## always commit your models to avoid problems later

db.define_table('contact',
                Field('first_name'),
                Field('title'),
                Field('thumbnail', 'text'),
                Field('caption'),
                Field('color'),
                Field('mark', 'boolean', default=False),
                )

db.define_table(
    'post',
    Field('user_name', requires=IS_NOT_EMPTY()),
    #Field('like', 'integer', default=0, requires=IS_INT_IN_RANGE(0, 1e6)),
    Field('user_email', default=get_user_email),
    Field('contact_id', 'reference contact')
)

db.define_table(
    'comment',
    Field('post_id', 'reference post'),
    Field('content', 'text'),
)

db.define_table(
    'follow',
    Field('user_id', 'reference auth_user'),
    Field('follows_id', 'reference auth_user')
)

db.commit()

