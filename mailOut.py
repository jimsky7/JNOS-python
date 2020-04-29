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

# ====================================================================================
# ====================================================================================
# Enable these if you wish to to override defaults from mailConfig.py
# LIVE = TRUE
# DEBUG = FALSE
# ====================================================================================
# ====================================================================================

import email, smtplib, os.path, logging
from os import path
from mailConfig import *
from mailJNOS import *

print('========================================================')

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
    log.info('Begin processing outbound Internet email.')
    if (DEBUG):
        print("Logging to {}".format(PATH_LOGS + scriptName + DOT_LOG))
except:
    print('Can\'t set up log file. Maybe permissions?')
    # NOTE: Continue even if no log was set up.

if (LIVE == FALSE):
    print('TESTING ONLY. No messages will be sent.')
    log.info('TESTING ONLY. No messages will be sent.')

# Begin by checking that spool data exists
dbExists = path.exists(PATH_MAIL + inetArea + DOT_IND) and path.exists(PATH_MAIL + inetArea + DOT_TXT)
log.debug('Checking {}'.format(PATH_MAIL + inetArea + DOT_IND))
log.debug('Checking {}'.format(PATH_MAIL + inetArea + DOT_TXT))
if (not dbExists):
    print(   'Internet/mailbox "{}" is empty. Nothing to send.'.format(inetArea))
    log.info('Internet/mailbox "{}" is empty. Nothing to send.'.format(inetArea))
    print(   'All done')
    log.info('All done')
    exit(0)

# Save file lengths so can check not modified before we exit
lenIND = os.path.getsize(PATH_MAIL + inetArea + DOT_IND)
lenTXT = os.path.getsize(PATH_MAIL + inetArea + DOT_TXT)
if (DEBUG):
    print('Index file length: {}\r\nMail file length: {}'.format(lenIND, lenTXT))

cp = JNOSarea(inetArea, PATH_MAIL, log)
if (cp.isOpen()):
    print(   cp.status())
    log.info(cp.status())
    rc = cp.getRecordCount()
    # print('Message count is {}'.format(rc))
else:
    print('Failed to open, or no file present for "{}"'.format(inetArea))
    log.critical('Failed to open, or no file present for "{}"'.format(inetArea))
    exit(0)
    
if (rc):
    # Connect to the SMTP server (remote)

    try:
        if (mxSMTPSSL):
            cs = smtplib.SMTP_SSL(mxSMTP, 465, None, None, None, 30)
        else:
            cs = smtplib.SMTP(mxSMTP, 25)
        cs.helo(sysID)
        # cs.login(user, pw)
    except SMTPAuthenticationError:
        print(       'SMTPAuthenticationError')
        log.critical('SMTPAuthenticationError')
        exit(0)
    except:
        print(       'Exception when connecting for outbound SMTP')
        log.critical('Exception when connecting for outbound SMTP')
        exit(0)

for i in range(1, rc+1):
    print('\r\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Message {}'.format(i))
    log.info( '>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Message {}'.format(i))
    result = cp.nextMessage()
    # print(cp.getRawMessage())
    parsed_email = email.message_from_bytes(cp.getRawMessage())
    mailHeaders = {'To':'', 'From':'', 'Subject':'', 'Date':'', 'Reply-To':'<'+replyTo+'>', 'X-Envelope-To':''}
    for headerKey in headersToKeep:
        if headerKey in parsed_email.keys():
            mailHeaders[headerKey] = parsed_email[headerKey]
    # Force completely valid Reply-To: and From: headers
    # When someone replies, we will use those to route the 
    #   reply to the proper area (BBS mailbox)
    # These are of the form
    #   "area@BBS" <acct@example.com>
    #   area: the callsign, like 'aa6ax'
    #   BBS: the JNOS BBS name, like 'AA6AX'
    #   acct: the email account name (without domain)
    #   example.com: the Internet domain
    mailHeaders['From'] = '"{}" <{}>'.format(mailHeaders['From'], replyTo)
    mailHeaders['Reply-To'] = mailHeaders['From']
    env = cp.envelopeTo()
    mailHeaders['X-Envelope-To'] = mailHeaders['To']
    mailHeaders['To'] = env
    # print the final headers
    log.debug('--------------------------------------------------------')
    log.debug('Headers as sent')
    for hk in mailHeaders:
        log.debug(hk + ': '+mailHeaders[hk])
    log.debug('--------------------------------------------------------')
    mp = parsed_email.is_multipart()
    if (mp):
        body = parsed_email.get_payload(0)
    else:
        body = parsed_email.get_payload()
    #DEBUG print('BODY >> {}'.format(body))
    #DEBUG print('--------------------------------------------------------')
    
    moo = email.message.Message()
    moo.set_type('text/plain')
    for ih in mailHeaders.keys():
        moo.__setitem__(ih, mailHeaders[ih])
    # Add body to message. UTF-8 encoding is fine (it's Internet mail after all)
    moo.set_payload(str(body).encode('utf-8'))
    
    if LIVE:
        try:
            cs.send_message(moo)
            print("Message {} sent as Internet email: \r\nFrom: {} \r\nTo: {}\r\nReply-To: {}\r\nSubject: {}\r\nDate: {}".format(i, mailHeaders['From'], mailHeaders['To'], mailHeaders['Reply-To'], mailHeaders['Subject'], mailHeaders['Date']))
            log.info("Message {} sent as Internet email: ".format(i))
        except smtplib.SMTPRecipientsRefused:
            print("Message {} recipent refused: \r\nFrom: {} \r\nTo: {}\r\nReply-To: {}\r\nSubject: {}\r\nDate: {}".format(i, mailHeaders['From'], mailHeaders['To'], mailHeaders['Reply-To'], mailHeaders['Subject'], mailHeaders['Date']))
            log.info("Message {} recipent refused: ".format(i))            
    else:
        print("Message {} NOT sent as Internet email: \r\nFrom: {} \r\nTo: {}\r\nReply-To: {}\r\nSubject: {}\r\nDate: {}".format(i, mailHeaders['From'], mailHeaders['To'], mailHeaders['Reply-To'], mailHeaders['Subject'], mailHeaders['Date']))
        log.info("Message {} NOT sent as Internet email: ".format(i))
    for kh in mailHeaders.keys():
        log.info('{}: {}'.format(kh, mailHeaders[kh]))
        print('{}: {}'.format(kh, mailHeaders[kh]))


log.info('--------------------------------------------------------')
log.info('Completed the loop. {}'.format(rc))
cp.closeAll()

if (rc):
    cs.quit()
    # Check size of area/mailbox email database and
    #   if size has changed, then do not delete.
    # This only results when another process has written new
    #   mail into the box while we were processing, so we do
    #   not want to delete the database in that case.
    endIND = os.path.getsize(PATH_MAIL + inetArea + DOT_IND)
    endTXT = os.path.getsize(PATH_MAIL + inetArea + DOT_TXT)
    print('--------------------------------------------------------')
    log.info('--------------------------------------------------------')
    if (LIVE):
        if ((endIND == lenIND) and (endTXT == lenTXT)):
            # Delete database files
            try:
                os.remove(PATH_MAIL + inetArea + DOT_IND)
                os.remove(PATH_MAIL + inetArea + DOT_TXT)
                print('Mail data for "{}" has been processed and cleared.'.format(inetArea))       
                log.info('Mail data for "{}" has been processed and cleared.'.format(inetArea))       
            except:
                print('IOError attempting to remove mail data. {}'.format(PATH_MAIL + inetArea))       
                log.warning('IOError attempting to remove mail data. {}'.format(PATH_MAIL + inetArea))       
        else:
            print('WARNING: Mail data for "{}" has changed and was not cleared.'.format(inetArea))       
            log.warning('WARNING: Mail data for "{}" has changed and was not cleared.'.format(inetArea))       
    else:
        print('TEST ONLY: Mail data for "{}" is not cleared when testing.'.format(inetArea))       
        log.warning('TEST ONLY: Mail data for "{}" is not cleared when testing.'.format(inetArea))       

print('--------------------------------------------------------')
log.info('--------------------------------------------------------')
print('All done')
log.info('All done')

