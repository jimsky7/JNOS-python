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

# ====================================================================================
# ====================================================================================

print('========================================================')

import email, smtplib, telnetlib, logging, os, sys
from mailConfig import *
from telnetlib import Telnet

# ====================================================================================
# General items
# If set, these will override mailConfig.py settings
# LIVE   = FALSE
# DEBUG  = TRUE

#   TELNET_HOST   = '192.168.2.2'
#   jnosUser      = 'aa6ax'
#   sysDomain     = 'AA6AX'
#   localSMTP     = '192.168.2.2'
#   localSMTPSSL  = FALSE

# function to check for JNOS disconnect in common input
def checkCommon(stchk, ctchk, cschk, logchk, bcs):
    # Detect when returned to JNOS
    if (stchk.find( "*** connected") >= 0):
        print(      "*** connected")
        logchk.info(bcs+"*** connected")
        return
    if (stchk.find("*** failure with") >= 0):
        sschk = "Remote BBS connection failed, so now ending the session with JNOS."
        print(sschk)
        logchk.critical(bcs+sschk)
    if ((stchk.find("*** reconnected to") >= 0) or (stchk.find("*** failure with") >= 0)):
        sschk = "Remote BBS connection failed unexpectedly, so now ending the session with JNOS."
        print(sschk)
        logchk.critical(bcs+sschk)
        try:
            ctchk.write(b'BYE' + TELNET_EOL)
            print("BYE")
            logchk.info(bcs+'BYE')

            # Wait for *** Connection...
            # From JNOS
            ctchk.read_until(b'***')
        except EOFError:
            if (DEBUG):
                print("Telnet was closed by JNOS.")
      
        #   End telnet JNOS session
        ctchk.close()
        #   End SMTP JNOS session
        cschk.quit()

        logchk.info(bcs+'All done.')
        print('All done.')
        print(       '========================================================')
        logchk.debug(bcs+'========================================================')
        exit(0)
    return

#   Get these from ARGV[]
ls = len(sys.argv)
if (ls < 3):
    print("USAGE: <interface> <bbsaddr> [<limit>]")
    exit(0)
if (ls==3):
    scriptName, BBS_INTERFACE, BBS_CONNECT = sys.argv
    mnlimit = 1
if (ls==4):
    scriptName, BBS_INTERFACE, BBS_CONNECT, mnlimit = sys.argv
    mnlimit = int(mnlimit)

ss = "Connect to {} via {} interface to retrieve up to {} messages.".format(BBS_CONNECT, BBS_INTERFACE, mnlimit)
print(ss)

BBS_INTERFACE   = BBS_INTERFACE.encode()
BBS_CONNECT     = BBS_CONNECT.encode()
BBS_CALLSIGN_STR= BBS_CONNECT.split(b"-")
BBS_CALLSIGN_STR= BBS_CALLSIGN_STR[0].decode()
BBS_CALLSIGN    = BBS_CALLSIGN_STR.encode()
BBS_TYPE        = b''
BBS_TYPE_STR    = BBS_TYPE.decode()

BCS = BBS_CALLSIGN_STR.upper() + " "
while len(BCS)<8:
    BCS = BCS + " "

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
    log.info(BCS+'========================================================')
    log.info(BCS+'========================================================')
    log.info(BCS+'Begin processing inbound BBS messages.')
    log.info(BCS+'Connecting to {} via {}'.format(BBS_CONNECT.decode(), BBS_INTERFACE.decode()))
    ss = "Will transfer up to {} messages from {} via {}.".format(mnlimit, BBS_CONNECT.decode(), BBS_INTERFACE.decode())
    log.info(BCS+ss)
    print(ss)
    if (DEBUG):
        print("Logging to {}".format(PATH_LOGS + scriptName + DOT_LOG))
except:
    print('Can\'t set up log file. Maybe permissions?')
    # NOTE: Continue even if no log was set up.

if (LIVE == FALSE):
    print('TESTING ONLY. No messages will be deleted from the remote BBS.')
    log.warning(BCS+'TESTING ONLY. No messages will be deleted from the remote BBS.')

# ====================================================================================
# Connect to JNOS command line.
# This is how we'll fire up the radio to talk to the remote BBS

try:
    ct = Telnet(TELNET_HOST)
    ct.open(TELNET_HOST)
except:
    print(          'Unable to connect to {}.'.format(TELNET_HOST))
    log.warning(BCS+'Unable to connect to {}.'.format(TELNET_HOST))
    print(          'Will not be able to talk to JNOS or the remote BBS.')
    log.warning(BCS+'Will not be able to talk to JNOS or the remote BBS.')
else:    
    print(       'Connected (telnet) to JNOS at {}'.format(TELNET_HOST))
    log.info(BCS+'Connected (telnet) to JNOS at {}'.format(TELNET_HOST))

# ====================================================================================
#   Log in JNOS
#   Note there is irregular capitalization "logon:" and "Password" so
#       instead look for only the tail of those prompts.

print(ct.read_until(b'ogin: ', JNOS_WAIT).decode('ascii'))
ct.write(TELNET_USER.encode('ascii') + TELNET_EOL)

print(ct.read_until(b'assword: ', JNOS_WAIT).decode('ascii'))
ct.write(TELNET_PASS.encode('ascii') + TELNET_EOL)

print(ct.read_until(JNOS_PROMPT, JNOS_WAIT).decode('ascii'))

print(       'JNOS login completed.')
log.info(BCS+'JNOS login completed.')

# ====================================================================================
sb = b'connect ' + BBS_INTERFACE + b' ' + BBS_CONNECT
sbd = sb.decode()
print(sbd)
log.info(BCS + sbd)
ct.write(sb + TELNET_EOL)

# ====================================================================================
# Connect to JNOS SMTP.
# This is where messages are delivered to the JNOS mailbox(es)

try:
    if (localSMTPSSL):
        cs = smtplib.SMTP_SSL(localSMTP, 465, None, None, None, 30)
    else:
        cs = smtplib.SMTP(localSMTP, 25)
    cs.helo(sysID)
    # NOTE: No login. Gateway must accept us by open relay or IP address
    # cs.login('pi@aa6ax.us', 'Nowhere-4')
# except SMTPHeloError:
#     print('SMTPHeloError')
# except SMTPAuthenticationError:
#     print('SMTPAuthenticationError')
except:
    print('Unable to establish an SMTP connection to JNOS.')
    print('Is JNOS running?')
    log.critical(BCS+'Unable to establish an SMTP connection to JNOS!')
    log.critical(BCS+'Is JNOS running?')
    exit(0)

# ====================================================================================
# INCOMING messages?
s = ct.read_until(BBS_PROMPT, BBS_WAIT).decode('ascii')
print(s)
checkCommon(s, ct, cs, log, BCS)

# BBS type?
pLines = s.strip("\r").split("\n")
for line in pLines:
    if (line.startswith("[")):
        BBS_TYPE = line.strip("\n")
        break
ss = "BBS type {}".format(BBS_TYPE)
print(ss)
log.info(BCS+ss)
BBS_TYPE_STR = str(BBS_TYPE)

ct.write(b'LM' + TELNET_EOL)
log.info(BCS+'LM')

s = (ct.read_until(BBS_PROMPT, BBS_WAIT).decode('ascii'))
print(s)
checkCommon(s, ct, cs, log, BCS)

mnlist = []
mnkill = []

lmLines = s.strip("\r").split("\n")
print(lmLines)
sw = FALSE

for line in lmLines:
    ls = line.split(" ")
    st = str(ls[0]).strip("b'")
    if (len(st) == 0 or st == '\r' or st.endswith(BBS_PROMPT_STR)):
        sw = FALSE
    if (sw):
        print("Msg: {}".format(st))
        try:
            msgn = int(st)
            mnlist.append(msgn)
        except:
            msgn = 0
    stu = st.upper()
    if (stu.startswith("MSG") or stu.startswith("MESS")):
        sw = TRUE

sl = len(mnlist)
plural = 's'
if (sl==1):
    plural = ''
ss = "{} message{}.".format(sl, plural)
print (ss)
log.info(BCS+ss)
if (sl):
    print(mnlist)
    log.info(BCS+str(mnlist))

mncount = 0

# READ all incoming messages
for msgn in mnlist:
    # Pick up a limited number of messages each time
    mncount = mncount + 1
    if (mncount>mnlimit):
        break
    # Read next message
    sb = b'READ ' + bytes(str(msgn), 'ascii') + b"\n"
    print(sb.decode())
    ct.write(sb)
    if (BBS_TYPE_STR.startswith("[ARY")):
        s = ct.read_until(BBS_PROMPT_ARY, BBS_WAIT).decode('ascii')
    else:
        s = ct.read_until(BBS_PROMPT, BBS_WAIT).decode('ascii')
    # print(s)
    checkCommon(s, ct, cs, log, BCS)

# ====================================================================================
    lmLines = s.strip("\r").split("\n")

    mailHeaders = {'To':'', 'From':'', 'Subject':'', 'Date':''}

    #   Switch based on portion of msg we are processing
    #   'sw' = 0 before headers
    #        = 1 in headers
    #        = 2 in body
    sw = 0
    i = 0
    body = ""
    if (DEBUG):
        print(lmLines)
    log.debug(BCS+str(lmLines))
    ss = "########## {}".format(BBS_TYPE_STR)
    if (DEBUG):
        print(ss)
    log.info(BCS+ss)
    while (sw < 3):
        # Before header: Skip empty lines; skip ====== separators
        if (len(lmLines)==0):
            # Ran out of content in or before any body
            sw = 2
            break
        hl = lmLines[0]
        lh = len(hl)
        if (sw==0):
            if ((hl=='') or (hl=='\r') or ((lh>4) and hl.startswith("==========="))):
                # Ignore before headers and do not transition
                hl = lmLines.pop(0)
                continue
            else:
                # Non-blanks line transitions to header processing
                sw = 1
                if (DEBUG):
                    print(">>> transition to headers")
        # Process header lines
        if (sw==1):
            if ((lh>4) and hl.startswith("----------")):
                # Ignore in headers
                hl = lmLines.pop(0)
                continue
            if ((lh==0) or (hl=='') or (hl=='\r')):
                # Empty line signals end of headers
                hl = lmLines.pop(0)
                sw = 2
                if (DEBUG):
                    print(">>> end of headers")
                continue
            # Process header line
            hl = lmLines.pop(0).strip(" ")
            lh = len(hl)
            if (DEBUG):
                print("Analyzing header[{}]: {}".format(lh, hl))
            # Parse KPC message ID string
            if (BBS_TYPE_STR.startswith("[KPC") and (lh>4) and (hl.upper().startswith("MSG#"))):
                if (DEBUG):
                    print(">>> KPC header")
                # MSG number
                msgParse = hl.split(" ")
                msgNum = msgParse[0].split("#")
                mn = msgNum[1]
                # Date
                msgParse1 = hl.split(" FROM ")
                msgParse1 = msgParse1[0].split(" ")
                # sDate = msgParse1[1] + " " + msgParse1[2]
                # convert KPC date format DD/MM/YYYY HH:MM:SS to DD MMM YYYY, HH:MM:SS
                dmy = msgParse1[1].split("/")
                monthWord = {"01":"Jan", "02":"Feb", "03":"Mar", "04":"Apr", "05":"May", "06":"Jun", "07":"Jul", "08":"Aug", "09":"Sep", "10":"Oct", "11":"Nov", "12":"Dec"}
                sDate = dmy[1]+" "+monthWord[dmy[0]]+" "+dmy[2]+" "+msgParse1[2]
                mailHeaders['Date'] = sDate
                # FROM
                i = msgParse.index("FROM")
                msgFrom = msgParse[i+1]
                mailHeaders['From'] = "{}@{}".format(msgFrom, BBS_CALLSIGN_STR)
                # TO
                i = msgParse.index("TO")
                msgTo = msgParse[i+1]
                mailHeaders['To'] = msgTo
                ss = ">>> completed parsing of KPC3+ MSG header, continuing"
                if (DEBUG):
                    print(ss)
                log.debug(BCS+ss)
                continue
            # All other BBS types (must) send headers
            if (hl.find(":")):
                hla = hl.split(":",1)
                # a header
                hla0u = hla[0].strip('\r').upper()
                if (hla0u.startswith("DATE")):
                    # date
                    mailHeaders['Date'] = hla[1].strip(' \r')
                if (hla0u.startswith("MESSAGE")):
                    # msg number
                    mailHeaders['Message-Id'] = hla[1].strip(' \r')
                if (hla0u.startswith("FROM")):
                    # from
                    mailHeaders['From'] = hla[1].strip(' \r')
                if (hla0u.startswith("TO")):
                    # to
                    mailHeaders['To'] = hla[1].strip(' \r')
                if (hla0u.startswith("SUBJECT")):
                    # subject
                    mailHeaders['Subject'] = hla[1].strip(' \r')
            
        if (sw==2):      
            if (DEBUG):
                print(">>> checking to@/from@")
            # Avoid looping when 'To" contains '@'
            # Just chop off after the '@'
            # ALL incoming messages must end here and not be forwarded
            i = mailHeaders['To'].find("@")
            if (i>0):
                sp = mailHeaders['To'].split('@')
                mailHeaders['To'] = str(sp[0])
            # Add BBS callsign to the 'From'
            i = mailHeaders['From'].find("@")
            if (i<0):
                mailHeaders['From'] = mailHeaders['From'] + "@" + BBS_CALLSIGN_STR
    
            if (DEBUG):
                print(mailHeaders)
                log.debug(BCS+str(mailHeaders))

            if (DEBUG):
                print("Body analysis >>>>>>")
            #   Body
            body = ""
            while (sw == 2):
                k = len(lmLines)
                if (k==0):
                    sw = 3
                    if (DEBUG):
                        print(">>> end of body")
                    break
                # One or more lines remain in body
                bl = lmLines.pop(0)
                lb = len(bl)
                # If one line remains then it's the prompt
                # so don't add to body
                if ((k<3) and (bl.endswith("]>") or bl.endswith(BBS_PROMPT_R_STR))):
                    # (All of that is kind of ad hoc. Trying to differentiate
                    # betwen a BBS prompt ACTUAL and a BBS prompt embedded
                    # in a message.
                    # Sometimes ARY-BBS's end message with ]>\r and other
                    # time just with ]>
                    # So at the very end of incoming packet if the last line
                    # contains the BBS prompt, want to omit it.
                    sw = 3
                    if (DEBUG):
                        print(">>> body ended by prompt [{}] '{}'".format(k, bl))
                else:
                    body = body + bl

    # ensure no raw BBS prompt strings remain on incoming messages
    # doesn't matter locally, but if user replies to one of these,
    # this becomes safer for the ultimate recipient.
    body = body.replace(BBS_PROMPT_STR,   "> \r")
    body = body.replace(BBS_PROMPT_N_STR, "> \n")
    
    if (DEBUG):
        print("Body below >>>>>>")
        print(body)
        log.debug(BCS+body)
        print("Body above >>>>>>")
        print(        '--------------------------------------------------------')
        log.debug(BCS+'--------------------------------------------------------')

    moo = email.message.Message()
    moo.set_type('text/plain')
    for ih in mailHeaders.keys():
        moo.__setitem__(ih, mailHeaders[ih])
    # Add body to message. UTF-8 encoding is fine locally.
    moo.set_payload(str(body).encode('utf-8'))
    
    sentOK = TRUE
    if LIVE:
        print("Message {}: \r\nFrom: {} \r\nTo: {}\r\nSubject: {}\r\nDate: {}".format(msgn, mailHeaders['From'], mailHeaders['To'], mailHeaders['Subject'], mailHeaders['Date']))
        log.info(BCS+"Message {}:".format(i))
        log.info(BCS+"From: {}".format(mailHeaders['From']))
        log.info(BCS+"To: {}".format(mailHeaders['To']))
        log.info(BCS+"Subject: {}".format(mailHeaders['Subject']))
        log.info(BCS+"Date: {}".format(mailHeaders['Date']))
        try:
            cs.send_message(moo)
            sentOK = TRUE
        except:
            print("[SMTP] Exception when attempting to import into JNOS.")            
            log.warning(BCS+"[SMTP] Exception when attempting to import into JNOS.")            
            log.warning(BCS+"[SMTP] This message will be retried next time.")
            sentOK = FALSE
    else:
        print("TEST ONLY: Message {} NOT imported: \r\nFrom: {} \r\nTo: {}\r\nSubject: {}\r\nDate: {}".format(i, mailHeaders['From'], mailHeaders['To'], mailHeaders['Subject'], mailHeaders['Date']))
        log.info(BCS+"Message {} NOT imported:".format(i))
        log.info(BCS+"From: {}".format(mailHeaders['From']))
        log.info(BCS+"To: {}".format(mailHeaders['To']))
        log.info(BCS+"Subject: {}".format(mailHeaders['Subject']))
        log.info(BCS+"Date: {}".format(mailHeaders['Date']))
        sentOK = FALSE
    if(sentOK):
        if (LIVE):
            ss = "KILL {}".format(msgn)
            print(ss)
            ct.write(ss.encode('ascii') + TELNET_EOL)
            st = ct.read_until(BBS_PROMPT, BBS_WAIT).decode('ascii')
            print(st)
            checkCommon(st, ct, cs, log, BCS)
            log.info(BCS+ss)
            # List of deleted message numbers
            mnkill.append(msgn)
        else:
            ss = "Message {} not deleted from remote BBS -- not LIVE".format(msgn)
            print(ss)
            log.warning(BCS+ss)

# ====================================================================================        
# ====================================================================================
ct.write(b'BYE' + TELNET_EOL)
print("BYE")
log.info(BCS+'BYE')

# Wait for *** Connection...
# From JNOS
try:
    ct.read_until(b'*** ')
except EOFError:
    if (DEBUG):
        print(        "Telnet was closed by JNOS.")
        log.debug(BCS+"Telnet was closed by JNOS.")
      
#   End telnet JNOS session
ct.close()
cs.quit()

log.info(BCS+'All done.')
print(       'All done.')
print(        '========================================================')
log.debug(BCS+'========================================================')





