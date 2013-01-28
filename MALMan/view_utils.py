from MALMan import app
import MALMan.database as DB

from flask import request, flash, abort, url_for
from flask.ext.principal import Permission, RoleNeed

from functools import wraps
from urlparse import urlparse
from math import ceil

def add_confirmation(var, confirmation):
    """add a confirmation message to a string"""
    if var != app.CHANGE_MSG:
        var += ", "
    var += confirmation
    return var


def return_flash (confirmation):
    """return a confirmation if something changed or an error if there are
    no changes
    """
    if confirmation == app.CHANGE_MSG:
        flash("No changes were specified", "error")
    else:
        flash(confirmation, 'confirmation')


def formatbool(var):
    """return a variable's boolean value in a onsistent way"""
    if var:
        return True
    else:
        return False


def accounting_categories(IN=True, OUT=True):
    """build the choices for the accounting_category_id select element, adding the type of transaction (IN or OUT) to the category name"""
    categories = DB.AccountingCategories.query.all()
    choices = []
    if IN:
        IN = [(str(category.id), category.name + " (IN)") for category in categories if category.is_revenue]
        choices.extend(IN) 
    if OUT:
        OUT = [(str(category.id), category.name + " (OUT)") for category in categories if not category.is_revenue]
        choices.extend(OUT) 
    return choices
   

def permission_required(*roles):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            perms = [Permission(RoleNeed(role)) for role in roles]
            for role in roles:
                if not Permission(RoleNeed(role)).can():
                    if role == 'member':
                        flash ('You need to be aproved as a member to access this resource', 'error') 
                        abort(401)
                    else:
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
