from MALMan import app, User, Dranken, roles_users, Role, Drankcat, stock_oorsprong, Dranklog, db, user_datastore
from flask import render_template, request, redirect, flash
from flask.ext.login import current_user, login_required
from flask_security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin
from flask_security.forms import ConfirmRegisterForm
from flask.ext.wtf import Form as BaseForm, TextField, PasswordField, SubmitField, HiddenField, Required, BooleanField, EqualTo, Email, ValidationError, Length, validators
from flask.ext.principal import Principal, Permission, RoleNeed, Need
try:
    from flaskext.sqlalchemy import SQLAlchemy
except ImportError:
    from flask_sqlalchemy import SQLAlchemy
from flask import current_app
from werkzeug.local import LocalProxy
_datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)

permission_stock = Permission(RoleNeed('stock'))
permission_members = Permission(RoleNeed('members'))

aanpassing = "These values were updated: "
error = ""

@app.route("/")
def index():
    if current_user.is_active() == True:
        user = current_user.email
        return render_template('account.html', user=user)
    else:
        return redirect('login')

@app.route("/leden")
@login_required
def ledenlijst():
    user = current_user.email
    users = User.query.all()
    perm_members = Permission(Need('role', 'members')).can()
    return render_template('ledenlijst.html', users=users, perm_members=perm_members, user=user)

@app.route('/leden_edit_own_account', methods=['GET', 'POST'])
@login_required
def leden_edit_own():
    user = current_user.email
    userdata = User.query.filter_by(id=current_user.id).first()
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
            flash("Er zijn geen veranderingen door te voeren", "error")
        else: 
            flash(confirmation, "confirmation")
    return render_template('leden_edit_own_account.html', user=user, userdata=userdata)

@app.route('/leden_edit_<userid>', methods=['GET', 'POST'])
@login_required
@permission_members.require(http_exception=403)
def leden_edit(userid):
    user = current_user
    userdata = User.query.filter_by(id=current_user.id).first()
    roles = Role.query.all()
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
                obj = User.query.get(userid)
                setattr(obj, atribute, var)
                db.session.commit()
                if confirmation != aanpassing:
                    confirmation += ", "
                confirmation += atribute + " = " + str(var) + " (was " + oldvar + ")"
        for atribute in ['stock','members']:
            var = request.form.get('perm_' + atribute)
            # Hack to interpret booleans correctly
            if var == None:
                var = False
            else:
                var = True
            if atribute in userdata.roles:
                oldvar = True
            else:
                oldvar = False
            # Only update changed values
            if var != oldvar:
                #check if we are adding or removing permissions
                if var:
                    ## add permission
                    # role = Role.query.filter_by(name=atribute).first()
                    # user_datastore.add_role_to_user(userdata, role)
                    # confirmation
                    if confirmation != aanpassing:
                        confirmation += ", "
                    confirmation += "added permission for " + atribute
                else:
                    ## remove permission
                    # changes = roles_users.query.filter_by(user_id=userid).filter_by(role_id=atribute).first()
                    # roles_users.remove(changes)
                    if confirmation != aanpassing:
                        confirmation += ", "
                    confirmation += "removed permission for " + atribute
        if confirmation == aanpassing:
            flash("Er zijn geen veranderingen door te voeren", "error")
        else: 
            flash(confirmation, "confirmation")
    return render_template('leden_edit_account.html', user=user, userdata=userdata, roles=roles)

# test functions in user_datastore
@app.route("/test")
def test():
    userdata = User.query.filter_by(id='4')
    user_datastore.delete_user(userdata)
    return 'test'

@app.route("/stock")
@login_required
def stock():
    user = current_user.email
    dranken = Dranken.query.all()
    return render_template('stock.html', lijst=dranken, user=user)

@app.route("/stock_tellen", methods=['GET', 'POST'])
@login_required
@permission_stock.require(http_exception=403)
def stock_tellen():
    user = current_user.email
    dranken = Dranken.query.all()
    if request.method == 'POST':
        confirmation = aanpassing
        for ind in request.form.getlist('check[]'):
            drankobject = Dranken.query.filter_by(id=ind).first()
            # only write to DB and display a confirmation for ids for which the amount_id we received in the POST does not equal the value in the DB 
            if int(request.form["amount_" + ind]) != int(drankobject.stock):
                changes = Dranklog(ind, (int(request.form["amount_" + ind]) - int(drankobject.stock)), 0, 0, "correctie") #userID moet nog worden ingevuld naar de user die dit toevoegt
                db.session.add(changes)
                db.session.commit()
                if confirmation != aanpassing:
                    confirmation += ", "
                confirmation += "stock " + drankobject.naam + " = " + request.form["amount_" + ind]
        if confirmation == aanpassing:
            flash("Er zijn geen veranderingen door te voeren", "error")
        else:
            flash(confirmation, "confirmation")
    return render_template('stock_tellen.html', lijst=dranken, user=user)

@app.route("/stock_aanpassen", methods=['GET', 'POST'])
@login_required
@permission_stock.require(http_exception=403)
def stock_aanpassen():
    user = current_user.email
    dranken = Dranken.query.all()
    drankcats = Drankcat.query.all()
    oorsprongen = stock_oorsprong.query.all()
    if request.method == 'POST':
        confirmation = aanpassing
        for ind in request.form.getlist('ind[]'):
            drankobject = Dranken.query.filter_by(id=ind).first()
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
                        newcat = Drankcat.query.filter_by(id=request.form[atribute + "_" + ind]).first().beschrijving
                        oldcat = Drankcat.query.filter_by(id=oudewaarde).first().beschrijving
                        confirmation += "categorie" + " " + drankobject.naam + " = \"" + newcat + "\" (was \"" + oldcat + "\")"
                    else:
                        confirmation += atribute + " " + drankobject.naam + " = " + request.form[atribute + "_" + ind] + " (was " + oudewaarde + ")"
        if confirmation == aanpassing:
            flash("Er zijn geen veranderingen door te voeren", "error")
        else: 
            flash(confirmation, "confirmation")
    return render_template('stock_aanpassen.html', lijst=dranken, categorieen=drankcats, oorsprongen=oorsprongen, user=user)

@app.route("/stock_aanvullen", methods=['GET', 'POST'])
@login_required
@permission_stock.require(http_exception=403)
def stock_aanvullen():
    user = current_user.email
    dranken = Dranken.query.filter_by(josto=True).all()
    if request.method == 'POST': 
        confirmation = aanpassing
        for ind in request.form.getlist('check[]'):
            drankopbject = Dranken.query.filter_by(id=ind).first()
            if int(request.form["amount_" + ind]) != 0:
                changes = Dranklog(ind, request.form["amount_" + ind], 0, 0, "aanvulling") #userID moet nog worden ingevuld naar de user die dit toevoegt
                db.session.add(changes)
                db.session.commit()
                if confirmation != aanpassing:
                    confirmation += ", "
                confirmation += "stock " + drankopbject.naam + " = +" + request.form["amount_" + ind]
        if confirmation == aanpassing:
            flash('Er zijn geen veranderingen door te voeren', 'error')
        else:
            flash(confirmation, 'confirmation')
    return render_template('stock_aanvullen.html', lijst=dranken, user=user)

@app.route("/stock_log", methods=['GET', 'POST'])
@login_required
def stock_log():
    user = current_user.email
    if request.method == 'POST': 
        changes = Dranklog.query.filter_by(id=request.form["revert"]).first()
        Dranklog.remove(changes)
    log = Dranklog.query.all()
    return render_template('stock_log.html', log=log, user=user)

@app.route("/stock_toevoegen", methods=['GET', 'POST'])
@login_required
@permission_stock.require(http_exception=403)
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

@app.route("/boekhouding")
@login_required
def boekhouding():
    user = current_user.email
    return render_template('boekhouding.html', user=user)

@app.errorhandler(403)
def forbidden(error):
    return render_template('403.html'), 403