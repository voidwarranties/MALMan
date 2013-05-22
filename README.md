MALMan is a WSGI app

Installation
============

Getting the code
----------------
Create a directory to contain the program and get the source code:

    mkdir -p /usr/local/share/webapps/MALMan
    git clone git://github.com/voidwarranties/MALMan.git /usr/local/share/webapps/MALMan

From here on on I will asume you are located in the directory you installed MALMan in, so move into this directory.

    cd /usr/local/share/webapps/MALMan

Setting up the virtualenv and getting dependencies
--------------------------------------------------
You will need to have version 2 of python, pip and virtualenv installed on your system. On debian-based systems these are provided by the packages python, python-pip and python-virtualenv. If installing on Arch linux you will need the packages python2, python2-pip and python2-virtualenv and will have to substitute 'virtualenv-2' for 'virtualenv' in the following command.

This will set up a isolated Python environment in the directory 'env' and install the python packages MALMan depends upon in this enviroment.

    virtualenv env
    env/bin/pip install -r requirements.txt

Setting up the database
-----------------------
You need to have a database server running on your system, such as MariaDB or MySQL. The following can also be done through a gui such as phpMyAdmin.

Start a MySQL shell and create a database called 'MALMan'. Then create a user which we will also call MALMan and give him access to the database we just made. Substitute a secure password for 'password'. Close the shell and import the contents of database.sql into the MALMan database.

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

Running in debug mode
---------------------
You should now be able to run MALMan in development mode. This isn't suitable for production use.

    env/bin/python run.py

MALMan should be running locally on 0.0.0.0:5000. There is a default account provided with username 'root@example.org' and password 'password'

Running in production mode
--------------------------
Be sure to disable the DEBUG mode in MALMan/MALMan.cfg when running in production.

MALMan can run as a WSGI app under Apache or as a fastcgi app under various other web servers. A runner is provided for both (MALMan.wsgi and MALMan.fcgi).

To serve MALMan under apache, include this in /etc/httpd/conf/httpd.conf:

    LoadModule wsgi_module modules/mod_wsgi.so
    WSGIScriptAlias /MALMan /usr/local/share/webapps/MALMan/MALMan.wsgi
    <Directory /usr/local/share/webapps/MALMan>
        Order deny,allow
        Allow from all
        WSGIScriptReloading On
    </Directory>

This tells apache to load the wsgi module at /usr/local/share/webapps/MALMan/MALMan.wsgi and serve it under /MALMan.

To serve with Lighttpd:

1. enable fastcgi: # lighttpd-enable-mod fastcgi
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
    
OR FOR DEBIAN:

    fastcgi.server += (
        "/MALMan" =>
    	((
    	    "socket" => "/tmp/MALMan-fcgi.sock",
       		"bin-path" => "/usr/local/share/webapps/MALMan/MALMan.debian6.fcgi",
        	"check-local" => "disable",
        	"max-procs" => 1

    	))
	)

    
3. enable the new config: lighttpd-enable-mod fastcgi-MALMan
4. change owner of the files to www-data: chown www-data:www-data /usr/local/share/webapps/MALMan -R
4. restart lighttpd: service lighttpd restart
5. you can find your website at http://localhost/MALMan.fcgi (or using the ip / a linked domain if hosted remotely)

Beware that you can only run one fastcgi.server instance, so if you are already running a fastcgi app you have to append MALMan to the fastcgi.server instance:

    fastcgi.server = (
        [...]
        ".php" =>
        (( "host" => "127.0.0.1",
            "port" => 1026,
            "bin-path" => "/usr/local/bin/php"
        )),
        "/MALMan" =>
        ((
            "socket" => "/tmp/MALMan-fcgi.sock",
               "bin-path" => "/usr/local/share/webapps/MALMan/MALMan.fcgi",
            "check-local" => "disable",
            "max-procs" => 1
        )),
        ".php4" =>
        (( "host" => "127.0.0.1",
            "port" => 1026
         ))
         [...]
     )
