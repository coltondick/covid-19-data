#!/bin/bash
set -e
cd /home/owid/covid-19-data/scripts
source venv/bin/activate

hour=$(TZ=Europe/Paris date +%H)

ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd ../.. && pwd )"
SCRIPTS_DIR=$ROOT_DIR/scripts

# ENV VARS
export OWID_COVID_PROJECT_DIR=${ROOT_DIR}
export OWID_COVID_CONFIG=${OWID_COVID_PROJECT_DIR}/scripts/config.yaml
export OWID_COVID_SECRETS=${OWID_COVID_PROJECT_DIR}/scripts/secrets.yaml


if [ $hour == 7 ] ; then
  cowid check jhu
fi

if [ $hour == 12 ] ; then
  cowid check vax
fi

if [ $hour == 14 ] ; then
  cowid check test
fi
