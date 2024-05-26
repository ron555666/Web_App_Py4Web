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

import datetime
import random

from py4web import action, request, abort, redirect, URL
from yatl.helpers import A
from .common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash
from py4web.utils.url_signer import URLSigner
from .models import get_username

url_signer = URLSigner(session)

# Some constants.
MAX_RETURNED_USERS = 20 # Our searches do not return more than 20 users.
MAX_RESULTS = 20 # Maximum number of returned meows.

@action('index')
@action.uses('index.html', db, auth.user, url_signer)
def index():
    return dict(
        # COMPLETE: return here any signed URLs you need.
        get_users_url = URL('get_users', signer=url_signer),
        follow_url=URL('set_follow', signer=url_signer),
        unfollow_url=URL('set_unfollow', signer=url_signer),
        search_url=URL('search', signer=url_signer),
        publish_url=URL('publish', signer=url_signer),
        get_meows_url=URL('get_meows', signer=url_signer),
    )

# function to have a left join, join the followed status to user
def add_followed_status(query):
    joinCondition = (db.follow.following == db.auth_user.id)

    users = db(query).select(
        db.auth_user.id,
        db.auth_user.username,
        db.follow.got_followed_status,
        left=db.follow.on(joinCondition)
    )

    results = []
    for user in users:
        user_infos = {
            "id": user.auth_user.id,
            "username": user.auth_user.username,
            "got_followed_status": user.follow.got_followed_status
        }
        results.append(user_infos)

    return results

@action("get_users", method='GET')
@action.uses(db, auth.user)
def get_users():
    # subList = (
    #         (db.follow.follower == auth.current_user.get('id')) &
    #         (db.follow.following == db.auth_user.id)
    # )

    query = db.auth_user.username.startswith("_")
    users = add_followed_status(query)

    users = sorted(users, key=lambda user: (not user['got_followed_status'], user['id']))
    users = users[0:MAX_RETURNED_USERS]

    return dict(users=users)

@action("set_follow", method="POST")
@action.uses(db, auth.user, url_signer.verify())
def set_follow():
    print("set_follow clicked")
    user_id = request.json.get('user_id')
    #print("for follow, Controller Received user ID:", user_id)

    user = db.auth_user[user_id]
    #print(user)

    follower_id = auth.current_user.get('id')
    login_guy = db.auth_user[follower_id]
    #print(login_guy)
    #print("follower_id:", follower_id)

    # Check if the current user is already following the target user
    is_following = db(
        (db.follow.follower == follower_id) & (db.follow.following == user_id)
    ).count() > 0

    if is_following:
        print("Current guy is already following the given userid.")
    else:
        db.follow.update_or_insert(
            (db.follow.follower == follower_id) & (db.follow.following == user_id),
            follower=follower_id,
            following=user_id
        )
        db.commit()
        #print("Current guy is now following the given userID.")

    query = (db.follow.follower == follower_id) & (db.follow.following == user_id)
    db(query).update(got_followed_status=True)

    db.commit()

    return "ok"

@action("set_unfollow", method="POST")
@action.uses(db, auth.user, url_signer.verify())
def set_unfollow():
    print("unfollow clicked")
    user_id = request.json.get('user_id')
    #print("for unfollow, the clicked button user ID:", user_id)

    follower_id = auth.current_user.get('id')
    login_guy = db.auth_user[follower_id]
    #print(login_guy)

    unfollowed = db(
        (db.follow.follower == follower_id) & (db.follow.following == user_id)
    ).delete()
    db.commit()

    # Update the got_followed_status
    query = (db.follow.follower == follower_id) & (db.follow.following == user_id)
    db(query).update(got_followed_status=False)
    db.commit()

    return "unfollow ok"

@action('search')
@action.uses(db)
def search():
    q = request.params.get("q")

    query = db.auth_user.username.startswith(q)
    results = add_followed_status(query)

    results = sorted(results, key=lambda user: (not user['got_followed_status'], user['id']))
    results = results[0:MAX_RETURNED_USERS]

    return dict(results=results)

@action('publish', method='POST')
@action.uses(db, auth.user, url_signer.verify())
def publish():
    content = request.json.get('content')  # get data from JSON
    print("received content is:" , content)

    meow_id = db.meow.insert(content=content, author=auth.current_user.get('id'), timestamp=datetime.datetime.now())
    meow = db.meow[meow_id]

    meows = db(db.meow).select()
    for m in meows:
        print("Meow ID:", m.id)
        print("Content:", m.content)

    return meow


@action("get_meows", method='GET')
@action.uses(db, auth.user)
def get_meows():
    meows = db().select(db.meow.ALL, orderby=~db.meow.timestamp)
    authors = db().select(db.auth_user.ALL)

    meows_with_username = []
    for meow in meows:
        author_name = ''
        for author in authors:
            if author.id == meow.author:
                author_name = author.username
                break
        meows_with_username.append(
            dict(
                id=meow.id,
                content=meow.content,
                author=author.id,
                author_name=author_name,
                timestamp=meow.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            )
        )

    return dict(meows=meows_with_username)



