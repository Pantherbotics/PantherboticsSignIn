# PantherboticsSignIn
#   Tracks sign-in / sign-out of club members at the NPHS Robotics Club
#   database-json.py: Stores log-in data as JSON files
# Originally written by Roger Fachini

import os, json, logging, time,  datetime, pprint, uuid
DATA_DIR = "data/"
STUDENT_DIR = DATA_DIR + "students/"
EVENT_DIR = DATA_DIR + "eventlog/"
SESSION_DIR = DATA_DIR + "sessions/"

class Database:
    EVENTS = []
    STUDENTS = {}
    SESSIONS = []
    def __init__(self):
        self.logger = logging.getLogger('db-json')
        self._initDir(DATA_DIR)
        self._initDir(STUDENT_DIR)
        self._initDir(EVENT_DIR)
        self._initDir(SESSION_DIR)
        self.loadAllStudents()
        self.loadEventLog()
        self.loadSessions()

    def listStudents(self):
        return [int(str(x).split('.')[0]) for x in os.listdir(STUDENT_DIR) if '.json' in x]

    def isStudentInDatabase(self, studentID):
        return os.path.isfile("%s%s.json"%(STUDENT_DIR, studentID))
    
    def createStudent(self, studentID, studentName):
        stPath = "%s%s.json"%(STUDENT_DIR, studentID)
        student =  {'id': studentID,
                    'name': studentName}
        self.STUDENTS.update({studentID:student})
        self._initJSON(stPath, data=student)

    def appendEventLog(self, studentID, eventTime, eventStatus = None):
        eventFile = eventTime.strftime("%Y-%m-%d-eventlog.json")
        eventPath = EVENT_DIR + eventFile
        self._initJSON(eventPath, data = [])
        uid = str(uuid.uuid4())
        event = {'id': studentID, 
                 'timestamp': eventTime,
                 'uuid': uid}
        if not eventStatus == None:
            event.update({'status':eventStatus})
        
        self.EVENTS.append(event.copy())
        event.update({'timestamp': event['timestamp'].isoformat()})

        with open(eventPath, 'r') as fHandle:
            data = json.load(fHandle)
            fHandle.close()
        data.append(event)
        with open(eventPath, 'w') as fHandle:
            json.dump(data, fHandle, indent=4)
            fHandle.close()

    def getEventsFor(self, studentID):
        return [e for e in self.EVENTS if e['id'] == studentID]

    def loadEventLog(self, dayOffset=2):
        files = os.listdir(EVENT_DIR)
        for f in files[-dayOffset:]:
            with open(EVENT_DIR + f, 'r') as fHandle:
                data = json.load(fHandle)
                for event in data:
                    if 'timestamp' in event.keys():
                        event['timestamp'] = datetime.datetime.strptime(event['timestamp'], "%Y-%m-%dT%H:%M:%S.%f")
                    self.EVENTS.append(event)

    def loadSessions(self):
        files = os.listdir(SESSION_DIR)
        for f in files:
            with open(SESSION_DIR + f, 'r') as fHandle:
                data = json.load(fHandle)
                for session in data:
                    if 'start_time' in session.keys():
                        session['start_time'] = datetime.datetime.strptime(session['start_time'], "%Y-%m-%dT%H:%M:%S.%f")
                    if 'end_time' in session.keys():
                        session['end_time'] = datetime.datetime.strptime(session['end_time'], "%Y-%m-%dT%H:%M:%S.%f")
                    self.SESSIONS.append(session)

    def loadAllStudents(self):
        for s in self.listStudents():
            fName = "%s%s.json"%(STUDENT_DIR, s)
            with open(fName, 'r') as fHandle:
                r = json.load(fHandle)
                self.STUDENTS.update({s:r})

    def _initDir(self, path):
        if not os.path.exists(path):
            os.makedirs(path)
            self.logger.info('Folder %s created', path)

    def _initJSON(self, path, data={}):
        if not os.path.isfile(path):
            self.logger.debug('Path %s does not exist, creating', path)
            with open(path, 'w') as fHandle:
                json.dump(data, fHandle, indent=4)
                fHandle.close()

    def createSession(self, studentID, startTime, endTime, status, startUUID, endUUID):
        session = {'id': studentID,
                   'start_time': startTime,
                   'end_time': endTime,
                   'duration': (endTime - startTime).total_seconds(),
                   'status': status,
                   'start_uuid': startUUID,
                   'end_uuid': endUUID}
        sessionFile = startTime.strftime(SESSION_DIR + "%Y-%m-%d-sessions.json")
        self._initJSON(sessionFile, data = [])

        self.SESSIONS.append(session.copy())
        session.update({'start_time': session['start_time'].isoformat()})
        session.update({'end_time': session['end_time'].isoformat()})

        with open(sessionFile, 'r') as fHandle:
            data = json.load(fHandle)
            fHandle.close()
        data.append(session)
        with open(sessionFile, 'w') as fHandle:
            json.dump(data, fHandle, indent=4)
            fHandle.close()

if __name__ == '__main__':
     d = Database()
     #pprint.pprint(d.STUDENTS)
     #pprint.pprint(d.EVENTS)

     #print d.getEventsFor(128872)
     #start = datetime.datetime.now()
     #time.sleep(2)
     #end = datetime.datetime.now()
     #d.createSession(123456, start, end, 'checkout', 'a', 'b')
     #pprint.pprint(d.SESSIONS)