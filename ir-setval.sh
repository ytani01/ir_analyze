#!/bin/sh
#
# (c) 2019 Yoichi Tanibayashi
#
MYNAME=`basename $0`

#IRSEND_CMD="irsend SEND_ONCE"
IRSEND_CMD="lirc-send.py -d"

##### funcs
usage () {
    echo "usage: ${MYNAME} device value button_up button_down_to_0 [button_up_10]"
}

irsend_repeat () {
    BTN=$1
    COUNT=$2

    if [ -z ${BTN} -o -z ${COUNT} ]; then
	echo $*
	exit 1
    fi
    
    i=1
    while [ $i -le $2 ]; do
	echo ${IRSEND} ${BTN}
	eval "${IRSEND} ${BTN}"
	sleep 1
	i=`expr $i + 1`
    done
}

##### main
if [ -z $1 ]; then
    usage
    exit 1
fi
DEVICE=$1

shift
if [ -z $1 ]; then
    usage
    exit 1
fi
VALUE=$1

shift
if [ -z $1 ]; then
    usage
    exit 1
fi
BTN_UP_1=$1

shift
if [ -z $1 ]; then
    usage
    exit 1
fi
BTN_DOWN_REPEAT=$1

shift
BTN_UP_10=
if [ ! -z $1 ]; then
    BTN_UP_10=$1    
fi

#echo "${DEVICE} ${VALUE} ${BTN_UP_1} ${BTN_DOWN_REPEAT} ${BTN_UP_10}"
IRSEND="${IRSEND_CMD} ${DEVICE} "
#echo $IRSEND

if [ -z ${BTN_UP_10} ]; then
    COUNT_10=0
    COUNT_1=${VALUE}
else
    COUNT_10=`expr ${VALUE} / 10`
    COUNT_1=`expr ${VALUE} % 10`
fi
#echo ${COUNT_1} ${COUNT_10}

irsend_repeat ${BTN_DOWN_REPEAT} 1
irsend_repeat ${BTN_UP_10}       ${COUNT_10}
irsend_repeat ${BTN_UP_1}        ${COUNT_1}

