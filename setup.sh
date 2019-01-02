#!/bin/sh

BINDIR=${HOME}/bin
REQUIRMENTS=requirements.txt
CMD="lirc-analyze.py lirc-send.py"

if [ -f ${REQUIRMENTS} ]; then
    sudo pip3 install -r requirements.txt
fi

if [ ! -d ${BINDIR} ]; then
    mkdir -p ${BINDIR}
fi

cp -fv ${CMD} ${BINDIR}

