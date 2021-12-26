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

# General items
TRUE           = 1
FALSE          = 0

# DOT_IND and DOT_TXT require initial dot
DOT_IND        = '.ind'
DOT_TXT        = '.txt'
DOT_LOG        = '.log'
DOT_USR        = '.usr'

# PATH (requires ending /)
PATH_JNOS     = '/jnos/'
PATH_LOGS     = '/jnos/logs/'
PATH_MAIL     = '/jnos/spool/mail/'

# Internal JNOS mail system (or test system)
area           = 'internet_out'
inetArea       = 'internet_out'
# For mail-stat
replyTo        = '<pi@aa6ax.us>'
statTo         = '<sky@aa6ax.us>'
statFrom       = '<sky@aa6ax.us>'

# External mail system
mxSMTP         = 'base.red7.com'
mxSMTPSSL      = TRUE
mxIMAP         = 'base.red7.com'
mxIMAPSSL      = TRUE
sysID          = 'PI.AA6AX.US'
BBSname        = 'AA6AX [JNOS BBS]'
user           = 'pi@aa6ax.us'
pw             = 'Nowhere-4'

# Defaults for LIVE AND DEBUG
LIVE           = TRUE
DEBUG          = TRUE

# Defaults for Telnetting to JNOS BBS
TELNET_HOST    = '192.168.2.2'

# local POP3 interface constants
POP3serverID   = "[JNOS+AA6AX] POP3 connector"
replyToPOP3    = "aa6ax@AA6AX"

# for mailInBBS use when connecting to remote BBS via radio
BBS_INTERFACE   = b'vhf'
BBS_CONNECT     = b''

TELNET_USER     = 'aa6ax'
TELNET_PASS     = 'zowie'
TELNET_EOL      = b'\n'

JNOS_PROMPT     = b'>\r'
JNOS_PROMPT_STR = JNOS_PROMPT.decode()
JNOS_WAIT       = 15

BBS_PROMPT      = b'>\r'
BBS_PROMPT_STR  = BBS_PROMPT.decode()
BBS_PROMPT_R    = b'>\r'
BBS_PROMPT_R_STR= BBS_PROMPT_R.decode()
BBS_PROMPT_N    = b'>\n'
BBS_PROMPT_N_STR= BBS_PROMPT_R.decode()
BBS_PROMPT_ARY   = b']>\r'
BBS_PROMPT_ARY_STR= BBS_PROMPT_ARY.decode()
BBS_PROMPT_KPC   = b', or Help >\r'
BBS_PROMPT_KPC_STR= BBS_PROMPT_KPC.decode()
BBS_WAIT        = 180

# ====================================================================================
# for INBOUND Internet email
# External mail system for INBOUND processing (IMAP)
inbox         = 'INBOX'
archive       = 'JNOS_archive'

# ====================================================================================
# Internal JNOS mail system (or test system)
jnosUser      = 'aa6ax'
sysDomain     = 'AA6AX'
localSMTP     = '192.168.2.2'
localSMTPSSL  = FALSE

headersToKeep = ['Date', 'Subject', 'To', 'From']

# Remote node to test in order to verify connectivity
NODE_CHECK_HOST = "n6saf-oak-lhg5xl.local.mesh"
NODE_CHECK_URL  = "/cgi-bin/status"
NODE_CHECK_PORT= 8080
