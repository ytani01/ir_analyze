#!/bin/sh
#
MYNAME=`basename $0`

IRSEND_CMD="lirc-send.py -i 1"

DEV_TV="lg_tv"
CMD_TV_TV="input down ok back back"
CMD_TV_HDMI="input down down ok back back" 

DEV_HDMI="hdmi"

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

case $1 in
    tv) 
	${IRSEND_CMD} ${DEV_TV} ${CMD_TV_TV} ;;
    hdmi) 
	${IRSEND_CMD} ${DEV_TV} ${CMD_TV_HDMI} ;;
esac
