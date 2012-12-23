#!/usr/bin/python2
from MALMan import app
# make server visible to external IPs
app.run(host='0.0.0.0')
