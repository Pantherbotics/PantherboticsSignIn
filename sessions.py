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
        studentPresent = self.db.isStudentInDatabase(studentID)
        if not studentPresent: return studentPresent

        if eventTime == None:  eventTime = datetime.datetime.now()
        reTime = self.roundTime(eventTime, TIME_INCREMENTS) 

        if not studentID in self.STATE.keys():
            self.rescanStudents()

        if studentID in self.STATE.keys():
            currentTime = self.STATE[studentID]['timestamp']
            if currentTime == None: currentTime = datetime.datetime.fromtimestamp(0)
            if self.roundTime(currentTime, TIME_INCREMENTS) == reTime:
                self.logger.debug('Duplicate scan ignored %s %s %s', studentID, currentTime.isoformat(), eventTime.isoformat())
                return studentPresent

        if studentID in self.STATE.keys():      
            currentState = self.STATE[studentID]['state']  
            newState = not currentState    
            self.db.appendEventLog(studentID, eventTime)
            self.STATE[studentID].update({'timestamp': eventTime, 
                                          'state': newState})
            self.logger.info('Scan event %s %s', studentID, eventTime.isoformat())
            self.generateSessions()


        #pprint.pprint(self.STATE)        
        return studentPresent

    def roundTime(self, dt=None, dateDelta=datetime.timedelta(minutes=1)):
        roundTo = dateDelta.total_seconds()

        if dt == None : dt = datetime.datetime.now()
        seconds = (dt - dt.min).seconds
        # // is a floor division, not a comment on following line:
        rounding = (seconds+roundTo/2) // roundTo * roundTo
        return dt + datetime.timedelta(0,rounding-seconds,-dt.microsecond)

    def dateFromISO(self, datestr):
        return datetime.datetime.strptime( datestr, "%Y-%m-%dT%H:%M:%S.%f" )

    def rescanStudents(self):
        for studentID in self.db.listStudents():
            log = self.db.getEventsFor(studentID)
            if len(log) == 0:
                tStamp = None
            else:
                tStamp = log[-1]['timestamp']

            data = {int(studentID):{'state': False,
                                    'timestamp': tStamp}}
            self.STATE.update(data)
    
    def isStudentSignedIn(self, studentID, dateRefrence=None, length=False):
        if dateRefrence == None: dateRefrence = datetime.datetime.now()
        log = self.db.getEventsFor(studentID)
        if len(log) == 0: return False
        if len(log) % 2 == 0: return False
        for event in log:
            eventLength = dateRefrence - event['timestamp']
            if eventLength.total_seconds() > 24*60*60:       #Do not process events > 24h old
                continue
            else:
                if length: return (True, eventLength)
                else: return True

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


    def isCurrentTimeInSession(self):
        now = datetime.datetime.now()
        return now.hour >= SESSION_START_HOUR and now.hour <= SESSION_END_HOUR


def consoleTrack():
    s = SessionTracker()
    while True:
        st = s.db.listStudents()
        for i in st:
            da = s.isStudentSignedIn(i, length=True)
            if  da == False:
                print "%-8s %-20s Absent" % (i, s.db.STUDENTS[i]['name'])
            else:
                print "%-8s %-20s %s" % (i, s.db.STUDENTS[i]['name'], da[1])
        try:
            a = raw_input('#>')
            a = int(a)
        except KeyboardInterrupt:
            exit(0)
        except ValueError:
            print "Error: Invalid Input (cannot convert to int)"
            continue
        
        suc = s.studentScanEvent(a)
        if not suc:
            name = raw_input("ID not in database; enter student name: ")
            s.db.createStudent(a, name)
            s.studentScanEvent(a)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    print '  Pantherbotics Electronic Sign-in Sheet'
    consoleTrack()