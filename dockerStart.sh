#!/bin/sh

CONF=/conf
CONF_SRC=/usr/src/app/conf

# if configuration file doesn't exist, clone the repo into conf
if [ ! -f $CONF/appdaemon.yaml ]; then
  git clone https://github.com/mfugate1/appdaemon.git /conf
fi

#check recursively under CONF for additional python dependencies defined in requirements.txt
find $CONF -name requirements.txt -exec pip3 install --upgrade -r {} \;

# Lets run it!
exec appdaemon -c $CONF "$@"