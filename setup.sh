#!/bin/sh

BINDIR=${HOME}/bin
REQUIRMENTS=requirements.txt
CMD=lirc_analyze.py

if [ -f ${REQUIRMENTS} ]; then
    pip3 install -r requirements.txt
fi

if [ ! -d ${BINDIR} ]; then
    mkdir -p ${BINDIR}
fi

cp -fv ${CMD} ${BINDIR}

