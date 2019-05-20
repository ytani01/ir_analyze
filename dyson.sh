#!/bin/sh
#
MYNAME=`basename $0`

REMOTE="dyson"
IRSEND="irsend SEND_ONCE ${REMOTE}"

ITEM=$1
VALUE=$2

BTN_UP1="${ITEM}_up0"
BTN_UP10="${ITEM}_up0x10"
BTN_DOWN_REPEAT="${ITEM}_down3-repeat"
BTN_DOWN1="${ITEM}_down2"

###
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

###
if [ X$1 = X ]; then
	exit 1
fi

COUNT=`expr $VALUE - 1`
COUNT10=`expr $COUNT / 10`
COUNT1=`expr $COUNT % 10`

echo ".. min "
if [ $ITEM = "fan" ]; then
    ${IRSEND} cool0
    sleep 1
fi
${IRSEND} ${BTN_DOWN1}
${IRSEND} ${BTN_DOWN_REPEAT}
irsend_repeat ${BTN_UP10} ${COUNT10}
irsend_repeat ${BTN_UP1} ${COUNT1}
echo
