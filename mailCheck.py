"""
    Check JNOS mailbox status(es) and send an email report
        only if any box has changed.
        
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

print("========================================================")

import email, smtplib, os.path, logging, datetime, traceback, socket
from os import path
from datetime import time
from time import localtime
from mailConfig import *
from mailJNOS import *
from traceback import *
# from datetime import timezone, tzinfo

class ExitNow(Exception):
    pass

dn = datetime.datetime.now()
dntz  = int(localtime().tm_gmtoff / 36)
if (dntz < 0):
    dntz = "-{:>04}".format(abs(dntz))
else:
    dntz = "{:>04}".format(dntz)
ds = str(dn.strftime("%a, %d %b %Y %H:%M:%S " + dntz))

# Choice of simple or fancy subject line
# Note the fancy UTF-style line is broken in two so as to avoid 75-limit
simpleSubject = BBSname + " " + ds
fancySubject  = "=?UTF-8?Q?" + BBSname + " =E2=9D=8C?=\r\n " + ds
statSubject   = fancySubject

# Subject: =?UTF-8?Q?Work_From_Home=3F_=E2=9D=8C_Work_From_Omni=3F?=
# =?UTF-8?Q?_=E2=9C=94=EF=B8=8F?=
 
# Note: statFrom contains an email address, including '@' and the @ is
#   required in order to construct a valid message ID (per RFC 2822)
statMID     = str(datetime.datetime.now().strftime("%d%m%Y%H%M%S_"+statFrom.strip("<>")))

DEBUG = TRUE

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
    log.info("========================================================")
    log.info("========================================================")
    log.info("Begin JNOS mailbox checks.")
    if (DEBUG):
        print("Logging to {}".format(PATH_LOGS + scriptName + DOT_LOG))
except PermissionError:
    print(      "Can't open or create a log file due to permissions violation.")
    log.warning("Can't open or create a log file due to permissions violation.")
except:
    print(      "Can't open or create a log file.")
    log.warning("Can't open or create a log file.")
    # NOTE: Continue even if no log was set up.

if (not LIVE):
    print(   "TEST ONLY. No messages will be sent.")
    log.info("TEST ONLY. No messages will be sent.")
   
# Check whether JNOS is running
JNOSSMTPstatus = "JNOS is running."
forceMail = FALSE
try:
    cso = smtplib.SMTP(localSMTP, 25)
    cso.helo(sysID)
    print(JNOSSMTPstatus)
    log.critical("JNOS is running.")
except:
    log.critical("Unable to establish an SMTP connection to JNOS!")
    JNOSSMTPstatus = "WARNING: JNOS is not running."
    print(JNOSSMTPstatus)
    forceMail = TRUE

hostName = socket.gethostname()
ipAddress = socket.gethostbyname(hostName+".local")
ipAddressMsg = "{} Local IP address is {}\r\n".format(hostName, ipAddress)
print(    ipAddressMsg)
log.debug(ipAddressMsg)
 
# Loop thru the internal (JNOS) areas/users
# Each one consists of an index file USER.ind and email repository USER.txt

areasReported = 0
try:
    dir = os.listdir(PATH_MAIL)
    dir.sort()
    if (DEBUG):
        print("Spool directory is " + PATH_MAIL)
        log.debug("Spool directory is " + PATH_MAIL)
    s1 = BBSname + "\r\n" + JNOSSMTPstatus + "\r\n"
    s2 = ds + "\r\n\r\n"
    s3 =  "Area           Count  New\r\n"
    s3 += "=========================\r\n"
    for fdn in dir:
        if (fdn.startswith("_") or fdn.startswith(".")):
            continue
        if (fdn.lower().endswith(DOT_IND.lower())):
            try:
                log.debug("Checking {}".format(fdn))
                a = fdn.rstrip(DOT_IND)
                cp = JNOSarea(a, PATH_MAIL, log)
                if (cp.isOpen()):
                    rc  = cp.getRecordCount()
                    rrc = cp.getReadRecordCount()
                    s3 += a.ljust(15, " ")
                    s3 += str(rc).rjust(5, " ")
                    s3 += str(rrc).rjust(5, " ")
                    s3 += "\r\n"
                    areasReported = areasReported + 1
            except:
                if (DEBUG):
                    print("Failed " + fdn)
                log.debug("Failed " + fdn)
    s3 += "=========================\r\n\r\n"
    s3 += JNOSSMTPstatus + "\r\n"
    sender = "\r\nSent by: " + scriptName
    using  = "\r\nUsing " + mxSMTP
    body = s1 + s2 + s3 + ipAddressMsg + sender + using
    print(body)
    log.info(body)
except:
    print(       "Could not open " + PATH_MAIL)
    log.critical("Could not open " + PATH_MAIL)
    raise ExitNow
    
sfn = "_" + scriptName + DOT_TXT
try:
    if (areasReported):
        print(    "{} areas were examined.".format(areasReported))
        log.debug("{} areas were examined.".format(areasReported))
        # Was there any change?
        stbody = ""
        try:
            st = open(PATH_MAIL + sfn, "r")
            stbody = st.read(-1)
            st.close()
        except:
            stbody = ""
            forceMail = TRUE
        try:
            st = open(PATH_MAIL + sfn, "w")
        except:
            traceback.print_tb(sys.exc_info()[2])
            print(       "Exception: {} {}".format(sys.exc_info()[0], sys.exc_info()[1]))
            log.critical("Exception: {} {}".format(sys.exc_info()[0], sys.exc_info()[1]))
            raise ExitNow
        s4 = s3.replace("\r","")
        s4 = s4.replace("\n","")
        st.write(s4)
        st.close()
            
        if ((stbody != s4) or forceMail):
            # Connect to the SMTP server (remote)
            # Send message indicating that counts have changed
            body = s1 + s2 + "Conditions have changed!\r\n\r\n" + s3 + ipAddressMsg + sender

            try:
                if (mxSMTPSSL):
                    cs = smtplib.SMTP_SSL(mxSMTP, 465, None, None, None, 30)
                    #    cs.set_debuglevel(1)
                else:
                    cs = smtplib.SMTP(mxSMTP, 25)
                cs.ehlo_or_helo_if_needed()
                cs.login(user, pw)
            except:
                print(       "Could not connect to {}\r\n".format(mxSMTP))
                log.critical("Could not connect to {}\r\n".format(mxSMTP))
                traceback.print_tb(sys.exc_info()[2])
                print(       "Exception: {} {}".format(sys.exc_info()[0], sys.exc_info()[1]))
                log.critical("Exception: {} {}".format(sys.exc_info()[0], sys.exc_info()[1]))
                # If could not send message, it could be due to a temporary
                #   failure in DNS or routing or timeout.
                # Deleting the 'memory' file ensures the script will
                #   attempt to send a message the next time it runs.
                try:
                    os.remove(PATH_MAIL + sfn)
                except:
                    print(       "Failed to remove " + PATH_MAIL + sfn)
                    log.critical("Failed to remove " + PATH_MAIL + sfn)
                # Now exit with stack trace
                raise ExitNow

            moo = email.message.Message()
            moo.add_header("To",      statTo)
            moo.add_header("From",    statFrom)
            moo.add_header("Subject", statSubject)
            moo.add_header("Date",    ds)
            moo.add_header("Message-ID", "<" + statMID + ">")
            moo.add_header("User-Agent", "JNOS-AA6AX")
            moo.set_type('text/plain')
            moo.set_payload(str(body))
    
            if LIVE:
                try:
                    cs.send_message(moo)
                    print(   "Report mailed to {}".format(statTo))
                    log.info("Report mailed to {}".format(statTo))
                except:
                    traceback.print_tb(sys.exc_info()[2])
                    print(       "Exception: {} {}".format(sys.exc_info()[0], sys.exc_info()[1]))
                    log.critical("Exception: {} {}".format(sys.exc_info()[0], sys.exc_info()[1]))
                    # If could not send message, it could be due to a temporary
                    #   failure in DNS or routing or timeout.
                    # Deleting the 'memory' file ensures the script will
                    #   attempt to send a message the next time it runs.
                    try:
                        os.remove(PATH_MAIL + sfn)
                    except:
                        print(       "Failed to remove " + PATH_MAIL + sfn)
                        log.critical("Failed to remove " + PATH_MAIL + sfn)
                    # Now exit with stack trace
                    raise ExitNow
            else:
                print(   "TEST ONLY: Report was not mailed to {}".format(statTo))
                log.info("TEST ONLY: Report was not mailed to {}".format(statTo))

            cs.quit()
        else:
            print(   "No change. Report was not mailed.")
            log.info("No change. Report was not mailed.")

except ExitNow:
    print(       "Exiting now.")
    log.critical("Exiting now.")
except:
    traceback.print_tb(sys.exc_info()[2])
    print(       "Exception: {} {}".format(sys.exc_info()[0], sys.exc_info()[1]))
    log.critical("Exception: {} {}".format(sys.exc_info()[0], sys.exc_info()[1]))
    
print(   "========================================================")
log.info("========================================================")

