#!/bin/sh
#
MYNAME=`basename $0`

REMOTE="tv-light"
IRSEND="irsend SEND_ONCE ${REMOTE}"
#IRSEND="lirc-send.py -i 0.3 ${REMOTE}"

#####
irsend_repeat () {
    echo $*
    i=0
    while [ $i -lt $2 ]; do
        ${IRSEND} $1
	sleep 1
	i=`expr $i + 1`
        echo "$i "
    done
}

usage () {
    echo usage: $MYNAME value
}

#####
if [ X$1 = X ]; then
    usage
    exit 1
fi

VALUE=$1

BTN_UP1="up"
BTN_DOWN1="down"

COUNT=`expr $VALUE - 1`
COUNT10=`expr $COUNT / 10`
COUNT1=`expr $COUNT % 10`

echo "COUNT=${COUNT}"

echo ".. min "
irsend_repeat ${BTN_DOWN1} 4
echo "up .."
irsend_repeat ${BTN_UP1} ${COUNT}
echo
