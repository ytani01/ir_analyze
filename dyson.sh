#!/bin/sh
#
MYNAME=`basename $0`

REMOTE="dyson"
IRSEND="irsend SEND_ONCE ${REMOTE}"
#IRSEND="lirc-send.py -i 0.3 ${REMOTE}"

#####
irsend_repeat () {
    echo $*
    i=1
    while [ $i -le $2 ]; do
        echo "$i "
        ${IRSEND} $1
	sleep 1
	i=`expr $i + 1`
    done
}

usage () {
    echo usage: $MYNAME item value
}

#####
if [ X$2 = X ]; then
    usage
    exit 1
fi

ITEM=$1
VALUE=$2

BTN_UP1="${ITEM}_up0"
BTN_UP10="${ITEM}_up0x10"
BTN_DOWN_REPEAT="${ITEM}_down3-repeat"
BTN_DOWN1="${ITEM}_down2"

COUNT=`expr $VALUE - 1`
COUNT10=`expr $COUNT / 10`
COUNT1=`expr $COUNT % 10`

echo ".. min "
if [ $ITEM = "fan" ]; then
    ${IRSEND} cool0
    sleep 1
    ${IRSEND} cool0
    sleep 1
fi
${IRSEND} ${BTN_DOWN1}
sleep 1
${IRSEND} ${BTN_DOWN_REPEAT}
sleep 1
${IRSEND} ${BTN_DOWN_REPEAT}
sleep 2
irsend_repeat ${BTN_UP10} ${COUNT10}
sleep 1
irsend_repeat ${BTN_UP1} ${COUNT1}
echo
