#!/usr/bin/python2
"""run the MALMan app"""
from MALMan import app

#from flask_debugtoolbar import DebugToolbarExtension
#toolbar = DebugToolbarExtension(app)

# make server visible to external IPs
app.run(host='0.0.0.0')
