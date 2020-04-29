# JNOS-python
Python scripts to augment JNOS packet radio

These are mostly python scripts to augment JNOS, which is a packet radio BBS package.

They provide support for connecting JNOS to Internet email (using IMAP and SMTP), and for importing messages from remote packet BBS's into JNOS on the radio.

Although the scripts work fine in my operating environment, they're provided only on an as-is basis with no guarantee they'll work anywhere else.

"Sky" - aa6ax

https://aa6ax.us/
https://aa6ax.us/p

####################################################################################
####################################################################################
####################################################################################
####################################################################################
####################################################################################

SECTION 1: charting packet traffic

####################################################################################
145.09.php

This is a PHP script/page that runs on a web server. It reads a .txt file containing javascript setup for Google Charts, and it builds a bar chart on the page that starts about 5 days before current date and displays hourly bars showing the composition of packet traffic on an hour-by-hour basis. There's a 'filter' that allows the viewer to specify a different date range.

The page refreshes every 10 minutes, though the data, of course, changes only once an hour by adding the most recent hour at the right hand end of the chart.

The data is created by the mailChartMaker.bash script, which needs to be run by cron at least once an hour.

Although the file name is 145.09 which represents the frequency we monitor here in San Francisco, of course it can show results from any log file for any station in any location.


####################################################################################
mailChart.py

"""
    Read JNOS AX25 log file and chart the stations that were heard
 
   Debugging:
        Set the variable DEBUG to any non-zero value
        Debug messages will appear in the log file 'mailChart.log'
    
    Hints:
    °   If this is run by cron, it must run as 'root' to manipulate files
    °   Suggested to run hourly near the end of the hour
    55 * * * * sudo python3 /PATH_TO/mailChart.py logFile.log chartOutput.txt logOutput.log CALLSIGN lineLimit bucketLimit
"""

JNOS AX25 log file entries are like this:

Wed Apr 29 14:46:26 2020 - vhf sent:
KISS: Port 0 Data
AX25: AA6AX-1->ID UI pid=Text
0000  00 92 88 40 40 40 40 e0 82 82 6c 82 b0 40 63 03  ...@@@@`..l.0@c.
0010  f0 41 41 36 41 58 20 5b 4a 4e 4f 53 32 5d 20 53  pAA6AX [JNOS2] S
0020  61 6e 20 46 72 61 6e 63 69 73 63 6f 20 28 61 61  an Francisco (aa
0030  36 61 78 2e 63 6f 6d 2f 70 29                    6ax.com/p)

Where the first line of each packet is the date + port, then indication of KISS mode, then AX25 station identification, then lines showing byte number + byte content (16 bytes) + alpha representation of that data. A packet's log entry ends with a blank line.

The Python code reads the entire log file and builds hourly "buckets" that tell what stations transmitted and how many bytes. This is then converted into javascript entries for Google Charts. The first line is the column header information, and subsequent lines are the hourly bucket info.

For example:

Column header info:

["Date" , "AA6AX-1", "AA6AX-15", "KE6JJJ-1", "KE6JJJ-2", "KE6JJJ-4", "KF6COZ", "KG6H-1", "KG6H-2", "KI6OID", "KI6OID-1", "KI6RYE", "KI6RYE-1", "KJ6LDJ", "KK6SF", "KK6SF-1", "KK6VQK-1", "KM6WOX-1", "N0ARY-1", "N6ZX-4", "W6KWF", "W6KWF-15", "W6REM", "W6REM-1", "W6YAR", "W6YAR-1", "WA3AW", "WB6RC", "YARS01" , { role: 'tooltip' }, { role: 'style' } ],

and one hourly bucket:

[ new Date(2020,3,07,11),0, 0, 74, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, '74', 'color:grey'],

The output file (the result) has to be transferred to a web server where the page (145.09.php) does a PHP "include" to pull in this data and construct the data table for the chart.


####################################################################################
mailChartMaker.bash

This is a bash shell script that sucks down a JNOS AX25 log file from a remote system, analyzes it and creates javascript entries for a Google Charts data structure, then exports that file to a web server where the (145.09.php) script can read it and build beautiful vibrant charts showing the activity reported by the log.

°	cd to the proper directory
°	use scp to fetch the log file from the Raspberry Pi, which is on the same local network
°	run mailChart.py to do the analysis
°	scp the analysis file to another web server
°	where the page 145.09.php picks up the data, builds the table, and does the interaction with the user.
°	a backup copy of the AX25 log is also uploaded for good measure

Suggested this cron be used:

## min hour  dom mon dow            command
   55    *    *   *   *            /Users/sky/Dropbox/aa6ax/Packet_radio/Python/jnos/scripts/mailChartMaker.bash
## Doing this at hour+55 ensures we get nearly the last full hour's data each time


####################################################################################
####################################################################################
####################################################################################
####################################################################################

SECTION 2: Handling remote BBS checking and message retrieval

####################################################################################
mailInBBS.py

Works a lot like "outpost PMM" in that it can reach out and fetch incoming BBS messages from a remote BBS and then inject them into the local JNOS system for later retrieval.

"""
    Relay mail from remote BBS system using JNOS connection for import
        and SMTP for insertion into JNOS.
        
        Inbound only    
        From one external account only        
        To one internal JNOS user only       
    
    References:
        Basic SMTP
            https://docs.python.org/3/library/smtplib.html
        Structured email messages
            https://docs.python.org/3/library/email.message.html?highlight=emailmessage#email.message.EmailMessage
            https://docs.python.org/3/library/email.message.html

    Debugging:
        Set the variable DEBUG to any non-zero value
        Debug messages will appear in the log file 'mailInBBS.log'
    
    Hints:
    *   If this is run by cron, it must run as 'root' to manipulate files
        */2 * * * * sudo python3 /path/mailInBBS.py
"""


####################################################################################
####################################################################################
####################################################################################
####################################################################################

SECTION 3: Connecting JNOS to actual Internet email

####################################################################################
mailConfig.py

Contains configuration info and "constants" for the various Python scripts.

"""
configuration for
    mailIn.py
    -   Pick up inbound Internet email and transfer to JNOS user area
        Injects using JNOS SMTP, so requires no internal knowledge of
        JNOS file structures.
    mailInBBS.py
    -   Connect to a remote BBS and get any messages for one user.
        Inject those using JNOS SMTP (like mailIn except on the radio).
    mailOut.py
    -   Check JNOS area internet_out and send to Internet mail using SMTP
    mailPopper.py
    -   Run a POP3 server so any local email program can pick up JNOS
        messages and treat them as email. Also using existing JNOS SMTP
        such an app can send to JNOS accounts and to external Internet mail.
    mailStat.py
    -   Report out the numbers of messages in each user area/mailbox by
        sending an email to an admin.
  uses
    mailJNOS.py
    -   Objects and methods for fetching messages from JNOS user areas.
        Note that we do not modify any JNOS files. This is very
        intentional, as the JNOS file structure is not fully docu-
        mented and we might make a mistake. Instead, we use JNOS's
        SMTP to inject new messages, and we telnet to JNOS to delete
        messages.
        Just incidentally, we do not pay any attention to user passwords
        because we have no way to validate them. JNOS is iffy in its
        password use. For example, JNOS's SMTP doesn't require any
        authentication, and is essentially an open relay. However,
        our POP3 code does forward a user password when it's deleting
        old messages (via telnet to JNOS BBS).
"""


####################################################################################
mailJNOS.py

Contains objects and functions for common use by the other Python scripts.

Note that the JNOS .ind and .txt files have a rather opaque structure, much of which I've figured out through long experience and documented in this file!


####################################################################################
mailIn.py

"""
    Relay mail from remote email system using IMAP
        Inbound only
    
        From one external account only
        To any internal JNOS user or to an external email account
        To: "user@BBS" <account@example.com>
        *   Goes thru external email account@example.com, is picked up
        *     here, drops into user@BBS local account.
        To: <account@example.com>
        *   Goes thru external email account@example.com, is picked up
        *     here, drops into default jnosUser local account
        jnosUser:
        *   If it's a user@BBS then the default is to drop incoming
        *     mail into this user account on JNOS.
        *  If it's an Internet email address like account@example.com
        *     AND if the SMTP connection is to an outside email server (!)
        *     then mail is forwarded to that account.
    
    References:
        Basic IMAP pickup using 'imaplib'
            https://docs.python.org/3/library/imaplib.html
        Good examples I used for IMAP processing
            https://pymotw.com/2/imaplib/
        email.parser
            https://docs.python.org/3/library/email.parser.html
        Basic SMTP
            https://docs.python.org/3/library/smtplib.html
        Structured email messages
            https://docs.python.org/3/library/email.message.html?highlight=emailmessage#email.message.EmailMessage
            https://docs.python.org/3/library/email.message.html

    Debugging:
        Set the variable DEBUG to any non-zero value
        Debug messages will appear in the log file 'mail-in.log'
    
    Hints:
    *   If this is run by cron, it must run as 'root' to manipulate files
        */2 * * * * sudo python3 /path/mailOut.py
"""

####################################################################################
mailOut.py

"""
    Relay mail from JNOS to remote email system using SMTP
        Outbount only
    
        From one internal JNOS (box or rewrite area) only (one .ind and .txt)
        To one external account only
    
    References:
        JNOS file index.h contains rough description of the .ind (index)
            and .txt (email repository) files.
        email.parser
            https://docs.python.org/3/library/email.parser.html
        Basic SMTP
            https://docs.python.org/3/library/smtplib.html
        Structured email messages
            https://docs.python.org/3/library/email.message.html?highlight=emailmessage#email.message.EmailMessage
            https://docs.python.org/3/library/email.message.html
    Hints:
    *   If this is run by cron, it must run as 'root' in order to delete
        the database index and mail contents files.
        */2 * * * * sudo python3 /path/mailOut.py
"""


####################################################################################
mailStat.py

Checks mailbox status(es) as reflected in .ind and .txt files and then sends an email summarizing what it finds.

"""
    Check JNOS mailbox status(es) and send an email report.
        
    References:
        JNOS file index.h contains rough description of the .ind (index)
            and .txt (email repository) files.
        Basic SMTP
            https://docs.python.org/3/library/smtplib.html
        Structured email messages
            https://docs.python.org/3/library/email.message.html?highlight=emailmessage#email.message.EmailMessage
            https://docs.python.org/3/library/email.message.html
    Hints:
       If this is run by cron, it must run as 'root'
        0 */4 * * * sudo python3 /PATH/SCRIPT_NAME.py
"""






