#!/bin/sh -eux

add_extra_apt_repositories() {
  apt-key add /home/vagrant/app/vagrant/postgres_pgp_ACCC4CF8.asc
  echo 'deb http://apt.postgresql.org/pub/repos/apt/ xenial-pgdg main' > /etc/apt/sources.list.d/postgres.list
}

update_apt() {
  apt-get update
}

install_postgresql() {
  apt-get remove -y postgresql-9.3
  apt-get install -y postgresql-9.6 libpq-dev

  sed -i 's/port = 5433/port = 5432/g' /etc/postgresql/9.6/main/postgresql.conf
  sudo service postgresql restart
}

install_system_dependencies() {
  apt-get install -y \
    firejail \
    gnupg2 \
    python3 \
    python3-dev \
    python-virtualenv \
    libjpeg-dev \
    ruby-dev \
    unzip

  sass -v || gem install sass
  listen -v || gem install listen
}

run_as_vagrant() {
  su vagrant -c "$1"
}

run_in_virtualenv() {
  run_as_vagrant "bash -c '. ~/venv/bin/activate && $1'"
}

install_custom_bashrc() {
  cp /home/vagrant/app/vagrant/bashrc /home/vagrant/.bashrc
}

create_secrets_sh() {
  if [ ! -f '/vagrant/secrets.sh' ]; then
    cp /home/vagrant/app/secrets.sh.example /home/vagrant/app/vagrant/secrets.sh
    ln -s /home/vagrant/app/vagrant/secrets.sh /home/vagrant/app/secrets.sh
  fi
}

setup_app_virtualenv() {
  run_as_vagrant "virtualenv -p /usr/bin/python3 ~/venv"

  run_in_virtualenv 'pip install -r ~/app/requirements.txt'
  run_in_virtualenv 'pip install -r ~/app/requirements_for_testing.txt'
}

create_postgresql_database_and_user() {
    # We make a user and a database both called vagrant, then the vagrant
    # username will automatically access that database.
    CREATE_USER="createuser --superuser vagrant"
    CREATE_DATABASE="createdb --owner vagrant vagrant"

    # Run as postgres user, it has permission to do this
    su -c "${CREATE_USER}" postgres || true
    su -c "${CREATE_DATABASE}" postgres || true
}

migrate_database_and_add_admin() {
  run_in_virtualenv "~/app/manage.py migrate"
  run_in_virtualenv "~/app/manage.py loaddata /home/vagrant/app/vagrant/admin_user_fixture.json"
}

disable_ubuntu_motd() {
  # This is absurd, but to switch off the message-of-the-day *framework*
  # you have to comment out some lines in a pam module!!
  # http://ubuntuforums.org/showthread.php?t=1449020

  sed -e '/pam_motd.so/ s/^#*/#/' -i /etc/pam.d/sshd
}

install_our_instructions_into_etc_profile() {
  cp /home/vagrant/app/vagrant/profile_cat_instructions.sh /etc/profile.d/profile_cat_instructions.sh
}

add_extra_apt_repositories
update_apt
install_postgresql
install_system_dependencies
install_custom_bashrc
create_secrets_sh
setup_app_virtualenv
create_postgresql_database_and_user
migrate_database_and_add_admin
disable_ubuntu_motd
install_our_instructions_into_etc_profile
