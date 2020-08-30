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

# ====================================================================================
# ====================================================================================

print('========================================================')

import imaplib, email, smtplib, logging, os, base64, quopri
from mailConfig import *

class ExitNow(Exception):
    pass

# ====================================================================================
# General items
# If set, these will override mailConfig.py settings
# LIVE   = FALSE
# DEBUG  = TRUE
 
# ====================================================================================
# Set up logging
scriptPath, scriptName = os.path.split(__file__)
scriptName = scriptName.split(".")[0]
if (DEBUG):
    logLevel = logging.DEBUG
else:
    logLevel = logging.INFO
try:
    logFormat = "%(asctime)-15s %(message)s"
    logging.basicConfig(filename=(PATH_LOGS + scriptName + DOT_LOG), level=logLevel, format=logFormat)
    log = logging.getLogger(scriptName)
    log.info("========================================================")
    log.info("========================================================")
    log.info("Begin processing inbound Internet email.")
    if (DEBUG):
        print("Logging to {}".format(PATH_LOGS + scriptName + DOT_LOG))
except:
    print("Can't set up log file. Maybe permissions?")
    # NOTE: Continue even if no log was set up.

if (LIVE == FALSE):
    print(   "TESTING ONLY. No messages will be sent or archived.")
    log.info("TESTING ONLY. No messages will be sent or archived.")

cs = None

def openSMTP(cso):
    # ====================================================================================
    # Connect to JNOS SMTP.
    # This is where messages are delivered to the JNOS mailbox(es)

    # SMTP already open?
    if (cso != None):
        return cso
    
    # Open the SMTP connection now
    try:
        if (localSMTPSSL):
            cso = smtplib.SMTP_SSL(localSMTP, 465, None, None, None, 30)
        else:
            cso = smtplib.SMTP(localSMTP, 25)
        cso.helo(sysID)
    except:
        print("Unable to establish an SMTP connection to JNOS.")
        print("Is JNOS running?")
        log.critical(BCS+"Unable to establish an SMTP connection to JNOS!")
        log.critical(BCS+"Is JNOS running?")
        exit(0)
    return cso

# ====================================================================================
# Connect to the IMAP server (remote)
# This server is where messages from the Internet are received

try:
    if (mxIMAPSSL):
        cp = imaplib.IMAP4_SSL(mxIMAP)
    else:
        cp = imaplib.IMAP4(mxIMAP)
except:
    print("Unable to establish an IMAP connection with {}.".format(mxIMAP))
    print("Will not be able to pick up inbound mail.")
    log.warning("Unable to establish an IMAP connection with {}.".format(mxIMAP))
    log.warning("Will not be able to pick up inbound mail.")
else:    
    print(   "Connected to IMAP server at {} for inbound mail.".format(mxIMAP))
    log.info("Connected to IMAP server at {} for inbound mail.".format(mxIMAP))

# Authenticate for pick up of IMAP
try:
    cp.login(user, pw)
except:
    print(       "IMAP login failed. Credentials may be incorrect.")
    log.critical("IMAP login failed.")
    exit(0)

namespace = cp.namespace()
log.debug(namespace[1][0])

# ====================================================================================
# Setup for inbound

# Select INBOX messages
# Will go thru and will relay these, then move
#   each one to /JNOS-archive and
#   mark as deleted in INBOX.
cp.select(inbox)
typ, mnb = cp.search(None, "ALL")
mns = str(mnb)
# mnnlist will be a list of message numbers to retrieve
mnlist = mns.strip("][b'").split(" ")
nm = len(mnlist)
# Number of messages waiting
# Check for empty
if mnlist[0]=="":
    print(   "No new mail.")
    log.info("No new mail.")
    nm = 0
    mnlist = []
else:
    print(   "{} new messages available. {}".format(nm, mns))
    log.info("{} new messages available. {}".format(nm, mns))
    
# List of messages to be deleted
mndeleted = []

# ====================================================================================
# Process all incoming messages
for i in mnlist:
    # Extract headers from incoming message
    mailHeaders = {"To":"", "From":"", "Subject":"", "Date":""}
    if (DEBUG):
        print(    "--------------------------------------------------------")
        log.debug("--------------------------------------------------------")
    # DEBUG print start of message
    # print(cp.retr(i+1)[1])
    
    # Get the next message.
    # There's no distinction on whether message is new or old.
    # If it is in INBOX, it will be processed.
    # After processing, it is copied to JNOS_archive and
    # marked/flagged as deleted.
    typ, msg_data = cp.fetch(str(i), "(RFC822)")
    
    # Parse the incoming email
    for response_part in msg_data:
        if isinstance(response_part, tuple):
            parsed_email = email.message_from_bytes(response_part[1])
            if (DEBUG):
                for header in [ "subject", "to", "from", "date" ]:
                    print("%-8s: %s" % (header.upper(), parsed_email[header]))
                print("--------------------------------------------------------")
      
    mp = parsed_email.is_multipart()
    log.debug("Message {} incoming: {} Multipart?: {}".format(i, parsed_email.get_default_type(), mp))
    body = ""

    # Get body of this email
    if mp:
        log.debug("Multipart")
        log.debug(parsed_email.get_boundary())
        body = parsed_email.get_payload(0).as_string()
        # WARNING: needs quoted-printable decoded
    else:
        log.debug("Not multipart")
        body = parsed_email.get_payload()
        # WARNING: needs quoted-printable decoded
    
    # Decode base64 if present
    # (Note unreliable way to detect base64 that will fail, for instance,
    #  if the message just includes the string.)
    try:
        x64,y64,z64 = body.rpartition("Content-Transfer-Encoding: base64")
        if (y64!=""):
            b = base64.b64decode(z64)
            print(    "Message was decoded from base64 to utf-8")
            log.debug("Message was decoded from base64 to utf-8")
            body = b.decode("utf-8")
    except:
        traceback.print_tb(sys.exc_info()[2])
        print(       "Exception: {} {}".format(sys.exc_info()[0], sys.exc_info()[1]))
        log.critical("Exception: {} {}".format(sys.exc_info()[0], sys.exc_info()[1]))
    
    # Decode quoted-printable if present
    # (Note unreliable way to detect quoted-printable)
    try:
        if (body.find("=\r") or body.find("=20\r")):
            b = quopri.decodestring(bytes(body, "utf-8"))
            print(    "Message was decoded from quoted-printable to utf-8")
            log.debug("Message was decoded from quoted-printable to utf-8")
            body = b.decode("utf-8")
    except:
        traceback.print_tb(sys.exc_info()[2])
        print(       "Exception: {} {}".format(sys.exc_info()[0], sys.exc_info()[1]))
        log.critical("Exception: {} {}".format(sys.exc_info()[0], sys.exc_info()[1]))
    
    log.debug("--------------------------------------------------------")
    # Keep (transfer) certain headers to msg we're building
    for headerKey in headersToKeep:
        if headerKey in parsed_email.keys():
            mailHeaders[headerKey] = parsed_email[headerKey]
    
    # Transform the 'To:' header if an account is present
    to = mailHeaders["To"]

    log.debug("Analyzing To: {}".format(to))
    # May be of the form "area@BBS" <email>

    # Check any quoted part, as this may be the area/mailbox plus BBS name
    s = to.split("\"")    
    if ((len(s)>1) and len(s[1])):
        # area@BBS was explicitly set
        if (jnosUser.count(".")):
            # Internet forwarding has '.' in the address
            mailHeaders["To"] = "\"{}\" <{}>".format(s[1].strip("\""), jnosUser.strip(" ><"))
        else:
            # BBS forwarding
            mailHeaders["To"] = s[1].strip("\"")
    else:
        # area@BBS not set, use default
        if (jnosUser.count(".")):
            # Internet forwarding has '.' in the address
            mailHeaders["To"] = "<{}>".format(jnosUser.strip(" ><"))
        else:
             # BBS forwarding
            mailHeaders["To"] = "<{}>".format(jnosUser.strip(" ><"))
    
    # print the final headers
    for hk in mailHeaders:
        log.debug(hk+": " + mailHeaders[hk])
    log.debug('--------------------------------------------------------')
    
    sw = 0
    
    # Connect to SMTP and inject the message
    #
    moo = email.message.Message()
    moo.set_type("text/plain")
    for ih in mailHeaders.keys():
        moo.__setitem__(ih, mailHeaders[ih])
    moo.set_payload(str(body).encode("utf-8"))
    
    sentOK = TRUE
    
    if LIVE:
        print(   "Message {} relayed: \r\nFrom: {} \r\nTo: {}\r\nSubject: {}\r\nDate: {}".format(i, mailHeaders["From"], mailHeaders["To"], mailHeaders["Subject"], mailHeaders["Date"]))
        log.info("Message {} relayed:".format(i))
        log.info("From: {}".format(mailHeaders["From"]))
        log.info("To: {}".format(mailHeaders["To"]))
        log.info("Subject: {}".format(mailHeaders["Subject"]))
        log.info("Date: {}".format(mailHeaders["Date"]))
        try:
            cs = openSMTP(cs)
            cs.send_message(moo)
            sentOK = TRUE
        except:
            print(      "[SMTP] Exception when attempting to send this message.")            
            log.warning("[SMTP] Exception when attempting to send this message.")            
            log.warning("[SMTP] This message will be retried.")
            sentOK = FALSE
    else:
        print(   "TEST ONLY: Message {} NOT relayed: \r\nFrom: {} \r\nTo: {}\r\nSubject: {}\r\nDate: {}".format(i, mailHeaders["From"], mailHeaders["To"], mailHeaders["Subject"], mailHeaders["Date"]))
        log.info("Message {} NOT relayed:".format(i))
        log.info("From: {}".format(mailHeaders["From"]))
        log.info("To: {}".format(mailHeaders["To"]))
        log.info("Subject: {}".format(mailHeaders["Subject"]))
        log.info("Date: {}".format(mailHeaders["Date"]))
        
    # Copy this message to the archive
    log.debug("--------------------------------------------------------")
    try:
        # Try to create new archive (mailbox)
        if (LIVE):
            typ, cr = cp.create(archive)
    except:
        log.debug(    "Message will be archived in {}.".format(archive))
    else:
        if (LIVE):
            log.debug("Message will be archived in {}.".format(archive))
        
    try:
        if LIVE:
            cp.copy(str(i), archive)
    except Exception as ex:
        print("Exception while attempting to archive message {} to {}.".format(i, archive))
    else:
        if LIVE:
            log.debug("Copied message {} to {}.".format(i, archive))
        else:
            log.debug("TEST ONLY: Live system would copy message {} to {}.".format(i, archive))
        if (sentOK):
            mndeleted.append(str(i))
        
# ====================================================================================
# All messages relayed, now mark them Deleted from INBOX
# Note: Do this in one fell swoop after all messages have been read.
if len(mndeleted):
    log.debug('========================================================')
    for i in mndeleted:
        if LIVE:
            cp.store(str(i), "+FLAGS", "\\Deleted")
            log.debug("Marked message {} deleted in {}.".format(i, inbox))
        else:
            log.debug("TEST ONLY: Live system would mark message {} deleted in {}.".format(i, inbox))

# ====================================================================================
# Everything relayed, close connections    
cp.logout()
if (cs != None):
    cs.quit()

log.info("All done.")
print(   "All done.")
print(    "========================================================")
log.debug("========================================================")
