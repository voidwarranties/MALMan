from MALMan import app
from MALMan.database import db, User, StockItems, Role, MembershipFee, StockCategories, BarLog, CashTransaction, user_datastore, Transactions, Banks, AccountingCategories, BarAccountLog
import MALMan.forms as forms
from MALMan.flask_security.recoverable import update_password
from flask import render_template, request, redirect, flash, abort
from flask.ext.login import current_user, login_required
from flask.ext.wtf import (Form, SubmitField, FormField, BooleanField, 
    IntegerField, validators)
from flask.ext.principal import Permission, RoleNeed, Need
from flask import current_app, url_for
from werkzeug.local import LocalProxy
from functools import wraps
from datetime import datetime, date
from urlparse import urlparse

_datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)

CHANGE_MSG = "These values were updated: "
def add_confirmation(var, confirmation):
    """add a confirmation message to a string"""
    if var != CHANGE_MSG:
        var += ", "
    var += confirmation
    return var


def return_flash (confirmation):
    """return a confirmation if something changed or an error if there are
    no changes
    """
    if confirmation == CHANGE_MSG:
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
    categories = AccountingCategories.query.all()
    choices = []
    if IN:
        IN = [(category.id, category.name + " (IN)") for category in categories if category.is_revenue]
        choices.extend(IN) 
    if OUT:
        OUT = [(category.id, category.name + " (OUT)") for category in categories if not category.is_revenue]
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


from math import ceil
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

ITEMS_PER_PAGE = 10

def url_for_other_page(page):
    """this function is used by the pagination macro in jinja2 templates"""
    args = request.view_args.copy()
    args['page'] = page
    url = url_for(request.endpoint, **args)
    query = '?' + urlparse(request.url).query
    return url + query
app.jinja_env.globals['url_for_other_page'] = url_for_other_page


@app.route("/")
def index():
    if current_user and current_user.is_active() and User.query.get(current_user.id).active_member:
        # is an aproved member
        user = User.query.get(current_user.id)
        return render_template('members_account.html', user=user)
    elif current_user and current_user.is_active():
        # is logged in but not aproved yet
        return render_template('members_waiting_aproval.html')
    else:
        # is not logged in
        return redirect('login')


@app.route("/members")
@permission_required('membership')
def members():
    users = User.query.filter_by(active_member='1')
    return render_template('members.html', users=users)


@app.route("/members/approve_new_members", methods=['GET', 'POST'])
@permission_required('membership', 'members')
def approve_new_members():
    new_members = User.query.filter_by(active_member='0')
    for user in new_members:
        setattr(forms.NewMembers, 'activate_' + str(user.id), 
            BooleanField('activate user'))
    form = forms.NewMembers()
    if form.validate_on_submit():
        confirmation = CHANGE_MSG
        for user in new_members:
            new_value = forms.booleanfix(request.form, 
                'activate_' + str(user.id))
            if new_value != user.active_member:
                setattr(user, 'active_member', True)
                setattr(user, 'member_since', date.today())
                db.session.commit()
                confirmation = add_confirmation(confirmation, 
                    user.email + " was made an active member")
        return_flash(confirmation)
        return redirect(request.path)
    return render_template('members_approve_new_members.html', new_members=new_members, 
        form=form)


@app.route('/members/edit_own_account', methods=['GET', 'POST'])
@login_required
def edit_own_account():
    userdata = User.query.get(current_user.id)
    form = forms.MembersEditOwnAccount(obj=userdata)
    if form.validate_on_submit():
        confirmation = CHANGE_MSG
        atributes = ['name', 'date_of_birth', 'email', 'telephone', 'city', 
            'postalcode', 'bus', 'number', 'street', 'show_telephone', 
            'show_email']
        for atribute in atributes:
            if atribute == 'show_telephone' or atribute == 'show_email':
                old_value = formatbool(getattr(userdata, atribute))
                new_value = forms.booleanfix(request.form, atribute)
            else:
                old_value = getattr(userdata, atribute)
                new_value = request.form.get(atribute)
            if str(new_value) != str(old_value):
                user = User.query.get(current_user.id)
                setattr(user, atribute, new_value)
                db.session.commit()
                confirmation = add_confirmation(confirmation, atribute + 
                    " = " + str(new_value) + " (was " + str(old_value) + ")")
        return_flash(confirmation)
        return redirect(request.path)
    return render_template('members_edit_own_account.html', userdata=userdata, 
        form=form)


@app.route("/bar_account")
@permission_required('membership')
def bar_account():
    log = BarAccountLog.query.filter_by(user_id=current_user.id)
    log = sorted(log, key=lambda i: i.datetime, reverse=True) #sort descending
    return render_template('bar_account_log.html', log=log)

@app.route('/members/edit_<int:userid>', methods=['GET', 'POST'])
@permission_required('membership', 'members')
def members_edit(userid):
    userdata = User.query.get(userid)
    roles = Role.query.all()
    # add roles to form
    for role in roles:
        if role != 'membership':
            # check the checkbox if the user has the role
            if role in userdata.roles:
                setattr(forms.MembersEditAccount, 'perm_' + str(role.name), 
                    BooleanField(role.name, default='y'))
            else:
                setattr(forms.MembersEditAccount, 'perm_' + str(role.name), 
                    BooleanField(role.name))
    form = forms.MembersEditAccount(obj=userdata)
    del form.email
    if form.validate_on_submit():
        confirmation = CHANGE_MSG
        atributes = ['name', 'date_of_birth', 'telephone', 'city', 
            'postalcode', 'bus', 'number', 'street', 'show_telephone', 
            'show_email', 'active_member', 'membership_dues']
        permissions = [role for role in roles if role != 'membership']
        atributes.extend(permissions)
        for atribute in atributes:
            if atribute in roles:
                new_value = forms.booleanfix(request.form, 
                    'perm_' + str(atribute))
                if atribute in userdata.roles:
                    old_value = True
                else:
                    old_value = False
            elif atribute in ['show_telephone', 'show_email', 'active_member']:
                old_value = formatbool(getattr(userdata, atribute))
                new_value = forms.booleanfix(request.form, atribute)
            else:
                old_value = getattr(userdata, str(atribute))
                new_value = request.form.get(atribute)
            if str(new_value) != str(old_value):
                if atribute in roles:
                    if new_value:
                        user_datastore.add_role_to_user(userdata, atribute)
                    else:
                        user_datastore.remove_role_from_user(userdata, atribute)
                else:
                    user = User.query.get(userid)
                    setattr(user, atribute, new_value)
                confirmation = add_confirmation(confirmation, str(atribute) + 
                    " = " + str(new_value) + " (was " + str(old_value) + ")")
                db.session.commit()
        return_flash(confirmation)
        return redirect(request.path)
    return render_template('members_edit_account.html', form=form)


@app.route('/members/edit_password', methods=['GET', 'POST'])
@login_required
def members_edit_password():
    form = forms.MembersEditPassword()
    _security = LocalProxy(lambda: current_app.extensions['security'])
    _datastore = LocalProxy(lambda: _security.datastore)
    if form.validate_on_submit():
        update_password(current_user, request.form['password'])
        _datastore.commit()
        flash("your password was updated", "confirmation")
        return redirect(request.path)
    return render_template('members_edit_password.html', form=form)


@app.route("/bar")
@permission_required('membership')
def bar():
    items = StockItems.query.all()
    return render_template('bar.html', items=items)


@app.route("/bar_remove_<int:item_id>", methods=['GET', 'POST'])
@permission_required('membership', 'bar')
def bar_remove(item_id):
    item = StockItems.query.get(item_id)
    form = forms.BarRemoveItem()
    if form.validate_on_submit():
        StockItems.remove(item)
        flash('The item was removed', 'confirmation')
        return redirect(url_for('bar'))
    return render_template('bar_remove.html', item=item, form=form)


@app.route("/bar/edit_item_amounts", methods=['GET', 'POST'])
@permission_required('membership', 'bar')
def edit_item_amounts():
    items = StockItems.query.all()
    for item in items:
        setattr(forms.BarEditAmounts, 'amount_' + str(item.id), 
            IntegerField(item.name, [validators.NumberRange(min=0, 
                message='please enter a positive number')], 
            default=item.stock))
    form = forms.BarEditAmounts()
    if form.validate_on_submit():
        confirmation = CHANGE_MSG
        for item in items:
            if int(request.form["amount_" + str(item.id)]) != int(item.stock):
                changes = BarLog(
                    item_id = item.id,
                    amount = int(request.form["amount_" + str(item.id)]) - int(item.stock),
                    total_price = 0,
                    user_id = current_user.id,
                    transaction_type = "correction")
                db.session.add(changes)
                db.session.commit()
                confirmation = add_confirmation(confirmation, "stock " + 
                    item.name + " = " + request.form["amount_" + 
                    str(item.id)])
        return_flash(confirmation)
        return redirect(request.path)
    return render_template('bar_edit_item_amounts.html', form=form)


@app.route("/bar/edit_items", methods=['GET', 'POST'])
@permission_required('membership', 'bar')
def edit_items():
    items = StockItems.query.all()
    categories = StockCategories.query.all()
    for item in items:
        setattr(forms.BarEdit, str(item.id), 
            FormField(forms.BarEditItem, default=item, separator='_'))
    form = forms.BarEdit()
    for item in form:
        if item.name != 'csrf_token' and item.name != 'submit':
            item.category_id.choices = [(category.id, category.name) for category in categories]
    if form.validate_on_submit():
        confirmation = CHANGE_MSG
        for item in items:
            # only write to DB and display a confirmation if the value given in the POST does not equal the value in the DB 
            atributes = ['name' , 'price' , 'stock_max', 'category_id', 'josto']
            for atribute in atributes:
                if atribute == 'josto':
                    old_value = formatbool(getattr(item, atribute))
                    new_value = forms.booleanfix(request.form, str(item.id) + '_josto')
                else: 
                    old_value = getattr(item, atribute)
                    new_value = request.form[str(item.id) + '_' + atribute]
                if str(old_value) != str(new_value):
                    setattr(item, atribute, new_value)
                    db.session.commit()
                    if atribute == "name":
                        confirmation = add_confirmation(confirmation, 
                            old_value + " => " + new_value)
                    elif atribute == "category_id":
                        newcat = StockCategories.query.get(new_value).name
                        oldcat = StockCategories.query.get(old_value).name
                        confirmation = add_confirmation(confirmation, 
                            "category" + " " + item.name + " = \"" + newcat + 
                            "\" (was \"" + oldcat + "\")")
                    else:
                        confirmation = add_confirmation(confirmation, 
                            atribute + " " + item.name + " = " +
                            str(new_value) + " (was " + str(old_value) + ")")
        return_flash(confirmation)
        return redirect(request.path)
    return render_template('bar_edit_items.html', form=form)


@app.route("/bar/stockup", methods=['GET', 'POST'])
@permission_required('membership', 'bar')
def stockup():
    # get all stock items from josto
    items = StockItems.query.filter_by(josto=True).all()
    # we need to redefine this everytime the view gets called, otherwise the setattr's are caried over
    class StockupForm(Form):
        submit = SubmitField('ok!')
    for item in items:
        if item.stockup > 0:
            setattr(StockupForm, 'amount_' + str(item.id), 
                IntegerField(item.name, [validators.NumberRange(min=0, 
                    message='please enter a positive number')], 
                default=item.stockup))
            setattr(StockupForm, 'check_' + str(item.id), 
                BooleanField(item.name))
    form = StockupForm()
    if form.validate_on_submit():
        confirmation = CHANGE_MSG
        for item in items:
            checked = forms.booleanfix(request.form, 'check_' + str(item.id))
            if checked: 
                if int(request.form["amount_" + str(item.id)]) != 0:
                    changes = BarLog(
                        item_id = item.id,
                        amount = request.form["amount_" + str(item.id)],
                        total_price = 0,
                        user_id = current_user.id,
                        transaction_type = "stock up")
                    db.session.add(changes)
                    db.session.commit()
                    confirmation = add_confirmation(confirmation, "stock " + 
                        item.name + " = +" + 
                        request.form["amount_" + str(item.id)])
        return_flash(confirmation)
        return redirect(request.path)
    return render_template('bar_stockup.html', form=form)


@app.route("/bar/log", defaults={'page': 1}, methods=['GET', 'POST'])
@app.route("/bar/log/page/<int:page>", methods=['GET', 'POST'])
@permission_required('membership', 'bar')
def bar_log(page):
    log = BarLog.query.order_by(BarLog.datetime.desc())
    item_count = len(log.all())
    log = log.paginate(page, ITEMS_PER_PAGE, False).items
    if not log and page != 1:
        abort(404)
    pagination = Pagination(page, ITEMS_PER_PAGE, item_count)
    form = forms.BarLog()
    if form.validate_on_submit():
        changes = BarLog.query.get(request.form["revert"])
        BarLog.remove(changes)
        flash('The change was reverted', 'confirmation')
        return redirect(request.path)
    return render_template('bar_log.html', log=log, pagination=pagination, form=form)


@app.route("/bar/add_item", methods=['GET', 'POST'])
@permission_required('membership', 'bar')
def add_item():
    categories = StockCategories.query.all()
    form = forms.BarAddItem()
    form.category_id.choices = [(category.id, category.name) for category in categories]
    if form.validate_on_submit():
        josto = forms.booleanfix(request.form, 'josto')
        changes = StockItems(request.form["name"], request.form["stock_max"], 
            request.form["price"], request.form["category_id"], josto)
        db.session.add(changes)
        db.session.commit()
        flash("added stock item: " + request.form["name"], "confirmation")
        return redirect(request.path)
    return render_template('bar_add_item.html', form=form)


@app.route("/accounting")
@permission_required('membership')
def accounting():
    banks = Banks.query.all()
    running_account = CashTransaction.query.all()
    running_acount_balance = sum(transaction.amount for transaction in running_account)
    return render_template('accounting.html', banks=banks, running_acount_balance=running_acount_balance)


@app.route("/accounting/log", defaults={'page': 1}, methods=['GET', 'POST'])
@app.route('/accounting/log/page/<int:page>', methods=['GET', 'POST'])
@permission_required('membership')
def accounting_log(page):
    log = Transactions.query.filter(Transactions.date_filed != None).order_by(Transactions.id.desc())
    banks = Banks.query.all()

    form=forms.FilterTransaction()
    form.bank_id.choices.extend([(bank.id, bank.name) for bank in banks])
    form.category_id.choices.extend(accounting_categories())

    filters = request.args.get('filters', '').split(",")
    for filter in filters:
        filter = filter.split(":")
        if len(filter) > 1: #split() seems to return empty lists, don't run on those
            if filter[0] == "amount":
                if filter[1] == '1':
                    log = log.filter(Transactions.amount > 0)
                else:
                    log = log.filter(Transactions.amount < 0)
            else:
                args = {filter[0]: filter[1]}
                log = log.filter_by(**args)
            setattr(form[filter[0]], 'data', filter[1])
    
    item_count = len(log.all())
    log = log.paginate(page, ITEMS_PER_PAGE, False).items
    if not log and page != 1:
        abort(404)
    pagination = Pagination(page, ITEMS_PER_PAGE, item_count)
   
    if request.method == 'POST':
    # why doesn't 'if form.validate_on_submit():' work?   
        url = '/accounting/log?filters='
        fields = ["bank_id", "category_id", "amount"]
        for field in fields:
            if request.form[field] != '0':
                url += field + ':' + request.form[field] + ","
        return redirect(url)
    return render_template('accounting_log.html', log=log, form=form, pagination=pagination)


@app.route("/accounting/cashlog", defaults={'page': 1})
@app.route('/accounting/cashlog/page/<int:page>')
@permission_required('membership', 'finances')
def accounting_cashlog(page):
    log = CashTransaction.query.order_by(CashTransaction.id.desc())
    
    item_count = len(log.all())
    log = log.paginate(page, ITEMS_PER_PAGE, False).items
    if not log and page != 1:
        abort(404)
    pagination = Pagination(page, ITEMS_PER_PAGE, item_count)
   
    return render_template('accounting_cashlog.html', log=log, pagination=pagination)


@app.route("/accounting/request_reimbursement", methods=['GET', 'POST'])
@permission_required('membership')
def accounting_request_reimbursement():
    form = forms.RequestReimbursement()
    del form.bank_id, form.to_from, form.category_id
    if form.validate_on_submit():
        transaction = Transactions(
            advance_date = request.form["date"], 
            amount = "-" + request.form["amount"],
            description = request.form["description"],
            to_from = current_user.name)
        db.session.add(transaction)
        db.session.commit()
        flash("the request for reimbursement was filed", "confirmation")
        return redirect(request.path)
    return render_template('accounting_request_reimbursement.html', form=form)


@app.route("/accounting/approve_reimbursements")
@permission_required('membership', 'finances')
def accounting_approve_reimbursements():
    requests = Transactions.query.filter_by(date_filed=None)
    return render_template('accounting_approve_reimbursements.html', requests=requests)


@app.route("/accounting/approve_<int:transaction_id>", methods=['GET', 'POST'])
@permission_required('membership', 'finances')
def accounting_approve_reimbursement(transaction_id):
    banks = Banks.query.all()
    transaction = Transactions.query.get(transaction_id)
    form = forms.ApproveReimbursement(obj=transaction)
    form.bank_id.choices = [(bank.id, bank.name) for bank in banks]
    form.category_id.choices = accounting_categories(IN=False)
    if form.validate_on_submit():
        transaction.date = request.form["date"]
        transaction.amount = request.form["amount"]
        transaction.to_from = request.form["to_from"]
        transaction.description = request.form["description"]
        transaction.category_id = request.form["category_id"]
        transaction.bank_id = request.form["bank_id"]
        transaction.bank_statement_number = request.form["bank_statement_number"]
        transaction.date_filed = date.today()
        transaction.filed_by_id = current_user.id
        db.session.commit()
        flash("the transaction was filed", "confirmation")
        return redirect(request.path)
    return render_template('accounting_approve_reimbursement.html', form=form)


@app.route("/accounting/add_transaction", methods=['GET', 'POST'])
@permission_required('membership', 'finances')
def accounting_add_transaction():
    banks = Banks.query.all()
    form = forms.AddTransaction()
    form.bank_id.choices = [(bank.id, bank.name) for bank in banks]
    form.category_id.choices = accounting_categories()
    if form.validate_on_submit():
        transaction = Transactions(
            date = request.form["date"],
            amount = request.form["amount"],
            to_from = request.form["to_from"], 
            description = request.form["description"],
            category_id = request.form["category_id"],
            bank_id = request.form["bank_id"],
            date_filed = date.today(),
            filed_by_id = current_user.id
            )
        db.session.add(transaction)
        db.session.commit()
        flash("the transaction was filed", "confirmation")
        if request.form["category_id"] == '6':
            id = Transactions.query.order_by(Transactions.id.desc()).first()
            return redirect(url_for('topup_bar_account', transaction_id=id.id))    
        return redirect('/accounting/log')
    return render_template('accounting_add_transaction.html', form=form)

@app.route("/accounting/topup_bar_account_<int:transaction_id>", methods=['GET', 'POST'])
@permission_required('membership', 'finances')
def topup_bar_account(transaction_id):
    users = User.query
    form = forms.TopUpBarAccount()
    form.user_id.choices = [(user.id, user.name) for user in users.all()]
    transaction = Transactions.query.get(transaction_id)
    # why doesn't "if form.validate_on_submit():" work here?
    if request.method == "POST":
        item = BarAccountLog(
            user_id = request.form["user_id"],
            transaction_id = transaction_id)
        db.session.add(item)
        db.session.commit()
        user = users.get(request.form["user_id"])
        flash(u"\u20AC" + str(transaction.amount) + " was added to " + user.name + "'s bar account", "confirmation")
        return redirect('/accounting/log')
    return render_template('accounting_topup_bar_account.html', form=form, transaction=transaction)


@app.route("/accounting/edit_<int:transaction_id>", methods=['GET', 'POST'])
@permission_required('membership', 'finances')
def accounting_edit_transaction(transaction_id):
    banks = Banks.query.all()
    transaction = Transactions.query.get(transaction_id)
    form = forms.EditTransaction(obj=transaction)
    form.bank_id.choices = [(bank.id, bank.name) for bank in banks]
    form.category_id.choices = accounting_categories()
    if form.validate_on_submit():
        confirmation = CHANGE_MSG
        for atribute in ['date', 'amount', 'to_from', 'description', 'category_id', 'bank_id', 'bank_statement_number']:
            old_value = getattr(transaction, str(atribute))
            new_value = request.form.get(atribute)
            if str(new_value) != str(old_value):
                setattr(transaction, atribute, new_value)
                confirmation = add_confirmation(confirmation, str(atribute) + 
                    " = " + str(new_value) + " (was " + str(old_value) + ")")
                db.session.commit()
        return_flash(confirmation)
        return redirect(request.path)
    return render_template('accounting_edit_transaction.html', form=form)

@app.route("/accounting/membershipfees", defaults={'page': 1})
@app.route('/accounting/membershipfees/page/<int:page>')
@permission_required('membership', 'finances')
def accounting_membershipfees(page):
    log = MembershipFee.query
    
    item_count = len(log.all())
    log = log.paginate(page, ITEMS_PER_PAGE, False).items
    if not log and page != 1:
        abort(404)
    pagination = Pagination(page, ITEMS_PER_PAGE, item_count)
   
    return render_template('accounting_membershipfees.html', log=log, pagination=pagination)

@app.errorhandler(401)
def error_401(error):
    error = "401 Unauthorized"
    lastpage = request.referrer
    return render_template('error.html', error=error, lastpage=lastpage), 401


@app.errorhandler(403)
def error_403(error):
    error = "403 Forbidden"
    lastpage = request.referrer
    return render_template('error.html', error=error, lastpage=lastpage), 403


@app.errorhandler(404)
def error_404(error):
    error = "404 Not Found"
    lastpage = request.referrer
    return render_template('error.html', error=error, lastpage=lastpage), 404
