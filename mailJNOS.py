import logging
import os
import sys
from mailConfig import *

class JNOSarea(object):
    """
        One JNOS 'area' or user.
        
        Open the index (user.ind) and provide support for
        sequential read of email contents (from user.txt).
        
        area:
        path:
        indexFilename:
        textFilename:
        fi: index file object
        ft: text file object
        index: the whole index as a bytes object
        indexLen: size of index in bytes
        indexRecordCount: number of records
        indexPos: position currently parsing in index object
        currentRecordNumber: current record number (zero-based)
        textPos: position next to read in text (email messages) file
        currentRecordLength: length of current record in the text file
            (i.e. how far to skip to get the subsequent record)
        mailChunk: the current record as a bytes object
        EOF: is TRUE if no index entries remain
        open: everything was properly initialized
    """
    
    # Initialize the object. It represents a database (index+text) for one
    #   JNOS user 'area'
    def __init__(self, areaName, pathName, log):
        self.area = areaName
        self.path = pathName
        self.open = 0
        self.log = log
        # Initial object/file positions (first byte)
        self.currentRecordNumber = 0
        self.textPos  = 0
        self.currentRecordLength = 0
        self.EOF = FALSE
        self.index = None
        self.indexLen = 0
        self.indexPos = 0
        self.indexRecordCount = 0
        self.rdCount = 0
        self.messageIdHeader = 0
        self.rawText = None
        self.textLength = 0
        # Open the index
        self.indexFilename = self.path + self.area + DOT_IND
        self.textFilename  = self.path + self.area + DOT_TXT
        self.log.debug('Index: {}'.format(self.indexFilename))
        self.log.debug('Text: {}'.format(self.textFilename))
        try:
            self.fi = open(self.indexFilename, 'rb')
            self.ft = open(self.textFilename,  'rb')
            try:
                self.textLength = os.path.getsize(self.textFilename)
            except:
                # Notably it fails on Mac OSX
                self.textLength = 0
            self.log.debug("textLength {}".format(self.textLength))
        except PermissionError:
            self.log.critical('Permission error')
            self.open = FALSE
            return
        except FileNotFoundError:
            self.log.warning("File does not exist {} or {}".format(self.indexFilename, self.textFilename))
            # However, .ind file may exist, in which case the area exists, but is empty
            self.usrFilename = self.path + self.area + DOT_USR
            try :
                self.fu = open(self.usrFilename, 'rb')
            except FileNotFoundError:
                self.log.warning("Also, no usr file {}".format(self.usrFilename))
            self.open = TRUE
            return
        except IOError:
            print(sys.exc_info()[2])
            self.log.critical(sys.exc_info()[2])
            self.open = FALSE
            return
        except:
            print("Other error")
            self.log.critical('Other error')
            self.open = FALSE
        # Read the whole index
        # (There could be memory issues here)
        try:
            self.index = self.fi.read()
            self.indexLen = len(self.index)
            log.debug('Index size: {} bytes'.format(self.indexLen))
        except:
            print('Error reading index. Maybe memory exceeded?')
            self.log.critical('Error reading index. Maybe memory exceeded?')
            exit(0)
        # Check version of the index file
        if (self.index[0] != 0x01):
            print('Wrong version number in {}'.format(self.indexFilename))
            self.log.critical('Wrong version number in {}'.format(self.indexFilename))
            exit(0);
        self.indexPos += 1
        # Number of messages present; Number of meassages unread
        self.indexRecordCount = self.readLong()
        self.rdCount = self.readLong()
        # Discard two numbers (don't know what they are)
        self.readLong()
        self.readLong()
        self.open = TRUE
    
    # Is the database (index+text files) open?
    def isOpen(self):
        return self.open
    
    # Close the databse (index+text files)
    def closeAll(self):
        self.fi.close()
        self.ft.close()
        self.open = FALSE
    
    # Report status as a string
    def status(self):
        r = ''
        if (self.path and self.area):
            r += ('{} {}\r\n'.format(self.path, self.area))
        if (self.indexFilename > ''):
            r += ('Index: {}\r\n'.format(self.indexFilename))
        if (self.textFilename > ''):
            r += ('Text: {}\r\n'.format(self.textFilename))
        if (self.indexLen):
            r += ('Index size: {}\r\n'.format(self.indexLen))
        if (self.currentRecordLength):
            r += ('Record length: {}\r\n'.format(self.currentRecordLength))
        if (self.currentRecordNumber):
            r += ('Record number: {}\r\n'.format(self.currentRecordNumber))
        r += 'Msg count: {}\r\n'.format(self.indexRecordCount)
        r += 'Read messages: {}\r\n'.format(self.rdCount)
        return 'OK '+r
    
    # Read a (long) number of 4 bytes from current position in index
    def readLong(self):
        num = self.index[self.indexPos]<<24 | self.index[self.indexPos+1]<<16 | self.index[self.indexPos+2]<<8 | self.index[self.indexPos+3]
        self.indexPos += 4
        return num
    
    # Read a (long) number of 4 bytes, but first byte is the least significant
    def readLongLittleEndian(self):
        num = self.index[self.indexPos] | self.index[self.indexPos+1]<<8 | self.index[self.indexPos+2]<<16 | self.index[self.indexPos+3] <<24
        self.indexPos += 4
        return num
    
    # Read one byte from current position in index
    def readByte(self):
        byt = self.index[self.indexPos]
        self.indexPos += 1
        return byt
    
    # Skip over one or more bytes in the index
    def skipBytes(self, n):
        self.indexPos += n
        return
    
    # Skip over bytes until NN 00 00 50 is reached (next index record)
    def skipBytesToNextRecord(self, n=7):
        # Peel off (discard) bytes until 0xNN000050
        #   is discovered. This is the next-record marker.
        try:
            for ib in range(0, n):
                num = self.index[self.indexPos]<<24 | self.index[self.indexPos+1]<<16 | self.index[self.indexPos+2]<<8 | self.index[self.indexPos+3]
                if ((num & 0x00FFFFFF) == 0x00000050):
                    return
                else:
                    self.indexPos += 1
        except IndexError:
            return
        return
        
    # Read a (time_t) system time (4 bytes) -- actually same as read a little-endian
    def readTime(self):
        time_t = self.index[self.indexPos] | self.index[self.indexPos+1]<<8 | self.index[self.indexPos+2]<<16 | self.index[self.indexPos+3] <<24
        self.indexPos += 4
        return time_t
    
    # Read a string (until a zero-byte, then skip the zero-byte) from the index
    def readString(self):
        s = bytearray(b'')
        # String continues to a zero-byte
        while (self.index[self.indexPos] > 0x00):
            # s.append(self.index[self.indexPos])
            s.append(self.index[self.indexPos])
            self.indexPos += 1
        # Then skip the zero-byte
        self.indexPos += 1
        return str(s.decode('utf-8'))
    
    # Envelope-To:
    def envelopeTo(self):
        return self.toHeader
    
    # Read next index entry, and also add the raw message text, into this object
    def nextMessage(self):
        if (self.indexRecordCount):
            self.log.debug("{} {} {}".format(self.indexPos, self.indexLen, self.EOF))
            # Read next index record and the corresponding email message
            msgType = self.readLong()
            self.log.debug('Msg type: 0x{:02x}'.format(msgType))
            msgStatus = self.readByte()
            self.log.debug('Status: 0x{:02x}'.format(msgStatus))
            self.currentRecordLength = self.readLongLittleEndian()
            self.log.debug('Length/offset: {}'.format(self.currentRecordLength))
            self.toHeader = self.readString()
            self.log.debug('To: {}'.format(self.toHeader))
            self.fromHeader = self.readString()
            self.log.debug('From: {}'.format(self.fromHeader))
            self.subjectHeader = self.readString()
            self.log.debug('Subject: {}'.format(self.subjectHeader))
            self.replyToHeader = '"{}" <{}>'.format(self.readString(), replyTo)
            self.log.debug('Reply-To: {}'.format(self.replyToHeader))
            self.messageIdHeader = self.readString()
            self.log.debug('Message-Id: {}'.format(self.messageIdHeader))
            # Discard two Dates
            self.readTime()
            self.readTime()
            self.ccList = self.readString()
            self.bbsList = self.readString()
            # 5 more bytes after this EXCEPT the very last record of the index
            self.skipBytesToNextRecord(7)
            # At this point the index position should be set for the next
            #   index entry.
            try:
                #DEBUG print('Record {} reading {} bytes'.format(self.currentRecordNumber, self.currentRecordLength))
                # Read the next actual email block
                self.rawMessage = self.ft.read(self.currentRecordLength)
                self.textPos += self.currentRecordLength
                self.currentRecordNumber += 1
                # print('--------\r\n'+str(self.rawMessage)+'\r\n--------\r\n')
            except IOError:
                print(sys.exc_info()[2])
                self.log.critical(sys.exc_info()[2])
                return FALSE
        else:
            # No records
            return FALSE
        return TRUE
    def getRecordCount(self):
        return self.indexRecordCount
    def getReadRecordCount(self):
        return self.rdCount
    def getTextLength(self):
        return self.textLength
    def getMessageId(self):
        return self.messageIdHeader
    def getRawMessage(self):
        return self.rawMessage
            
# One JNOS message object
# This is not an official JNOS thing, just holds only what I need
#   in order to process POP3 requests.
class JNOSmessage(object):
    def __init__(self, i, rawMessage, messageLength, messageId):
        self.i = i
        self.rawMessage = rawMessage
        self.messageLength = messageLength
        self.messageId = messageId
    def getI(self):
        return self.i
    def getRawMessage(self):
        return self.rawMessage
    def getMessageLength(self):
        return self.messageLength
    def getMessageId(self):
        return self.messageId
            
