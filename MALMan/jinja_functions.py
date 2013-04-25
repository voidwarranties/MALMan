from MALMan import app
import MALMan.database as DB

def getmail(user_id):
    user = DB.User.query.get(user_id)
    return user

def hasrole(user_id, role):
	user = DB.User.query.get(user_id)
	if role in user.roles:
		return True
	return False

# define extra jinja functions
app.jinja_env.globals.update(getmail=getmail)
app.jinja_env.globals.update(hasrole=hasrole)