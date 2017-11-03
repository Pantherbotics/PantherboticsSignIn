# PantherboticsSignIn
#   Tracks sign-in / sign-out of club members at the NPHS Robotics Club
#   sessions.py: Keeps track of login / logout sessions over time
# Originally written by Roger Fachini

import logging, datetime, pprint, time, threading

#--------Configuration--------
# If > 1, sign-in / sign-out times will be rounded to this increment in minutes
TIME_INCREMENTS = datetime.timedelta(minutes=5)

#If a session is longer than this time, it is assumed that the person forgot to sign out
MAX_HRS = 16
MAX_MIN = 0
MAX_SEC = 0
MAX_SESSION_LENGTH = ((MAX_HRS*60) + MAX_MIN)*60 + MAX_SEC #S57600 seconds = 16hrs

#If a session length ends up exceeding MAX_SESSION_LENGTH, their session will be closed at this time (hour)
DEF_SESSION_END_HRS = 17
DEF_SESSION_END_MIN = 0
DEF_SESSION_END_SEC = 0

#--------Database Selection--------
from database_json import Database


class SessionTracker:
    STATE = {}     #Stores current state of all signed-in students. 
    def __init__(self):
        self.logger = logging.getLogger('session')
        self.db = Database()      
        self.generateSessions()  #Run through last session logs and generate state information
        self.eventThread = threading.Thread(target=self.eventLoop, args=(()))
        self.eventThread.daemon = True
        self.eventThread.start()
        
    def studentScanEvent(self, studentID, eventTime = None):
        #process student login / logout. returns false if student is not in existing database
        priorStudent = self.db.isStudentInDatabase(studentID) #the name "studentPresent" implies "is the student present at the club?" not "is the student included in the database?" changed name to "priorStudent" for clarity
        if not priorStudent: return False #Exit?

        if eventTime == None:  eventTime = datetime.datetime.now()
        reTime = self.roundTime(eventTime, TIME_INCREMENTS) 

        if not studentID in self.STATE.keys():
            self.rescanStudents()

        if studentID in self.STATE.keys():      
            self.db.appendEventLog(studentID, eventTime)
            self.logger.debug('Scan event %s %s', studentID, eventTime.isoformat())
            self.generateSessions()

        return True


    def roundTime(self, dt=None, dateDelta=datetime.timedelta(minutes=1)):
        #Rounds a datetime.datetime object to a datetime.timedelta object
        roundTo = dateDelta.total_seconds()

        if dt == None : dt = datetime.datetime.now()
        seconds = (dt - dt.min).seconds
        # // is a floor division, not a comment on following line:
        rounding = (seconds+roundTo/2) // roundTo * roundTo
        return dt + datetime.timedelta(0,rounding-seconds,-dt.microsecond)


    def dateFromISO(self, datestr):
        #parses a string for an ISO8601 date. returns a datetime object
        return datetime.datetime.strptime( datestr, "%Y-%m-%dT%H:%M:%S.%f" )


    def getCurrentState(self, studentID):
        #gets the current state of a student ('signin' | 'signout' | 'timeout')
        if not studentID in self.STATE.keys(): return None
        else: return self.STATE[studentID]


    def rescanStudents(self):
        #Generates the state of students for the first time
        for studentID in self.db.listStudents(): 
            if studentID in self.STATE.keys(): continue    # Ignore students that already have a state
            log = self.db.getEventsFor(studentID)          # Get the last few scan events for this student
            sess =self.db.getLatestSessionFor(studentID)   # Get the latest Sesssion for this student

            if len(log) == 0:                              #Set STATE timestamp to latest scan event, if any
                tStamp = None
            else:
                tStamp = log[-1]['timestamp']

            if sess == None:                               #Set STATE status to latest session status (scanout | timeout), if any
                status = None
            else:
                status = sess['status']
            
            data = {int(studentID):{'status': status,      #Write the new state to self.STATE
                                    'timestamp': tStamp}}
            self.STATE.update(data)


    def generateSessions(self):
        #Iterates through scan events, and generates Sessions from patterns in the scan events
        STATE = {}  #NOTE: This is different from self.STATE!
        uuidGroups = [[s['start_uuid'], s['end_uuid']] for s in self.db.SESSIONS]  # Iterate through existing Sessions, and gather all UUIDs
        parsedUUIDs =  [uuid for sublist in uuidGroups for uuid in sublist]        # of already existing Sessions 
        
        for event in self.db.EVENTS:
            eventUUID = event['uuid']                  
            if eventUUID in parsedUUIDs: continue    #Do not process any events that have already been processed
                                                     # (UUID exists in another event)
            registerTimeout = False      
            stID = event['id']                             #Get studentID and timestamp of event
            timestamp = event['timestamp']
            sessionLength = 0
            if stID in STATE.keys():                       #Student has already been processed (at least second time), we can use previous data
                sessStatus = STATE[stID]['status'] 
                sessUUID = STATE[stID]['uuid']             #get status, UUID, and timestamp of previous event
                sessTimestamp = STATE[stID]['timestamp']
                sessionLength = timestamp - sessTimestamp  #Get difference between timestamps (length of session if signout)

                #NOTE: A Timeout Session is generated Before a scanin event (two generated in one loop)
                #Student was previously scanned in and session is longer than acceptable: TIMEOUT
                if sessStatus == 'scanin' and sessionLength.total_seconds() >= MAX_SESSION_LENGTH: 
                    #TODO: Calculate timestamp of timeout session end in a better fashion. 
                    backtimestamp = sessTimestamp.replace(hour=DEF_SESSION_END_HRS,   
                                                          minute=DEF_SESSION_END_MIN, 
                                                          second=DEF_SESSION_END_SEC)
                    registerTimeout = True                                                                 #event is a timeout (just used for debug purpouses)
                    self.db.createSession(stID, sessTimestamp, backtimestamp, 'timeout', sessUUID, None)   #Create a new Session on timeout
                    STATE.update({stID:{'status': 'timeout', 'timestamp': backtimestamp}})                 #Update state with timeout info

                #Student was previously scanned in and session is within acceptable size: SCANOUT
                if sessStatus == 'scanin' and sessionLength.total_seconds() <= MAX_SESSION_LENGTH:
                    self.db.createSession(stID, sessTimestamp, timestamp, 'scanout', sessUUID, eventUUID)  #Create a new Session on scanout
                    newStatus = 'scanout'

                #Student was previously scanned out: SCANIN
                elif sessStatus == 'scanout' or sessStatus == 'timeout':
                    newStatus = 'scanin'
            
            else:
                newStatus = 'scanin'
                sessionLength = 0

            logDebug = not (stID in self.STATE.keys() and self.STATE[stID]['status'] == newStatus) #Events are registered but not printed to console (prevents console spam)

            if registerTimeout:
                self.logger.info('Student %-18s (%s) Forgot to sign out. length: %s', self.db.STUDENTS[stID]['name'], stID, backtimestamp - sessTimestamp)

            if newStatus == 'scanin' and logDebug: 
                self.logger.info('Student %-18s (%s) Scanned In  at %s length: %s', self.db.STUDENTS[stID]['name'], stID, timestamp.isoformat(), sessionLength)
            elif newStatus == 'scanout' and logDebug: 
                self.logger.info('Student %-18s (%s) Scanned Out at %s length: %s', self.db.STUDENTS[stID]['name'], stID, timestamp.isoformat(), sessionLength)
                

            STATE.update() #Update state with status and timestamp

        #Update self.STATE information from newly generate STATE info
        self.rescanStudents()  
        for sID, data in STATE.iteritems():
            if data['status'] == 'scanin':
                sessTimestamp = data['timestamp']
                sessionLength = datetime.datetime.now() - sessTimestamp
                if sessionLength.total_seconds() >= MAX_SESSION_LENGTH: 
                    backtimestamp = sessTimestamp.replace(hour=DEF_SESSION_END_HRS, minute=DEF_SESSION_END_MIN, second=DEF_SESSION_END_SEC)
                    self.db.createSession(sID, sessTimestamp, backtimestamp, 'timeout', data['uuid'], None)
                    STATE.update({stID:{'status': 'timeout', 'timestamp': backtimestamp}})
                    self.logger.debug('Student %-18s (%s) Forgot to sign out. length: %s', self.db.STUDENTS[sID]['name'], sID, backtimestamp - sessTimestamp)

            if sID in self.STATE.keys():
                self.STATE[sID].update({'status':data['status'], 'timestamp': data['timestamp']})


    def eventLoop(self):
        while True:
            time.sleep(60*5)
            self.generateSessions()

    def _setEventOfType(self, type, studentID, timestamp, uuid, debug=True):
        if type == 'scanin':
            self.logger.info('Student %-18s (%s) Forgot to sign out.', self.db.STUDENTS[studentID]['name'], studentID)

        elif type == 'scanin': 
            self.logger.info('Student %-18s (%s) Scanned In  at %s', self.db.STUDENTS[studentID]['name'], studentID, timestamp.isoformat())

        elif type == 'scanout': 
            self.logger.info('Student %-18s (%s) Scanned Out at %s', self.db.STUDENTS[studentID]['name'], studentID, timestamp.isoformat())
        OUT = {studentID:{'status': type, 'timestamp': timestamp, 'uuid': eventUUID}}
=
#END OF CLASS SessionTracker()

def consoleTrack():
    s = SessionTracker()
    error = False
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