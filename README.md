MALMan is a WSGI app

Installation [![Build Status](https://travis-ci.org/voidwarranties/MALMan.svg?branch=master)](https://travis-ci.org/voidwarranties/MALMan)
============

Getting the code
----------------
Create a directory to contain the program and get the source code:

    mkdir -p /usr/local/share/webapps
    git clone git://github.com/voidwarranties/MALMan.git /usr/local/share/webapps/MALMan

From here on on I will asume you are located in the directory you installed MALMan in,
so move into this directory.

    cd /usr/local/share/webapps/MALMan

Setting up the virtualenv and getting dependencies
--------------------------------------------------
You will need to have version 2 of python, pip and virtualenv installed on your system.
On debian-based systems these are provided by the packages python, python-pip and python-virtualenv.
If installing on Arch linux you will need the packages python2, python2-pip and python2-virtualenv
and will have to substitute 'virtualenv-2' for 'virtualenv' in the following command.

Set up a isolated Python environment in the directory 'env'.

    virtualenv env

Fetch the latest version of distribute, which is needed to fetch some of the dependencies:

    env/bin/pip install distribute --upgrade


Install the required python packages into the enviroment.

    env/bin/pip install -r requirements.txt

Setting up the database
-----------------------
You need to have a database server running on your system, such as MariaDB or MySQL.
The following can also be done through a gui such as phpMyAdmin.

Start a MySQL shell and create a database called 'MALMan'.
Then create a user which we will also call MALMan and give him access to the database we just made.
Substitute a secure password for 'password'.
Close the shell and import the contents of database.sql into the MALMan database.

    mysql -p -u root
    > CREATE DATABASE MALMan;
    > CREATE USER MALMan@localhost IDENTIFIED BY 'password';
    > GRANT ALL PRIVILEGES ON MALMan.* TO MALMan@localhost;
    > EXIT
    mysql -u MALMan -p -h localhost MALMan < database.sql

Configuration
-------------
Copy MALMan.cfg.template to MALMan.cfg and fill in the apropriate MySQL, SMTP and security parameters.

    cp MALMan/MALMan.cfg{.template,}

For development purposes you might want to use Python's SMTP debugging server:

    python -m smtpd -n -c DebuggingServer localhost:1025

This will start an SMTP server on port 1025 of localhost.
All mails sent will be displayed in the console output.

Running in debug mode
---------------------
You should now be able to run MALMan in development mode. This isn't suitable for production use.

    env/bin/python commands.py runserver

MALMan should be running locally on 0.0.0.0:5000.

Specify a host to make it accessible to other devices on the network:

    env/bin/python commands.py runserver --host ::

Activating the first account
----------------------------
After registering a user's membership request will have to be accepted by an
active member with member management permissions. With no one to activate the
first user we will have to do this outside of MALMan:

    env/bin/python commands.py activate_member user@example.org
    env/bin/python commands.py give_perm user@example.org members

This will accept the membership request of your first user and grant her
membership managment permissions, so further request can be handled through
MALMan.

Running in production mode
--------------------------
Be sure to disable the DEBUG mode in MALMan/MALMan.cfg when running in production.

MALMan can run as a WSGI app under Apache or as a fastcgi app under various other web servers.
A runner is provided for both (MALMan.wsgi and MALMan.fcgi).

### Serve under apache

Include this in /etc/httpd/conf/httpd.conf:

    LoadModule wsgi_module modules/mod_wsgi.so
    WSGIScriptAlias /MALMan /usr/local/share/webapps/MALMan/MALMan.wsgi
    <Directory /usr/local/share/webapps/MALMan>
        Order deny,allow
        Allow from all
        WSGIScriptReloading On
    </Directory>

This tells apache to load the wsgi module at /usr/local/share/webapps/MALMan/MALMan.wsgi
and serve it under /MALMan.

### Serve with Lighttpd

1. enable fastcgi:

    lighttpd-enable-mod fastcgi

2. make a new file /etc/lighttpd/conf-available/15-fastcgi-MALMan.conf with this content:

    fastcgi.server += (
        "/MALMan" =>
        ((
            "socket" => "/tmp/MALMan-fcgi.sock",
               "bin-path" => "/usr/local/share/webapps/MALMan/MALMan.fcgi",
            "check-local" => "disable",
            "max-procs" => 1
        ))
    )

3. enable the new config:

    lighttpd-enable-mod fastcgi-MALMan

4. change owner of the files to www-data:

    chown www-data:www-data /usr/local/share/webapps/MALMan -R

4. restart lighttpd:

    service lighttpd restart

5. you can find your website at http://localhost/MALMan.fcgi
(or using the ip / a linked domain if hosted remotely)
