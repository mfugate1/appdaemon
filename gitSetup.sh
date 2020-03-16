#!/bin/sh

GIT_REPO_URL=https://github.com/mfugate1/appdaemon.git
GIT_BRANCH=master

cd /conf
git init
git remote add origin ${GIT_REPO_URL}
git fetch
git checkout -t origin/${GIT_BRANCH}
cd -

./dockerStart.sh "$@"
