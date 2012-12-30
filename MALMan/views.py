from MALMan import app
from MALMan.database import User, StockItems, Role, StockCategories, BarLog, db, user_datastore
import MALMan.forms as forms
from MALMan.flask_security.recoverable import update_password
from flask import render_template, request, redirect, flash, abort
from flask.ext.login import current_user, login_required
from flask.ext.wtf import (Form, SubmitField, FormField, BooleanField, 
    IntegerField, validators)
from flask.ext.principal import Permission, RoleNeed, Need
from flask import current_app
from werkzeug.local import LocalProxy
from functools import wraps
from datetime import date
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


@app.route("/")
def index():
    if current_user and current_user.is_active() and User.query.get(current_user.id).active_member:
        # is an aproved member
        return render_template('members_account.html')
    elif current_user and current_user.is_active():
        # is logged in but not aproved yet
        return render_template('members_waiting_aproval.html')
    else:
        # is not logged in
        return redirect('login')


@app.route("/members")
@permission_required('membership', 'members')
def members():
    users = User.query.filter_by(active_member='1')
    perm_members = Permission(Need('role', 'members')).can()
    return render_template('members.html', perm_members=perm_members, 
        users=users)


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
                changes = BarLog(item.id, 
                    (int(request.form["amount_" + str(item.id)]) - int(item.stock))
                    , 0, current_user.id, "correction") 
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
                    changes = BarLog(item.id, 
                        request.form["amount_" + str(item.id)], 
                        0, current_user.id, "stock up") 
                    db.session.add(changes)
                    db.session.commit()
                    confirmation = add_confirmation(confirmation, "stock " + 
                        item.name + " = +" + 
                        request.form["amount_" + str(item.id)])
        return_flash(confirmation)
        return redirect(request.path)
    return render_template('bar_stockup.html', form=form)


@app.route("/bar/log", methods=['GET', 'POST'])
@permission_required('membership', 'bar')
def bar_log():
    log = BarLog.query.all()
    form = forms.BarLog()
    if form.validate_on_submit():
        changes = BarLog.query.get(request.form["revert"])
        BarLog.remove(changes)
        flash('The change was reverted', 'confirmation')
        return redirect(request.path)
    return render_template('bar_log.html', log=log, form=form)


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
    return render_template('accounting.html')


@app.route("/accounting/log")
@permission_required('membership')
def accounting_log():
    return render_template('accounting_log.html')


@app.route("/accounting/request_reimbursement")
@permission_required('membership')
def accounting_request_reimbursement():
    return render_template('accounting_request_reimbursement.html')


@app.route("/accounting/approve_reimbursements")
@permission_required('membership', 'finances')
def accounting_approve_reimbursements():
    return render_template('accounting_approve_reimbursements.html')


@app.route("/accounting/add_transaction")
@permission_required('membership', 'finances')
def accounting_edit_transation():
    return render_template('accounting_add_transaction.html')


@app.route("/accounting/edit_transaction")
@permission_required('membership', 'finances')
def accounting_edit_transation():
    return render_template('accounting_edit_transaction.html')


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
