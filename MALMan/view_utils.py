from MALMan import app
import MALMan.database as DB

from flask import request, flash, abort, url_for, current_app
from flask.ext.principal import Permission, RoleNeed
from flask.ext.login import current_user, login_required

import os
from functools import wraps
from urlparse import urlparse
from math import ceil
from werkzeug import secure_filename

def add_confirmation(var, confirmation):
    """add a confirmation message to a string"""
    if var != app.config['CHANGE_MSG']:
        var += ", "
    var += confirmation
    return var


def return_flash (confirmation):
    """return a confirmation if something changed or an error if there are
    no changes
    """
    if confirmation == app.config['CHANGE_MSG']:
        flash("No changes were specified", "error")
    else:
        flash(confirmation, 'confirmation')


def accounting_categories(IN=True, OUT=True):
    """build the choices for the accounting_category_id select element, adding the type of transaction (IN or OUT) to the category name"""
    categories = DB.AccountingCategory.query.all()
    choices = []
    if IN:
        IN = [(str(category.id), category.name + " (IN)") for category in categories if category.is_revenue]
        choices.extend(IN) 
    if OUT:
        OUT = [(str(category.id), category.name + " (OUT)") for category in categories if not category.is_revenue]
        choices.extend(OUT) 
    return choices


def membership_required():
    '''Check if a user is logged in and a member. If not, redirrect to login page or display an error'''
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated():
                return current_app.login_manager.unauthorized()
            if not current_user.active_member:
                flash ('You need to be aproved as a member to access this resource', 'error') 
                abort(403)
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper


def permission_required(*roles):
    '''Check if a user had one or more permission roles. For this the user must be logged in and a member.'''
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated():
                return current_app.login_manager.unauthorized()
            if not current_user.active_member:
                flash ('You need to be aproved as a member to access this resource', 'error') 
                abort(403)
            for role in roles:
                if not Permission(RoleNeed(role)).can():
                    flash('You need the permission \'' + str(role) + 
                        '\' to access this resource.', 'error')
                    abort(403)
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper


class Pagination(object):
    def __init__(self, page, per_page, total_count):
        self.page = page
        self.per_page = per_page
        self.total_count = total_count

    @property
    def pages(self):
        return int(ceil(self.total_count / float(self.per_page)))

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    def iter_pages(self, left_edge=2, left_current=2,
                   right_current=5, right_edge=2):
        last = 0
        for num in xrange(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and \
                num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num


def url_for_other_page(page):
    """this function is used by the pagination macro in jinja2 templates"""
    args = request.view_args.copy()
    args['page'] = page
    url = url_for(request.endpoint, **args)
    query = '?' + urlparse(request.url).query
    return url + query
app.jinja_env.globals['url_for_other_page'] = url_for_other_page


def upload_attachments(request, attachments, transaction, DB):
    confirmation = ""
    for uploaded_attachment in request.files.getlist('attachment'):
        if uploaded_attachment.filename == '': 
            break
        # add the attachment to the accounting_attachments DB table
        extension = uploaded_attachment.filename.rsplit('.', 1)[1]
        accounting_attachment = DB.AccountingAttachment(extension = extension)
        DB.db.session.add(accounting_attachment)
        DB.db.session.commit()
        # save attachment
        url = attachments.save(
            uploaded_attachment,
            name = str(accounting_attachment.id) + '.')
        # link the attachment to the transaction
        if transaction.attachments:
            getattr(transaction, 'attachments').append(accounting_attachment)
        else:
            setattr(transaction, 'attachments', [accounting_attachment])
        # write changes to DB
        DB.db.session.commit()
        confirmation = add_confirmation(confirmation, "added the attachment " + uploaded_attachment.filename)
    return confirmation
