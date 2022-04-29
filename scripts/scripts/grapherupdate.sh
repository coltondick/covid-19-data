#!/bin/bash

set -e

BRANCH="master"
ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd ../.. && pwd )"
SCRIPTS_DIR=$ROOT_DIR/scripts

cd $ROOT_DIR

# Activate Python virtualenv
source $SCRIPTS_DIR/venv/bin/activate

# Interpret inline Python script in `scripts` directory
run_python() {
  (cd $SCRIPTS_DIR/scripts; python -c "$1")
}

# Make sure we have the latest commit.
git checkout $BRANCH
git pull

# ENV VARS
export OWID_COVID_PROJECT_DIR=${ROOT_DIR}
export OWID_COVID_CONFIG=${OWID_COVID_PROJECT_DIR}/scripts/config.yaml
export OWID_COVID_SECRETS=${OWID_COVID_PROJECT_DIR}/scripts/secrets.yaml

# Run Grapher updates
cowidev-grapher-db

## Additional individual grapher updates
minute=$(date +%M)
if [ $minute == 20 ] ; then
  cowid --server jhu grapher-db
  cowid --server decoupling grapher-db
  cowid --server hosp grapher-db
  cowid --server gmobility grapher-db
  cowid --server sweden grapher-db
  cowid --server uk-nations grapher-db
  cowid --server oxcgrt grapher-db
fi