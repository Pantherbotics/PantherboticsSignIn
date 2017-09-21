# PantherboticsSignIn
#   Tracks sign-in / sign-out of club members at the NPHS Robotics Club
#   sessions.py: Keeps track of login / logout sessions over time
# Originally written by Roger Fachini

import logging, datetime, pprint, time

#--------Configuration--------
# If > 1, sign-in / sign-out times will be rounded to this increment in minutes
TIME_INCREMENTS = datetime.timedelta(minutes=5)

#If a session is longer than this time, it is assumed that the person forgot to sign out
MAX_SESSION_LENGTH = 57600

#If a session length ends up exceeding MAX_SESSION_LENGTH, their session will be closed at this tome (hour)
DEF_SESSION_END_HOUR = 17
DEF_SESSION_END_MINUTE = 0
DEF_SESSION_END_SECOND = 0

#--------Database Selection--------
from database_json import Database


class SessionTracker:
    STATE = {}
    SESSIONS = {}
    def __init__(self):
        self.logger = logging.getLogger('session')
        self.db = Database()
        self.generateSessions()
        
        

    def studentScanEvent(self, studentID, eventTime = None):
        #process student login / logout. returns false if student is not in existing database
        priorStudent = self.db.isStudentInDatabase(studentID) #the name "studentPresent" implies "is the student present at the club?" not "is the student included in the database?" changed name to "priorStudent" for clarity
        if not priorStudent: return false #Exit?

        if eventTime == None:  eventTime = datetime.datetime.now()
        reTime = self.roundTime(eventTime, TIME_INCREMENTS) 

        if not studentID in self.STATE.keys():
            self.rescanStudents()

        if studentID in self.STATE.keys():      
            self.db.appendEventLog(studentID, eventTime)
            self.logger.info('Scan event %s %s', studentID, eventTime.isoformat())
            self.generateSessions()

        return true

    def roundTime(self, dt=None, dateDelta=datetime.timedelta(minutes=1)):
        roundTo = dateDelta.total_seconds()

        if dt == None : dt = datetime.datetime.now()
        seconds = (dt - dt.min).seconds
        # // is a floor division, not a comment on following line:
        rounding = (seconds+roundTo/2) // roundTo * roundTo
        return dt + datetime.timedelta(0,rounding-seconds,-dt.microsecond)

    def dateFromISO(self, datestr):
        return datetime.datetime.strptime( datestr, "%Y-%m-%dT%H:%M:%S.%f" )

    def getCurrentState(self, studentID):
        if not studentID in self.STATE.keys(): return None
        else: return self.STATE[studentID]

    def rescanStudents(self):
        for studentID in self.db.listStudents():
            if studentID in self.STATE.keys(): continue
            log = self.db.getEventsFor(studentID)
            sess =self.db.getLatestSessionFor(studentID)
            if len(log) == 0:
                tStamp = None
            else:
                tStamp = log[-1]['timestamp']

            if sess == None:
                status = None
            else:
                status = sess['status']
            
            data = {int(studentID):{'status': status,
                                    'timestamp': tStamp}}
            self.STATE.update(data)


    def generateSessions(self):
        STATE = {}
        uuidGroups = [[s['start_uuid'], s['end_uuid']] for s in self.db.SESSIONS]
        parsedUUIDs =  [uuid for sublist in uuidGroups for uuid in sublist]
        
        for event in self.db.EVENTS:
            eventUUID = event['uuid']
            if eventUUID in parsedUUIDs: continue

            registerTimeout = False
            stID = event['id']
            timestamp = event['timestamp']
            sessionLength = 0
            if stID in STATE.keys():
                sessStatus = STATE[stID]['status']
                sessUUID = STATE[stID]['uuid']
                sessTimestamp = STATE[stID]['timestamp']
                sessionLength = timestamp - sessTimestamp
                if sessStatus == 'scanin' and sessionLength.total_seconds() >= MAX_SESSION_LENGTH:
                    backtimestamp = sessTimestamp.replace(hour=DEF_SESSION_END_HOUR, minute=DEF_SESSION_END_MINUTE, second=DEF_SESSION_END_SECOND)
                    registerTimeout = True
                    self.db.createSession(stID, sessTimestamp, backtimestamp, 'timeout', sessUUID, None)
                    STATE.update({stID:{'status': 'timeout', 'timestamp': backtimestamp}})

                if sessStatus == 'scanin' and sessionLength.total_seconds() <= MAX_SESSION_LENGTH:
                    self.db.createSession(stID, sessTimestamp, timestamp, 'scanout', sessUUID, eventUUID)
                    newStatus = 'scanout'
                elif sessStatus == 'scanout' or sessStatus == 'timeout':
                    newStatus = 'scanin'
            else:
                newStatus = 'scanin'
                sessionLength = 0

            if registerTimeout:
                self.logger.debug('Student %-18s (%s) Forgot to sign out. length: %s', self.db.STUDENTS[stID]['name'], stID, backtimestamp - sessTimestamp)
            if newStatus == 'scanin': 
                self.logger.debug('Student %-18s (%s) Scanned In  at %s length: %s', self.db.STUDENTS[stID]['name'], stID, timestamp.isoformat(), sessionLength)
            elif newStatus == 'scanout': 
                self.logger.debug('Student %-18s (%s) Scanned Out at %s length: %s', self.db.STUDENTS[stID]['name'], stID, timestamp.isoformat(), sessionLength)
                

            STATE.update({stID:{'status': newStatus, 'timestamp': timestamp, 'uuid': eventUUID}})
        self.rescanStudents()
        for sID, data in STATE.iteritems():
            if data['status'] == 'scanin':
                sessTimestamp = data['timestamp']
                sessionLength = datetime.datetime.now() - sessTimestamp
                if sessionLength.total_seconds() >= MAX_SESSION_LENGTH:
                    backtimestamp = sessTimestamp.replace(hour=DEF_SESSION_END_HOUR, minute=DEF_SESSION_END_MINUTE, second=DEF_SESSION_END_SECOND)
                    self.db.createSession(sID, sessTimestamp, backtimestamp, 'timeout', data['uuid'], None)
                    STATE.update({stID:{'status': 'timeout', 'timestamp': backtimestamp}})
                    self.logger.debug('Student %-18s (%s) Forgot to sign out. length: %s', self.db.STUDENTS[sID]['name'], sID, backtimestamp - sessTimestamp)

            if sID in self.STATE.keys():
                self.STATE[sID].update({'status':data['status'], 'timestamp': data['timestamp']})

    def isCurrentTimeInSession(self):
        now = datetime.datetime.now()
        return now.hour >= SESSION_START_HOUR and now.hour <= SESSION_END_HOUR


def consoleTrack():
    s = SessionTracker()
    error = false
    while not error: #this will continue until student scan event fails AFTER adding a new student, which should never happen.
        try:
            inputID = raw_input('#>')
            inputID = int(inputID)
        except KeyboardInterrupt:
            exit(0)
        except ValueError:
            print "Error: Invalid Input (cannot convert to int)"
            continue #This continue statement causes any input prior to the error to be continue, so if you types 401F22, then a = 401
        
        inDatabase = s.studentScanEvent(inputID)
        if not inDatabase:
            name = raw_input("ID not in database; enter student name: ")
            s.db.createStudent(inputID, name)
            error = s.studentScanEvent(inputID)

   	print "Error: studentScanEvent failed with inputID::" + inputID

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    print '  Pantherbotics Electronic Sign-in Sheet'
    consoleTrack()