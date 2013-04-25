from MALMan import app
import MALMan.database as DB
import MALMan.forms as forms
from MALMan.view_utils import add_confirmation, return_flash, permission_required, formatbool
from flask_security.recoverable import update_password
from flask_security.utils import url_for_security

from flask import render_template, request, redirect, flash, current_app
from flask.ext.login import current_user, login_required

from werkzeug.local import LocalProxy

@app.route("/")
def index():
    if current_user and current_user.is_active() and DB.User.query.get(current_user.id).active_member:
        # is an aproved member
        user = DB.User.query.get(current_user.id)
        return render_template('my_account/overview.html', user=user)
    elif current_user and current_user.is_active():
        # is logged in but not aproved yet
        return render_template('my_account/waiting_aproval.html')
    else:
        # is not logged in
        return redirect(url_for_security('login'))


@app.route("/my_account/bar_account")
@permission_required('membership')
def account_bar_account():
    log = DB.BarAccountLog.query.filter_by(user_id=current_user.id)
    log = sorted(log, key=lambda i: i.datetime, reverse=True) #sort descending
    return render_template('my_account/bar_account_log.html', log=log)


@app.route('/my_account/edit_own_account', methods=['GET', 'POST'])
@login_required
def account_edit_own_account():
    userdata = DB.User.query.get(current_user.id)
    form = forms.MembersEditOwnAccount(obj=userdata)
    if form.validate_on_submit():
        confirmation = app.CHANGE_MSG
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
                user = DB.User.query.get(current_user.id)
                setattr(user, atribute, new_value)
                DB.db.session.commit()
                confirmation = add_confirmation(confirmation, atribute + 
                    " = " + str(new_value) + " (was " + str(old_value) + ")")
        return_flash(confirmation)
        return redirect(request.path)
    return render_template('my_account/edit_own_account.html', userdata=userdata, 
        form=form)


@app.route('/my_account/edit_password', methods=['GET', 'POST'])
@login_required
def account_edit_own_password():
    form = forms.MembersEditPassword()
    _security = LocalProxy(lambda: current_app.extensions['security'])
    _datastore = LocalProxy(lambda: _security.datastore)
    if form.validate_on_submit():
        update_password(current_user, request.form['password'])
        _datastore.commit()
        flash("your password was updated", "confirmation")
        return redirect(request.path)
    return render_template('my_account/edit_password.html', form=form)