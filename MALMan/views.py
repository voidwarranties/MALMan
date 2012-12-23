import re
from MALMan import app, User, Dranken, roles_users, Role, Drankcat, stock_oorsprong, Dranklog, db, user_datastore
import forms
from flask import render_template, request, redirect, flash, abort
from flask.ext.login import current_user, login_required
from flask_security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin
from flask_security.forms import ConfirmRegisterForm
from flask_security.recoverable import update_password
from flask.ext.wtf import Form as BaseForm, TextField, PasswordField, SubmitField, HiddenField, FormField, Required, NumberRange, BooleanField, IntegerField, EqualTo, Email, ValidationError, Length, validators, ListWidget
from flask.ext.principal import Principal, Permission, RoleNeed, Need
try:
    from flaskext.sqlalchemy import SQLAlchemy
except ImportError:
    from flask_sqlalchemy import SQLAlchemy
from flask import current_app
from werkzeug.local import LocalProxy
from functools import wraps
from datetime import date
_datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)

aanpassing = "These values were updated: "
error = ""
def add_confirmation(var, string):
    if var != aanpassing:
        var += ", "
    var += string
    return var
def return_flash (confirmation):
    if confirmation == aanpassing:
        flash("No changes were specified", "error")
    else:
        flash(confirmation, 'confirmation')

def formatbool(var):
    '''take a boolean variable and output it the same way everytime'''
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
                        flash('You need the permission \'' + str(role) + '\' to access this resource.', 'error')
                        abort(403)
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper

@app.route("/")
def index():
    if current_user and current_user.is_active() and User.query.get(current_user.id).actief_lid:
        # is an aproved member
        return render_template('account.html')
    elif current_user and current_user.is_active():
        # is logged in but not aproved yet
        user = current_user.email
        return render_template('waiting_aproval.html')
    else:
        # is not logged in
        return redirect('login')

@app.route("/leden")
@permission_required('membership', 'members')
def ledenlijst():
    users = User.query.filter_by(actief_lid='1')
    perm_members = Permission(Need('role', 'members')).can()
    return render_template('ledenlijst.html', perm_members=perm_members, users=users)

@app.route("/new_members", methods=['GET', 'POST'])
@permission_required('membership', 'members')
def new_members():
    new_members = User.query.filter_by(actief_lid='0')
    for user in new_members:
        setattr(forms.new_members, 'activate_' + str(user.id), BooleanField('Activate User'))
    form = forms.new_members()

    if form.validate_on_submit():
        confirmation = ''
        for user in new_members:
            var = request.form.get('activate_' + str(user.id))
            # Hack to interpret booleans correctly
            if var == None:
                var = False
            else:
                var = True
            oldvar = str(user.actief_lid)
            if var != user.actief_lid:
                setattr(user, 'actief_lid', True)
                setattr(user, 'member_since', date.today())
                db.session.commit()
                if confirmation != '':
                    confirmation += ", "
                confirmation += user.email + " was made an active member"
        return_flash(confirmation)
        return redirect(request.path)
    return render_template('new_members.html', new_members=new_members, form=form)

@app.route('/leden_edit_own_account', methods=['GET', 'POST'])
@login_required
def leden_edit_own():
    userdata = User.query.get(current_user.id)
    form = forms.leden_edit_own_account(obj=userdata)
    if form.validate_on_submit():
        confirmation = aanpassing
        atributes = ['name', 'geboortedatum', 'email', 'telephone', 'gemeente', 'postalcode', 'bus', 'number', 'street', 'show_telephone', 'show_email']
        for atribute in atributes:
            var = request.form.get(atribute)
            # Hack to interpret booleans correctly
            if var == None:
                var = False
            elif var == "y":
                var = True
            oldvar = str(getattr(userdata, atribute))
            if str(var) != oldvar:
                obj = User.query.get(current_user.id)
                setattr(obj, atribute, var)
                db.session.commit()
                confirmation = add_confirmation(confirmation, atribute + " = " + str(var) + " (was " + oldvar + ")")
        return_flash(confirmation)
        return redirect(request.path)
    return render_template('leden_edit_own_account.html', userdata=userdata, form=form)

@app.route('/leden_edit_password', methods=['GET', 'POST'])
@login_required
def leden_edit_password():
    form = forms.leden_edit_password()
    _security = LocalProxy(lambda: current_app.extensions['security'])
    _datastore = LocalProxy(lambda: _security.datastore)
    if form.validate_on_submit():
        update_password(current_user, request.form['password'])
        _datastore.commit()
        flash("your password was updated", "confirmation")
        return redirect(request.path)
    return render_template('leden_edit_password.html', form=form)

@app.route('/leden_edit_<int:userid>', methods=['GET', 'POST'])
@permission_required('membership', 'members')
def leden_edit(userid):
    userdata = User.query.get(userid)
    roles = Role.query.all()
    # add roles to form
    for role in roles:
        if role != 'membership':
            # check the checkbox if the user has the role
            if role in userdata.roles:
                setattr(forms.leden_edit_account, 'perm_' + str(role.name), BooleanField(role.name, default='y'))
            else:
                setattr(forms.leden_edit_account, 'perm_' + str(role.name), BooleanField(role.name))
    form = forms.leden_edit_account(obj=userdata)
    del form.email
    if form.validate_on_submit():
        confirmation = aanpassing
        atributes = ['name', 'geboortedatum', 'telephone', 'gemeente', 'postalcode', 'bus', 'number', 'street', 'show_telephone', 'show_email', 'actief_lid', 'membership_dues']
        for atribute in atributes:
            var = request.form.get(atribute)
            # Hack to interpret booleans correctly
            if var == None:
                var = False
            elif var == "y":
                var = True
            oldvar = str(getattr(userdata, atribute))
            if str(var) != oldvar:
                obj = User.query.get(userid)
                setattr(obj, atribute, var)
                db.session.commit()
                if confirmation != aanpassing:
                    confirmation += ", "
                confirmation += atribute + " = " + str(var) + " (was " + oldvar + ")"
        for permission_field in roles:
            if permission_field != "membership":
                var = request.form.get('perm_' + str(permission_field))
                # Hack to interpret booleans correctly
                if var == None:
                    var = False
                else:
                    var = True
                if permission_field in userdata.roles:
                    oldvar = True
                else:
                    oldvar = False
                # Only update changed values
                if var != oldvar:
                    #check if we are adding or removing permissions
                    if var:
                        # add permission
                        role = Role.query.filter_by(name=permission_field).first()
                        user_datastore.add_role_to_user(userdata, role)
                        db.session.commit()
                        # confirmation
                        if confirmation != aanpassing:
                            confirmation += ", "
                        confirmation += "added permission for " + str(permission_field)
                    else:
                        # remove permission
                        role = Role.query.filter_by(name=permission_field).first()
                        user_datastore.remove_role_from_user(userdata, role)
                        db.session.commit()
                    confirmation = add_confirmation(confirmation, "removed permission for " + str(permission_field))
        return_flash(confirmation)
        return redirect(request.path)
    return render_template('leden_edit_account.html', form=form)

@app.route("/stock")
@permission_required('membership')
def stock():
    dranken = Dranken.query.all()
    return render_template('stock.html', lijst=dranken)

@app.route("/stock_tellen", methods=['GET', 'POST'])
@permission_required('membership', 'stock')
def stock_tellen():
    dranken = Dranken.query.all()
    for drank in dranken:
        setattr(forms.stock_tellen, 'amount_' + str(drank.id), IntegerField(drank.naam, [
            validators.NumberRange(min=0, message='please enter a positive number')], default=drank.stock))
    form = forms.stock_tellen()
    if form.validate_on_submit():
        confirmation = aanpassing
        for drankobject in dranken:
            # only write to DB and display a confirmation for ids for which the amount_id we received in the POST does not equal the value in the DB 
            if int(request.form["amount_" + str(drankobject.id)]) != int(drankobject.stock):
                changes = Dranklog(drankobject.id, (int(request.form["amount_" + str(drankobject.id)]) - int(drankobject.stock)), 0, 0, "correctie") #userID moet nog worden ingevuld naar de user die dit toevoegt
                db.session.add(changes)
                db.session.commit()
                confirmation = add_confirmation(confirmation, "stock " + drankobject.naam + " = " + request.form["amount_" + str(drankobject.id)])
        return_flash(confirmation)
        return redirect(request.path)
    return render_template('stock_tellen.html', lijst=dranken, form=form)

@app.route("/stock_aanpassen", methods=['GET', 'POST'])
@permission_required('membership', 'stock')
def stock_aanpassen():
    dranken = Dranken.query.all()
    drankcats = Drankcat.query.all()
    for drank in dranken:
        setattr(forms.stock_aanpassen, str(drank.id), FormField(forms.stock_aanpassen_single, default=drank, separator='_'))
    form = forms.stock_aanpassen()
    for item in form:
        if item.name != 'csrf_token' and item.name != 'submit':
            item.categorieID.choices = [(categorie.id, categorie.beschrijving) for categorie in drankcats]
    if form.validate_on_submit():
        confirmation = aanpassing
        for drank in dranken:
            drankobject = drank
            # only write to DB and display a confirmation if the value given in the POST does not equal the value in the DB 
            atributes = ['naam' , 'prijs' , 'aanvullenTot', 'categorieID', 'josto']
            for atribute in atributes:
                if atribute == 'josto':
                    old_value = formatbool(getattr(drank, atribute))
                    new_value = forms.booleanfix(request.form, str(drank.id) + '_josto')
                else: 
                    old_value = getattr(drank, atribute)
                    new_value = request.form[str(drank.id) + '_' + atribute]
                if str(old_value) != str(new_value):
                    setattr(drank, atribute, new_value)
                    db.session.commit()
                    if atribute == "naam":
                        confirmation = add_confirmation(confirmation, old_value + " => " + new_value)
                    elif atribute == "categorieID":
                        newcat = Drankcat.query.get(new_value).beschrijving
                        oldcat = Drankcat.query.get(old_value).beschrijving
                        confirmation = add_confirmation(confirmation, "categorie" + " " + drank.naam + " = \"" + newcat + "\" (was \"" + oldcat + "\")")
                    else:
                        confirmation = add_confirmation(confirmation, atribute + " " + drank.naam + " = " + str(new_value) + " (was " + str(old_value) + ")")
        return_flash(confirmation)
        return redirect(request.path)
    return render_template('stock_aanpassen.html', form=form)

@app.route("/stock_aanvullen", methods=['GET', 'POST'])
@permission_required('membership', 'stock')
def stock_aanvullen():
    # get all stock items from josto which are not at full capacity
    jostodranken = Dranken.query.filter_by(josto=True).all()
    # we need to redefine this everytime the view gets called, otherwise the setattr's are caried over
    class stock_aanvullen_form(BaseForm):
       submit = SubmitField('ok!')
    for drank in jostodranken:
        if drank.aanvullen > 0:
            setattr(stock_aanvullen_form, 'amount_' + str(drank.id), IntegerField(drank.naam, [validators.NumberRange(min=0, message='please enter a positive number')], default=drank.aanvullen))
            setattr(stock_aanvullen_form, 'check_' + str(drank.id), BooleanField(drank.naam))
    form = stock_aanvullen_form()
    if form.validate_on_submit():
        confirmation = aanpassing
        for drank in jostodranken:
            drankopbject = Dranken.query.get(drank.id)
            checked = forms.booleanfix(request.form, 'check_' + str(drank.id))
            if checked: 
                if int(request.form["amount_" + str(drank.id)]) != 0:
                    changes = Dranklog(drank.id, request.form["amount_" + str(drank.id)], 0, 0, "aanvulling") #userID moet nog worden ingevuld naar de user die dit toevoegt
                    db.session.add(changes)
                    db.session.commit()
                    confirmation = add_confirmation(confirmation, "stock " + drankopbject.naam + " = +" + request.form["amount_" + str(drank.id)])
        return_flash(confirmation)
        return redirect(request.path)
    return render_template('stock_aanvullen.html', form=form)

@app.route("/stock_log", methods=['GET', 'POST'])
@permission_required('membership', 'stock')
def stock_log():
    log = Dranklog.query.all()
    form = forms.stock_log()
    if form.validate_on_submit():
        changes = Dranklog.query.get(request.form["revert"])
        Dranklog.remove(changes)
        flash('The change was reverted', 'confirmation')
        return redirect(request.path)
    return render_template('stock_log.html', log=log, form=form)

@app.route("/stock_toevoegen", methods=['GET', 'POST'])
@permission_required('membership', 'stock')
def stock_toevoegen():
    drankcats = Drankcat.query.all()
    form = forms.stock_toevoegen()
    form.categorieID.choices = [(categorie.id, categorie.beschrijving) for categorie in drankcats]
    if form.validate_on_submit():
        josto = forms.booleanfix(request.form, 'josto')
        changes = Dranken(request.form["naam"], request.form["aanvullenTot"], request.form["prijs"], request.form["categorieID"], josto)
        db.session.add(changes)
        db.session.commit()
        flash("stockitem toegevoegd: " + request.form["naam"], "confirmation")
        return redirect(request.path)
    return render_template('stock_toevoegen.html', form=form)

@app.route("/accounting")
def accounting():
    return render_template('accounting.html')

@app.route("/accounting_log")
def accounting_log():
    return render_template('accounting_log.html')

@app.route("/accounting_requestreimbursement")
def accounting_requestreimbursement():
    return render_template('accounting_requestreimbursement.html')

@app.route("/accounting_approvereimbursements")
@permission_required('finances')
def accounting_approvereimbursements():
    return render_template('accounting_approvereimbursements.html')

@app.route("/accounting_addtransaction")
@permission_required('finances')
def accounting_edittransation():
    return render_template('accounting_addtransaction.html')

@app.route("/accounting_edittransaction")
@permission_required('finances')
def accounting_edittransation():
    return render_template('accounting_edittransaction.html')

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
