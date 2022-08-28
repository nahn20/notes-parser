#! /bin/bash
SCRIPTPATH=$(dirname "$0")

cd $SCRIPTPATH &&
git pull &&
pip3 install -r requirements.txt
