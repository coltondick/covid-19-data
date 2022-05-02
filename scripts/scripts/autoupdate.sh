#!/bin/bash

set -e

BRANCH="master"
ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd ../.. && pwd )"
SCRIPTS_DIR=$ROOT_DIR/scripts

# ENV VARS
export OWID_COVID_PROJECT_DIR=${ROOT_DIR}
export OWID_COVID_CONFIG=${OWID_COVID_PROJECT_DIR}/scripts/config.yaml
export OWID_COVID_SECRETS=${OWID_COVID_PROJECT_DIR}/scripts/secrets.yaml
export PATH=$PATH:/usr/local/bin/  # so geckodriver is correctly found

has_changed() {
  git diff --name-only --exit-code $1 >/dev/null 2>&1
  [ $? -ne 0 ]
}

has_changed_gzip() {
  # Ignore the header because it includes the creation time
  cmp --silent -i 8 $1 <(git show HEAD:$1)
  [ $? -ne 0 ]
}

git_push() {
  if [ -n "$(git status --porcelain)" ]; then
    msg="data("$1"): automated update"
    git add .
    git commit -m "$msg"
    git push
  fi
}


cd $ROOT_DIR

# Activate Python virtualenv
source $SCRIPTS_DIR/venv/bin/activate

# Interpret inline Python script in `scripts` directory
run_python() {
  (cd $SCRIPTS_DIR/scripts; python -c "$1")
}

# Make sure we have the latest commit.
git reset --hard origin/master
git pull

# =====================================================================
# JHU

# Attempt to download JHU CSVs
cowid jhu get

hour=$(date +%H)
if has_changed './scripts/input/jhu/*'; then
  echo "Generating JHU files..."
  cowid --server jhu generate
  # python $SCRIPTS_DIR/scripts/jhu.py --skip-download
  git_push "jhu"
else
  echo "JHU export is up to date"
fi

# =====================================================================
# Decoupling charts
hour=$(date +%H)
if [ $hour == 01 ] ; then
  echo "Generating decoupling dataset..."
  cowid --server decoupling generate
  git_push "decoupling"
fi

# =====================================================================
# VAX ICER
hour=$(date +%H)
if [ $hour == 03 ] ; then
  echo "Generating ICE vaccination data..."
  cowid --server vax icer
fi

# =====================================================================
# Hospital & ICU data

hour=$(date +%H)
if [ $hour == 05 ] || [ $hour == 17 ] ; then
  # Download CSV
  echo "Generating hospital & ICU export..."
  cowid --server hosp generate
  cowid --server hosp grapher-io
  git_push "hosp"
fi

# =====================================================================
# Vaccinations

hour=$(date +%H)
if [ $hour == 07 ] ; then
  echo "Generating Vaccination (get, process, generate)..."
  cowid --server vax get
  cowid --server vax process generate
  git_push "vax"
fi


# =====================================================================
# Google Mobility

hour=$(date +%H)
if [ $hour == 09 ] ; then
  # Generate dataset
  cowid --server gmobility generate

  echo "Generating Google Mobility export..."
  cowid --server gmobility grapher-io

  if has_changed './scripts/grapher/Google Mobility Trends (2020).csv'; then
    git_push "mobility"
  fi
fi

# =====================================================================
# Swedish Public Health Agency

hour=$(date +%H)
if [ $hour == 11 ] ; then
  # Attempt to download data
  cowid --server sweden get
  if has_changed './scripts/input/sweden/sweden_deaths_per_day.csv'; then
    echo "Generating Swedish Public Health Agency dataset..."
    cowid --server sweden generate
    git_push "sweden"
  else
    echo "Swedish Public Health Agency export is up to date"
  fi
fi

# =====================================================================
# UK subnational data
hour=$(date +%H)
if [ $hour == 13 ] ; then
  # Download CSV
  echo "Generating UK subnational export..."
  cowid --server uk-nations generate
  git_push "uk"
fi

# =====================================================================
# US vaccinations
hour=$(date +%H)
if [ $hour == 15 ] ; then
  echo "Generating US vaccination files..."
  cowid --server vax us-states
  if has_changed './public/data/vaccinations/us_state_vaccinations.csv'; then
    git_push "vax,us"
  else
    echo "US vaccination export is up to date"
  fi
fi

# =====================================================================
# Variants
hour=$(date +%H)
if [ $hour == 19 ] ; then
  echo "Generating CoVariants dataset..."
  cowid --server variants generate
  cowid --server variants grapher-io
  git_push "variants"
fi

# =====================================================================
# Excess Mortality
hour=$(date +%H)
if [ $hour == 21 ] ; then
  echo "Generating CoVariants dataset..."
  cowid --server xm generate
  git_push "xm"
fi

# =====================================================================
# Policy responses
OXCGRT_CSV_PATH=./scripts/input/bsg/latest.csv
hour=$(date +%H)
if [ $hour == 23 ] ; then
  # Download CSV
  cowid --server oxcgrt get
  # If there are any unstaged changes in the repo, then the
  # CSV has changed, and we need to run the update script.
  if has_changed $OXCGRT_CSV_PATH; then
    echo "Generating OxCGRT export..."
    cowid --server oxcgrt grapher-io
    git_push "oxcgrt"
  else
    echo "OxCGRT export is up to date"
  fi
else
  echo "OxCGRT CSV was recently updated; skipping download"
fi


# =====================================================================
# Megafile
cowid --server megafile
git_push "megafile"