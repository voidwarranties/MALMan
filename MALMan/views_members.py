
from MALMan import app
import MALMan.database as DB
import MALMan.forms as forms
from MALMan.view_utils import add_confirmation, return_flash, permission_required, membership_required, string_to_date

from flask import render_template, request, redirect, flash, abort, url_for
from flask.ext.wtf import BooleanField

import datetime


@app.route("/members")
@membership_required()
def members():
    users = DB.User.query.filter_by(active_member=True)
    return render_template('members/members.html', users=users)


@app.route("/members/approve_new_members", methods=['GET', 'POST'])
@permission_required('members')
def members_approve_new_members():
    new_members = DB.User.query.filter_by(membership_start=None)
    for user in new_members:
        setattr(forms.NewMembers, 'activate_' + str(user.id), BooleanField('activate user'))
    form = forms.NewMembers()
    if form.validate_on_submit():
        confirmation = app.config['CHANGE_MSG']
        for user in new_members:
            new_value = 'activate_' + str(user.id) in request.form
            if new_value != user.active_member:
                user.membership_start = datetime.date.today()
                DB.db.session.commit()
                confirmation = add_confirmation(confirmation, user.email +
                                                " was made an active member")
        return_flash(confirmation)
        return redirect(request.url)
    return render_template('members/approve_new_members.html', new_members=new_members, form=form)


@app.route("/members/former_members")
@permission_required('members')
def members_former_members():
    former_members = DB.User.query.filter(DB.User.membership_start <= DB.User.membership_end)
    return render_template('members/former_members.html', users=former_members)


@app.route("/members/remove_<int:user_id>", methods=['GET', 'POST'])
@permission_required('members')
def members_remove_member(user_id):
    user = DB.User.query.get(user_id)
    if not user:
        flash("There is no user with this user id.", "error")
        abort(404)
    if user.membership_end or not user.membership_start:
        flash("This user is not a member.", "error")
        abort(404)
    form = forms.MembersRemoveMember()
    if form.validate_on_submit():
        confirmation = app.config['CHANGE_MSG']
        user.membership_end = datetime.date.today()
        DB.db.session.commit()
        confirmation = add_confirmation(confirmation, user.email + " is no longer a member.")
        return redirect(url_for('members'))
    return render_template('members/remove_member.html', user=user, form=form)


@app.route('/members/edit_<int:user_id>', methods=['GET', 'POST'])
@permission_required('members')
def members_edit_member(user_id):
    userdata = DB.User.query.get(user_id)
    roles = DB.Role.query.all()
    # add roles to form
    for role in roles:
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
        confirmation = app.config['CHANGE_MSG']
        atributes = ['name', 'date_of_birth', 'telephone', 'city', 'postalcode',
                     'bus', 'number', 'street', 'show_telephone', 'show_email',
                     'membership_dues']
        atributes.extend([role for role in roles])
        for atribute in atributes:
            if atribute in roles:
                old_value = atribute in userdata.roles
                new_value = 'perm_' + atribute.name in request.form
            elif atribute in ['show_telephone', 'show_email']:
                old_value = getattr(userdata, atribute)
                new_value = atribute in request.form
            elif atribute in ['date_of_birth']:
                old_value = getattr(userdata, atribute)
                new_value = string_to_date(request.form.get(atribute))
            else:
                old_value = getattr(userdata, atribute)
                new_value = request.form.get(atribute)
            if str(new_value) != str(old_value):
                if atribute in roles:
                    if new_value:
                        DB.user_datastore.add_role_to_user(userdata, atribute)
                    else:
                        DB.user_datastore.remove_role_from_user(userdata, atribute)
                else:
                    user = DB.User.query.get(user_id)
                    setattr(user, atribute, new_value)
                confirmation = add_confirmation(confirmation, str(atribute) + " = " +
                                                str(new_value) + " (was " + str(old_value) + ")")
                DB.db.session.commit()
        return_flash(confirmation)
        return redirect(request.url)
    return render_template('members/edit_account.html', form=form)
