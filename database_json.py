# PantherboticsSignIn
#   Tracks sign-in / sign-out of club members at the NPHS Robotics Club
#   database-json.py: Stores log-in data as JSON files
# Originally written by Roger Fachini

import os, json, logging, datetime, pprint
DATA_DIR = "data/"
STUDENT_DIR = DATA_DIR + "students/"
EVENT_DIR = DATA_DIR + "eventlog/"

class Database:
    EVENTS = []
    STUDENTS = {}
    def __init__(self):
        self.logger = logging.getLogger('db-json')
        self._initDir(DATA_DIR)
        self._initDir(STUDENT_DIR)
        self._initDir(EVENT_DIR)
        self.loadAllStudents()
        self.loadEventLog()

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

        event = {'id': studentID, 
                 'timestamp': eventTime.isoformat()}
        if not eventStatus == None:
            event.update({'status':eventStatus})

        self.EVENTS.append(event)

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

if __name__ == '__main__':
     d = Database()
     pprint.pprint(d.STUDENTS)
     pprint.pprint(d.EVENTS)

     print d.getEventsFor(128872)