from MALMan import app
from flask import render_template, request

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

@app.errorhandler(413)
def error_413(error):
    error = "413 Request entity too large"
    lastpage = request.referrer
    return render_template('error.html', error=error, lastpage=lastpage), 413
