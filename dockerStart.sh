#!/bin/sh

CONF=/conf
CONF_SRC=/usr/src/app/conf

GIT_REPO_URL=https://github.com/mfugate1/appdaemon.git
GIT_BRANCH=master

# if configuration file doesn't exist, clone the repo into conf
if [ ! -f $CONF/appdaemon.yaml ]; then
  cd /conf
  git init
  git remote add origin ${GIT_REPO_URL}
  git fetch
  git checkout -t origin/${GIT_BRANCH}
  cd -
fi

#check recursively under CONF for additional python dependencies defined in requirements.txt
find $CONF -name requirements.txt -exec pip3 install --upgrade -r {} \;

# Lets run it!
exec appdaemon -c $CONF "$@"