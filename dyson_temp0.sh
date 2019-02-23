#!/bin/sh
#
MYNAME=`basename $0`

REMOTE="dyson"
IRSEND="irsend SEND_ONCE ${REMOTE}"
BTN_UP10="temp_up0x10"
BTN_UP1="temp_up0"
BTN_DOWN0="temp_down0_repeat"

TEMP=$1

###
irsend_repeat () {
    echo $*
    i=1
    while [ $i -le $2 ]; do
        echo "$i "
        ${IRSEND} $1
#	sleep 1
	i=`expr $i + 1`
    done
}

###
if [ X$1 = X ]; then
	exit 1
fi

COUNT10=`expr $TEMP / 10`
COUNT1=`expr $TEMP % 10`

echo ".. 0 "
${IRSEND} ${BTN_DOWN0}
irsend_repeat ${BTN_UP10} ${COUNT10}
irsend_repeat ${BTN_UP1} ${COUNT1}
echo
