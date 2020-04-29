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

# ====================================================================================
# Change these to override mailConfig.py settings
# LIVE = TRUE
# DEBUG = FALSE

print('========================================================')

import email, smtplib, os.path, logging, datetime
from os import path
from datetime import time
from mailConfig import *
from mailJNOS import *

ds = str(datetime.datetime.now().ctime())
statSubject = BBSname + ' ' + ds

# ====================================================================================
# Set up logging
scriptPath, scriptName = os.path.split(__file__)
scriptName = scriptName.split('.')[0]
if (DEBUG):
    logLevel = logging.DEBUG
else:
    logLevel = logging.INFO
try:
    logFormat = '%(asctime)-15s %(message)s'
    logging.basicConfig(filename=(PATH_LOGS + scriptName + DOT_LOG), level=logLevel, format=logFormat)
    log = logging.getLogger(scriptName)
    log.info('========================================================')
    log.info('========================================================')
    log.info('Begin JNOS mailbox stats.')
    if (DEBUG):
        print("Logging to {}".format(PATH_LOGS + scriptName + DOT_LOG))
except PermissionError:
    print("Can't open or create a log file due to permissions violation.")
    log.warning("Can't open or create a log file due to permissions violation.")
except:
    print("Can't open or create a log file.")
    log.warning("Can't open or create a log file.")
    # NOTE: Continue even if no log was set up.

if (not LIVE):
    print('TEST ONLY. No messages will be sent.')
    log.info('TEST ONLY. No messages will be sent.')
   
# Loop thru the internal (JNOS) areas/users
# Each one consists of an index file USER.ind and email repository USER.txt

areasReported = 0
try:
    dir = os.listdir(PATH_MAIL)
    dir.sort()
    if (DEBUG):
        print("Spool directory is " + PATH_MAIL)
    log.debug("Spool directory is " + PATH_MAIL)
    s =  BBSname + "\r\n"
    s += ds + "\r\n\r\n"
    s += "Area           Count Read\r\n"
    s += "=========================\r\n"
    for fdn in dir:
        if (fdn.lower().endswith(DOT_IND.lower())):
            try:
                log.debug('Checking {}'.format(fdn))
                a = fdn.rstrip(DOT_IND)
                cp = JNOSarea(a, PATH_MAIL, log)
                if (cp.isOpen()):
                    rc  = cp.getRecordCount()
                    rrc = cp.getReadRecordCount()
                    s += a.ljust(15, " ")
                    s += str(rc).rjust(5, " ")
                    s += str(rrc).rjust(5, " ")
                    s+= "\r\n"
                    areasReported = areasReported + 1
            except:
                if (DEBUG):
                    print("Failed " + fdn)
                log.debug("Failed " + fdn)
    s += "=========================\r\n"
    print(s)
    log.info(s)
    body = s
except:
    print("Could not open " + PATH_MAIL)
    exit(0)
    
if (areasReported):
    # Connect to the SMTP server (remote)

    try:
        if (mxSMTPSSL):
            cs = smtplib.SMTP_SSL(mxSMTP, 465, None, None, None, 30)
        else:
            cs = smtplib.SMTP(mxSMTP, 25)
        cs.helo(sysID)
        # cs.login(user, pw)
    except SMTPAuthenticationError:
        print('SMTPAuthenticationError')
    except:
        print('Exception when connecting for outbound SMTP')
        exit(0)

moo = email.message.Message()
moo.add_header('To', statTo)
moo.add_header('From', statFrom)
moo.add_header('Subject', statSubject)
moo.add_header('Date', ds)
headers = ""
headers += "To: {}\r\n".format(statTo)
headers += "From: {}\r\n".format(statFrom)
headers += "Subject: {}\r\n".format(statSubject)
headers += "Date: {}\r\n".format(ds)
moo.set_type('text/html')
moo.set_payload(str("<PRE>\r\n\r\n" + body + "</PRE>"))
    
if LIVE:
    try:
        cs.send_message(moo)
        print("Report mailed to {}".format(statTo))
        log.info("Report mailed to {}".format(statTo))
    except smtplib.SMTPRecipientsRefused:
        print("Recipient refused {}".format(statTo))
        log.info("Recipient refused {}".format(statTo))
else:
        print("TEST ONLY: Report was not mailed to {}".format(statTo))
        log.info("TEST ONLY: Report was not mailed to {}".format(statTo))
cs.quit()



print('========================================================')
log.info('========================================================')

