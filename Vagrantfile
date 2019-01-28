Vagrant.configure("2") do |config|
  config.vm.box ="ubuntu/xenial64"  # same as linode server

  config.vm.box_check_update = true
  config.vm.define "malman-dev"
  config.vm.hostname = "malman-dev"
  config.vm.provider "virtualbox"

  # don't auto update virtualbox guest additions
  config.vbguest.no_install = true

  # enable host io cache
  config.vm.provider "virtualbox" do |v|
      v.customize [
          "storagectl", :id,
          # "--name", "SATA Controller",
          # "--name", "IDE Controller",
          "--name", "SCSI",
          "--hostiocache", "on"
      ]
  end

  # config.disksize.size = '30GB'
  config.vm.provider "virtualbox" do |vb|
    vb.memory = "1024"
    vb.cpus = 2
    vb.name = "vagrant_malman-dev"
    vb.customize [ "modifyvm", :id, "--uartmode1", "disconnected" ]
  end

  config.vm.network "private_network", ip: "172.16.12.2"

  config.vm.synced_folder ".", "/vagrant", disabled: true

  ## mount using vboxsf (slow)
  APACHE_UID = 33
  APACHE_GID = 33
  config.vm.synced_folder ".", "/var/www/MALMan", type: 'virtualbox', create: true, owner: APACHE_UID, group: APACHE_GID

  ## mount using NFS (faster)
  # config.nfs.map_uid = Process.uid   # give www-data user write access
  # config.nfs.map_gid = Process.gid   # give www-data user write access
  # add directory to /etc/exports if necessary and restart nfs
  # config.vm.synced_folder "/nfs/MALMan/", "/var/www/MALMan", type: 'nfs', create: true, nfs_export: false

  # Prevent TTY Errors
  config.ssh.shell = "bash -c 'BASH_ENV=/etc/profile exec bash'"

  config.vm.provision "ansible" do |ansible|
    ansible.playbook = "envs/dev/playbook.yml"
  end

  config.vm.post_up_message = "
    add '172.16.12.2 malman-dev' to /etc/hosts if necessary.

    - MALMan: http://malman-dev/  (running in production mode as a WSGI app under apache, u:admin@example.com p:secret))
    - PHPMyAdmin: http://malman-dev/phpmyadmin (u:MALMan p:CLUBMATE2010)
    - Maildev: http://malman-dev:1080/

    to run in debug mode:
    $ vagrant ssh
    $ cd /var/www/MALMan
    $ export WERKZEUG_DEBUG_PIN=off; virtualenv/bin/python commands.py rundebug
    => http://malman-dev:5000/"
end
