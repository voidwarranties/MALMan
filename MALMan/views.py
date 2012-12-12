from MALMan import app, User, Dranken, roles_users, Role, Drankcat, stock_oorsprong, Dranklog, db, user_datastore
from forms import new_members_form, leden_edit_own_account_form, leden_edit_account_form, leden_edit_password_form
from flask import render_template, request, redirect, flash, abort
from flask.ext.login import current_user, login_required
from flask_security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin
from flask_security.forms import ConfirmRegisterForm
from flask_security.recoverable import update_password
from flask.ext.wtf import Form as BaseForm, TextField, PasswordField, SubmitField, HiddenField, Required, NumberRange, BooleanField, EqualTo, Email, ValidationError, Length, validators
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
def nothingchanged():
    flash("No changes were specified", "error")

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
        setattr(new_members_form, 'activate_' + str(user.id), BooleanField('Activate User'))
    form = new_members_form()

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
        if confirmation == '':
            nothingchanged()
        else: 
            flash(confirmation, "confirmation")
        return redirect(request.path)
    return render_template('new_members.html', new_members=new_members, new_members_form=form)

@app.route('/leden_edit_own_account', methods=['GET', 'POST'])
@login_required
def leden_edit_own():
    userdata = User.query.get(current_user.id)
    form = leden_edit_own_account_form(obj=userdata)
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
                if confirmation != aanpassing:
                    confirmation += ", "
                confirmation += atribute + " = " + str(var) + " (was " + oldvar + ")"
        if confirmation == aanpassing:
            nothingchanged()
        else: 
            flash(confirmation, "confirmation")
        return redirect(request.path)
    return render_template('leden_edit_own_account.html', userdata=userdata, form=form)

@app.route('/leden_edit_password', methods=['GET', 'POST'])
@login_required
def leden_edit_password():
    form = leden_edit_password_form()
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
                setattr(leden_edit_account_form, 'perm_' + str(role.name), BooleanField(role.name, default='y'))
            else:
                setattr(leden_edit_account_form, 'perm_' + str(role.name), BooleanField(role.name))
    form = leden_edit_account_form(obj=userdata)
    del form.email, form.password, password_confirm
    if request.method == 'POST':
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
                        if confirmation != aanpassing:
                            confirmation += ", "
                        confirmation += "removed permission for " + str(permission_field)
        if confirmation == aanpassing:
            nothingchanged()
        else: 
            flash(confirmation, "confirmation")
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
    if request.method == 'POST':
        confirmation = aanpassing
        for ind in request.form.getlist('check[]'):
            drankobject = Dranken.query.get(ind)
            # only write to DB and display a confirmation for ids for which the amount_id we received in the POST does not equal the value in the DB 
            if int(request.form["amount_" + ind]) != int(drankobject.stock):
                changes = Dranklog(ind, (int(request.form["amount_" + ind]) - int(drankobject.stock)), 0, 0, "correctie") #userID moet nog worden ingevuld naar de user die dit toevoegt
                db.session.add(changes)
                db.session.commit()
                if confirmation != aanpassing:
                    confirmation += ", "
                confirmation += "stock " + drankobject.naam + " = " + request.form["amount_" + ind]
        if confirmation == aanpassing:
            nothingchanged()
        else:
            flash(confirmation, "confirmation")
    return render_template('stock_tellen.html', lijst=dranken)

@app.route("/stock_aanpassen", methods=['GET', 'POST'])
@permission_required('membership', 'stock')
def stock_aanpassen():
    dranken = Dranken.query.all()
    drankcats = Drankcat.query.all()
    oorsprongen = stock_oorsprong.query.all()
    if request.method == 'POST':
        confirmation = aanpassing
        for ind in request.form.getlist('ind[]'):
            drankobject = Dranken.query.get(ind)
            # only write to DB and display a confirmation if the value given in the POST does not equal the value in the DB 
            atributes = ['naam', 'prijs', 'aanvullenTot', 'categorieID'] #josto is not implemented jet
            for atribute in atributes:
                if str(request.form[atribute + "_" + ind]) != str(getattr(drankobject, atribute)):
                    oudewaarde = str(getattr(drankobject, atribute))
                    obj = Dranken.query.get(ind)
                    setattr(obj, atribute, request.form[atribute + "_" + ind])
                    db.session.commit()
                    if confirmation != aanpassing:
                        confirmation += ", "
                    if atribute == "naam":
                        confirmation += oudewaarde + " => " + request.form["naam_" + ind]
                    elif atribute == "categorieID":
                        newcat = Drankcat.query.get(request.form[atribute + "_" + ind]).beschrijving
                        oldcat = Drankcat.query.get(oudewaarde).beschrijving
                        confirmation += "categorie" + " " + drankobject.naam + " = \"" + newcat + "\" (was \"" + oldcat + "\")"
                    else:
                        confirmation += atribute + " " + drankobject.naam + " = " + request.form[atribute + "_" + ind] + " (was " + oudewaarde + ")"
        if confirmation == aanpassing:
            nothingchanged()
        else: 
            flash(confirmation, "confirmation")
    return render_template('stock_aanpassen.html', lijst=dranken, categorieen=drankcats, oorsprongen=oorsprongen)

@app.route("/stock_aanvullen", methods=['GET', 'POST'])
@permission_required('membership', 'stock')
def stock_aanvullen():
    dranken = Dranken.query.filter_by(josto=True).all()
    if request.method == 'POST': 
        confirmation = aanpassing
        for ind in request.form.getlist('check[]'):
            drankopbject = Dranken.query.get(ind)
            if int(request.form["amount_" + ind]) != 0:
                changes = Dranklog(ind, request.form["amount_" + ind], 0, 0, "aanvulling") #userID moet nog worden ingevuld naar de user die dit toevoegt
                db.session.add(changes)
                db.session.commit()
                if confirmation != aanpassing:
                    confirmation += ", "
                confirmation += "stock " + drankopbject.naam + " = +" + request.form["amount_" + ind]
        if confirmation == aanpassing:
            nothingchanged()
        else:
            flash(confirmation, 'confirmation')
    return render_template('stock_aanvullen.html', lijst=dranken)

@app.route("/stock_log", methods=['GET', 'POST'])
@permission_required('membership', 'stock')
def stock_log():
    if request.method == 'POST': 
        changes = Dranklog.query.get(request.form["revert"])
        Dranklog.remove(changes)
    log = Dranklog.query.all()
    return render_template('stock_log.html', log=log)

@app.route("/stock_toevoegen", methods=['GET', 'POST'])
@permission_required('membership', 'stock')
def stock_toevoegen():
    drankcats = Drankcat.query.all()
    oorsprongen = stock_oorsprong.query.all()
    if request.method == 'POST': 
        changes = Dranken(request.form["naam"], request.form["aanvullenTot"], request.form["prijs"], request.form["categorieID"], request.form["josto"])
        db.session.add(changes)
        db.session.commit()
        flash("stockitem toegevoegd: " + request.form["naam"], "confirmation")
    return render_template('stock_toevoegen.html', categorieen=drankcats, oorsprongen=oorsprongen)

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