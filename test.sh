#!/bin/sh -e

THIS_SCRIPT=$0
THIS_DIR=$(dirname ${THIS_SCRIPT})


nuke_pyc_files() {
  make clean
}

run_pep8_style_checks() {
    # F401: imported but unused
    # F403 'from foo import *'
    # F405: ...  may be undefined, or defined from star imports ...

    flake8 \
        --ignore=F401,F403,F405 \
        --exclude='expirybot/*/*/migrations/*.py' \
    .

    # Now re-check for F403 & F405 everywhere *except* settings

    flake8 \
        --select=F403,405 \
        --exclude='expirybot/settings/*.py' \
    .
}

run_more_pep8_checks() {
    # Run some PEP8 checks *after* unit testing.
    # This is nicer to work with in development as you can clean up once it's
    # working

    # F401: don't allow `imported but unused` except in __init__.py, settings
    flake8 \
        --select=F401 \
        --exclude='*/__init__.py,expirybot/settings/*.py' \
    .
}

run_python_unit_tests() {
    python manage.py test --failfast -v 3
}

test_that_no_models_need_migrations() {
    OUTPUT=$(python manage.py makemigrations --dry-run)
    if [ "${OUTPUT}" != "No changes detected" ] ; then
        echo
        echo 'ERROR: Some models need migrations!'
        echo
        python manage.py makemigrations --dry-run
        exit 2
    fi
}

nuke_pyc_files
# run_pep8_style_checks
run_python_unit_tests
# run_more_pep8_checks
test_that_no_models_need_migrations
