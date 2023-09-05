#!/usr/bin/env bash
set -e

DEPLOY_DIR=/catalina
OPS_DEPLOY_DIR=/home/jstone/catalina-ops/catalina
VALIDATE_DEPLOY_DIR=opt/validate/bin
RUN_DATE=`date +'%Y%m%d'`

BASE_DIR=/data/CSS
DEST_DIR=/data/ready
LOGDIR=$BASE_DIR/logs

export PATH=$PATH:$VALIDATE_DEPLOY_DIR

if [ ! -e $BASEDIR/.lockfile ]; then
    $DEPLOY_DIR/ingest/process_uploads.py --basedir $BASE_DIR --destdir $DEST_DIR --permissive-validation --schemadir $DEPLOY_DIR/schemas --max-nights 2

    LOGFILE=$(find $LOGDIR -name "*.log" -type f -cmin -60 | sort -r | head -n1);
    if [ -n "$LOGFILE" ]; then
        echo "Logfile found: $LOGFILE"
        NO_PROCESS=$(grep "0 products discovered" "$LOGFILE" | wc -c)     
        echo "Compressing logfile: $LOGFILE..."
        gzip "$LOGFILE"
        if [ "$NO_PROCESS" -eq 0 ]; then
            echo "Sending processing notification..."
            #grep 'WARNING' $LOGFILE | head -n 2000 | mail -a "$LOGFILE".gz -r $NOTIFICATION_SENDER -s "Catalina processing complete ${RUN_DATE}" $NOTIFICATION_SENDER $EXTRA_RECIPIENTS
        fi
    fi
else
    echo "Lockfile detected. Skipping for now"
fi
