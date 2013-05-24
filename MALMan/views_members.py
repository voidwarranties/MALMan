from MALMan import app
import MALMan.database as DB
import MALMan.forms as forms
from MALMan.view_utils import add_confirmation, return_flash, permission_required, membership_required

from flask import render_template, request, redirect
from flask.ext.wtf import BooleanField

from datetime import date

@app.route("/members")
@membership_required()
def members():
    users = DB.User.query.filter_by(active_member='1')
    return render_template('members/members.html', users=users)


@app.route("/members/approve_new_members", methods=['GET', 'POST'])
@permission_required('members')
def members_approve_new_members():
    new_members = DB.User.query.filter_by(active_member='0')
    for user in new_members:
        setattr(forms.NewMembers, 'activate_' + str(user.id),
            BooleanField('activate user'))
    form = forms.NewMembers()
    if form.validate_on_submit():
        confirmation = app.config['CHANGE_MSG']
        for user in new_members:
            new_value = 'activate_' + str(user.id) in request.form
            if new_value != user.active_member:
                setattr(user, 'active_member', True)
                setattr(user, 'member_since', date.today())
                DB.db.session.commit()
                confirmation = add_confirmation(confirmation,
                    user.email + " was made an active member")
        return_flash(confirmation)
        return redirect(request.url)
    return render_template('members/approve_new_members.html', new_members=new_members,
        form=form)


@app.route('/members/edit_<int:userid>', methods=['GET', 'POST'])
@permission_required('members')
def members_edit_member(userid):
    userdata = DB.User.query.get(userid)
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
        atributes = ['name', 'date_of_birth', 'telephone', 'city',
            'postalcode', 'bus', 'number', 'street', 'show_telephone',
            'show_email', 'active_member', 'membership_dues']
        atributes.extend([role for role in roles])
        for atribute in atributes:
            if atribute in roles:
                old_value = atribute in userdata.roles
                new_value = 'perm_' + atribute.name in request.form
            elif atribute in ['show_telephone', 'show_email', 'active_member']:
                old_value = getattr(userdata, atribute)
                new_value = atribute in request.form
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
                    user = DB.User.query.get(userid)
                    setattr(user, atribute, new_value)
                confirmation = add_confirmation(confirmation, str(atribute) +
                    " = " + str(new_value) + " (was " + str(old_value) + ")")
                DB.db.session.commit()
        return_flash(confirmation)
        return redirect(request.url)
    return render_template('members/edit_account.html', form=form)
