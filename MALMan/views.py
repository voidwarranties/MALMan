from MALMan import app, User, Dranken, roles_users, Role, Drankcat, stock_oorsprong, Dranklog, db, user_datastore
from flask import render_template, request, redirect, flash
from flask.ext.login import current_user, login_required
from flask_security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin
from flask_security.forms import ConfirmRegisterForm
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
                    else:
                        flash('You need the permission \'' + str(role) + '\' to access this resource.', 'error')
                    return redirect(request.referrer or '/')
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper

@app.route("/")
def index():
    if current_user and current_user.is_active() and User.query.get(current_user.id).actief_lid:
        # is an aproved member
        user = current_user.email
        return render_template('account.html', user=user)
    elif current_user and current_user.is_active():
        # is logged in but not aproved yet
        user = current_user.email
        return render_template('waiting_aproval.html', user=user)
    else:
        # is not logged in
        return redirect('login')

@app.route("/leden")
@permission_required('membership', 'members')
def ledenlijst():
    user = current_user.email
    users = User.query.filter_by(actief_lid='1')
    perm_members = Permission(Need('role', 'members')).can()
    return render_template('ledenlijst.html', users=users, perm_members=perm_members, user=user)

@app.route("/new_members", methods=['GET', 'POST'])
@permission_required('membership', 'members')
def new_members():
    user = current_user.email
    users = User.query.filter_by(actief_lid='0')
    if request.method == 'POST':
        confirmation = ''
        for user in users:
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
    return render_template('new_members.html', users=users, user=user)

@app.route('/leden_edit_own_account', methods=['GET', 'POST'])
@login_required
def leden_edit_own():
    user = current_user.email
    userdata = User.query.get(current_user.id)
    if request.method == 'POST':
        confirmation = aanpassing
        atributes = ['name', 'geboortedatum', 'email', 'telephone', 'gemeente', 'postalcode', 'bus', 'number', 'street', 'show_telephone', 'show_email']
        for atribute in atributes:
            var = request.form.get(atribute)
            # Hack to interpret booleans correctly
            if var == None:
                var = False
            elif var == "True":
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
    return render_template('leden_edit_own_account.html', user=user, userdata=userdata)

@app.route('/leden_edit_<userid>', methods=['GET', 'POST'])
@permission_required('membership', 'members')
def leden_edit(userid):
    user = current_user.email
    userdata = User.query.get(userid)
    roles = Role.query.all()
    if request.method == 'POST':
        confirmation = aanpassing
        atributes = ['name', 'geboortedatum', 'email', 'telephone', 'gemeente', 'postalcode', 'bus', 'number', 'street', 'show_telephone', 'show_email', 'actief_lid', 'membership_dues']
        for atribute in atributes:
            var = request.form.get(atribute)
            # Hack to interpret booleans correctly
            if var == None:
                var = False
            elif var == "True":
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
    return render_template('leden_edit_account.html', user=user, userdata=userdata, roles=roles)

@app.route("/stock")
@permission_required('membership')
def stock():
    user = current_user.email
    dranken = Dranken.query.all()
    return render_template('stock.html', lijst=dranken, user=user)

@app.route("/stock_tellen", methods=['GET', 'POST'])
@permission_required('membership', 'stock')
def stock_tellen():
    user = current_user.email
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
    return render_template('stock_tellen.html', lijst=dranken, user=user)

@app.route("/stock_aanpassen", methods=['GET', 'POST'])
@permission_required('membership', 'stock')
def stock_aanpassen():
    user = current_user.email
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
    return render_template('stock_aanpassen.html', lijst=dranken, categorieen=drankcats, oorsprongen=oorsprongen, user=user)

@app.route("/stock_aanvullen", methods=['GET', 'POST'])
@permission_required('membership', 'stock')
def stock_aanvullen():
    user = current_user.email
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
    return render_template('stock_aanvullen.html', lijst=dranken, user=user)

@app.route("/stock_log", methods=['GET', 'POST'])
@permission_required('membership', 'stock')
def stock_log():
    user = current_user.email
    if request.method == 'POST': 
        changes = Dranklog.query.get(request.form["revert"])
        Dranklog.remove(changes)
    log = Dranklog.query.all()
    return render_template('stock_log.html', log=log, user=user)

@app.route("/stock_toevoegen", methods=['GET', 'POST'])
@permission_required('membership', 'stock')
def stock_toevoegen():
    user = current_user.email
    drankcats = Drankcat.query.all()
    oorsprongen = stock_oorsprong.query.all()
    if request.method == 'POST': 
        changes = Dranken(request.form["naam"], request.form["aanvullenTot"], request.form["prijs"], request.form["categorieID"], request.form["josto"])
        db.session.add(changes)
        db.session.commit()
        flash("stockitem toegevoegd: " + request.form["naam"], "confirmation")
    return render_template('stock_toevoegen.html', categorieen=drankcats, oorsprongen=oorsprongen, user=user)

@app.route("/accounting")
def accounting():
    user = current_user.email
    return render_template('accounting.html', user=user)

@app.route("/accounting_log")
def accounting_log():
    user = current_user.email
    return render_template('accounting_log.html', user=user)

@app.route("/accounting_requestreimbursement")
def accounting_requestreimbursement():
    user = current_user.email
    return render_template('accounting_requestreimbursement.html', user=user)

@app.route("/accounting_approvereimbursements")
@permission_required('finances')
def accounting_approvereimbursements():
    user = current_user.email
    return render_template('accounting_approvereimbursements.html', user=user)

@app.route("/accounting_addtransaction")
@permission_required('finances')
def accounting_edittransation():
    user = current_user.email
    return render_template('accounting_addtransaction.html', user=user)

@app.route("/accounting_edittransaction")
@permission_required('finances')
def accounting_edittransation():
    user = current_user.email
    return render_template('accounting_edittransaction.html', user=user)