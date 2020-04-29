#!/bin/bash

#
## Suggested crontab
## min hour  dom mon dow            command
#   55    *    *   *   *            /Users/sky/Dropbox/aa6ax/Packet_radio/Python/jnos/scripts/mailChartMaker.bash
## Doing this at hour+55 ensures we get nearly the last full hour's data each time
#

echo =====================================================================
echo Begin processing.

#
echo cd /Users/sky/Dropbox/aa6ax/Packet_radio/Python/jnos/
cd /Users/sky/Dropbox/aa6ax/Packet_radio/Python/jnos/

# Read log from skyPi4
echo 
echo =====================================================================
echo Transfer current log from skyPi4
scp -p -i /Users/sky/.ssh/id_rsa pi@skypi4.local:/jnos/logs/vhf.log logs/vhf.log

# Digest the log file to make chart inserts
echo
echo =====================================================================
echo Process the log to create javascript data
python scripts/mailChart.py logs/vhf.log logs/mailChart-charts.txt logs/mailChart.log AA6AX 20000000 1200

# Write processed chart inserts to aa6ax.us
echo 
echo =====================================================================
echo Transfer processed javascript to aa6ax.us web site
scp -p -i /Users/sky/.ssh/id_rsa logs/mailChart-charts.txt root@red7.com:/var/www/skysites_chroot/aa6ax/_data/mailChart-charts.txt 

# Write log to aa6ax.us
echo 
echo =====================================================================
echo Backup the entire log onto aa6ax.us
scp -p -i /Users/sky/.ssh/id_rsa logs/vhf.log root@red7.com:/var/www/skysites_chroot/aa6ax/_data/vhf.log 

echo
echo All done.
echo =====================================================================
