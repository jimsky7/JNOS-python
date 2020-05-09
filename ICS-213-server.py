#!/usr/bin/python3
"""
    Wait for HTTP POST On port 8081
    
    When it arrives, if it's the ICS 213 form, prepare a packet message
    and connect to JNOS via SMTP to send it.
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
import os, smtplib, logging, email
import time
from mailConfig import *
import urllib

hostName = "localhost"
hostPort = 8081

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
    log.info('Local server to process ICS 213 forms.')
    if (DEBUG):
        print("Logging to {}".format(PATH_LOGS + scriptName + DOT_LOG))
except:
    print('Can\'t set up log file. Maybe permissions?')
    # NOTE: Continue even if no log was set up.


class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        if (self.requestline.find("/ICS-213.py") < 0):
            return
        s = self.requestline.strip("GET /")
        s = s.strip("ICS-213.py")
        s = s.strip("?")
        s = s.split("&")
        form = {}
        exceptions = 0
        for k in s:
            try:
                kk = k.split('=')
                kk[1] = kk[1].replace("+", " ")
                kk[1] = urllib.parse.unquote(kk[1])
                form[kk[0]] = kk[1]
            except:
                exceptions = exceptions + 1
        
        # Create packet message
        print(form)
        
        # ====================================================================================
        # Connect to the SMTP server (JNOS)
        # This is where messages are delivered to the JNOS mailbox(es)
        if((form.get("PACKET_TO")!=None)):
            if (localSMTPSSL):
                cs = smtplib.SMTP_SSL(localSMTP, 465, None, None, None, 30)
            else:
                cs = smtplib.SMTP(localSMTP, 25)
            cs.helo(sysID)
            # Inject the message
            #
            mailHeaders = {}
            if (form.get("PACKET_TO")==None):
                print("Cannot send. No PACKET_TO.")
                form["PACKET_TO"] = TELNET_USER
            mailHeaders["To"] = form["PACKET_TO"]
            mailHeaders["From"] = TELNET_USER
            if (form.get("SUBJECT")==None):
                form["SUBJECT"] = ""
            mailHeaders["Subject"] = form["SUBJECT"]
            print(mailHeaders)
            
            body = ""
            body = body + "#######################\n"
            body = body + "ICS form 213\n"
            
            if (form.get("TO")==None):
                form["TO"] = ""
            if (form.get("TO_LOCATION")==None):
                form["TO_LOCATION"] = ""
            body = body + "To:   {} // Location: {}\n".format(form["TO"], form["TO_LOCATION"])

            if (form.get("FROM")==None):
                form["TO"] = ""
            if (form.get("FROM_LOCATION")==None):
                form["FROM_LOCATION"] = ""
            body = body + "From: {} // Location: {}\n".format(form["FROM"], form["FROM_LOCATION"])
            
            body = body + "Subject: {}\n".format(form["SUBJECT"])

            if (form.get("DATE")):
                body = body + "DATE: {}\n".format(form.get("DATE"))
            if (form.get("TIME")):
                body = body + "TIME: {}\n".format(form.get("TIME"))
            body = body + "- - - - - - - - - - - -\n"
            
            if (form.get("CHECK_ORIGINAL")=="on"):
                body = body + "X- Original message\n"
            if (form.get("CHECK_REPLY")=="on"):
                body = body + "X- Reply\n"
            
            if (form.get("CHECK_FIREHAZMAT")=="on"):
                body = body + "X- FIRE or HAZMAT\n"
            if (form.get("CHECK_MEDICAL")=="on"):
                body = body + "X- MEDICAL\n"
            if (form.get("CHECK_RESCUE")=="on"):
                body = body + "X- RESCUE\n"
            if (form.get("CHECK_INFRASTRUCTURE")=="on"):
                body = body + "X- INFRASTRUCTURE\n"
            if (form.get("CHECK_OTHER")=="on"):
                body = body + "X- OTHER\n"
            if (form.get("INCIDENT_ADDRESS")):
                body = body + "Incident address: {}\n".format(form.get("INCIDENT_ADDRESS"))
            if (form.get("INCIDENT_CROSSSTREET")):
                body = body + "Cross street: {}\n".format(form.get("INCIDENT_CROSSSTREET"))
            body = body + "- - - - - - - - - - - -\n"
            
            if (form.get("MSG_NUMBER")):
                body = body + "MESSAGE #: {}\n".format(form.get("MSG_NUMBER"))
            
            if (form.get("CHECK_EMERGENCY")=="on"):
                body = body + "X- EMERGENCY\n"
            if (form.get("CHECK_PRIORITY")=="on"):
                body = body + "X- PRIORITY\n"
            if (form.get("CHECK_ROUTINE")):
                body = body + "X- ROUTINE\n"
            if (form.get("CHECK_REPLY_REQUIRED")):
                body = body + "X- REPLY REQUIRED\n"
            if (form.get("CHECK_REPLY_NOT_NEEDED")):
                body = body + "X- REPLY NOT NEEDED\n"
            body = body + "#######################\n"
            
            if (form.get("MESSAGE")==None):
                form["MESSAGE"] = ""
            body = body + "Message: \n{}\n".format(form["MESSAGE"])
            body = body + "- - - - - - - - - - - -\n"

            if (form.get("SIGNATURE")==None):
                form["SIGNATURE"] = ""
            if (form.get("POSITION")==None):
                form["POSITION"] = ""
            body = body + "SIGNATURE: {} // POSITION: {}\n".format(form.get("SIGNATURE"),form.get("POSITION"))
            
            if (form.get("DATE_TIME")==None):
                form["DATE_TIME"] = ""
            if (form.get("CALLSIGN")==None):
                form["CALLSIGN"] = ""
            if (form.get("TACTICAL")==None):
                form["TACTICAL"] = ""
            body = body + "SENT/REC'D: {} // CALLSIGN: {} // TACTICAL: {}\n".format(form.get("DATE_TIME"),form.get("CALLSIGN"), form.get("TACTICAL"))
            body = body + "#######################\n"
 
            if (form.get("REPLY")==None):
                form["REPLY"] = ""
            body = body + "Reply: \n{}\n".format(form["REPLY"])
            body = body + "- - - - - - - - - - - -\n"

            if (form.get("REPLY_SIGNATURE")==None):
                form["REPLY_SIGNATURE"] = ""
            if (form.get("REPLY_POSITION")==None):
                form["REPLY_POSITION"] = ""
            body = body + "SIGNATURE: {} // POSITION: {}\n".format(form.get("REPLY_SIGNATURE"),form.get("REPLY_POSITION"))
            
            if (form.get("REPLY_DATE_TIME")==None):
                form["REPLY_DATE_TIME"] = ""
            if (form.get("REPLY_CALLSIGN")==None):
                form["REPLY_CALLSIGN"] = ""
            if (form.get("REPLY_TACTICAL")==None):
                form["REPLY_TACTICAL"] = ""
            body = body + "SENT/REC'D: {} // CALLSIGN: {} // TACTICAL: {}\n".format(form.get("REPLY_DATE_TIME"),form.get("REPLY_CALLSIGN"), form.get("REPLY_TACTICAL"))
            body = body + "#######################\n"


            moo = email.message.Message()
            moo.set_type('text/plain')
            for ih in mailHeaders.keys():
                moo.__setitem__(ih, mailHeaders[ih])
            moo.set_payload(str(body).encode('utf-8'))
    
            try:
                cs.send_message(moo)
                sentOK = TRUE
                log.info('Queued one ICS 213 message to {} in JNOS.'.format(form["PACKET_TO"]))
                print(   'Queued one ICS 213 message to {} in JNOS.'.format(form["PACKET_TO"]))
            except:
                print("[SMTP] Exception")
                sentOK = FALSE
                        
            cs.quit()
            cs.close()
        
        else:
            print(       'No packet destination address?')
            log.critical('No packet destination address?')
    
        print('========================================================')
        log.debug('========================================================')

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes("<html><head><title>ICS 213</title></head>", "utf-8"))
        self.wfile.write(bytes("<body><p>ICS 213 to packet radio</p>", "utf-8"))
        # self.wfile.write(bytes("<p>You accessed path: %s</p>" % self.path, "utf-8"))
        self.wfile.write(bytes("</body></html>", "utf-8"))
       
myServer = HTTPServer((hostName, hostPort), MyServer)
print(time.asctime(), "Server Starts - %s:%s" % (hostName, hostPort))

try:
    myServer.serve_forever()
except KeyboardInterrupt:
    pass

myServer.server_close()
print(time.asctime(), "Server Stops - %s:%s" % (hostName, hostPort))
