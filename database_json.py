# PantherboticsSignIn
#   Tracks sign-in / sign-out of club members at the NPHS Robotics Club
#   database-json.py: Stores log-in data as JSON files
# Originally written by Roger Fachini

import os, json, logging, datetime
DATA_DIR = "data/"
STUDENT_DIR = DATA_DIR + "students/"
EVENT_DIR = DATA_DIR + "eventlog/"

class Database:
    def __init__(self):
        self.logger = logging.getLogger('db-json')
        self._initDir(DATA_DIR)
        self._initDir(STUDENT_DIR)
        self._initDir(EVENT_DIR)

    def listStudents(self):
        return [str(x).split('.')[0] for x in os.listdir(STUDENT_DIR) if '.json' in x]

    def isStudentInDatabase(self, studentID):
        return os.path.isfile("%s%s.json"%(STUDENT_DIR, studentID))
    
    def createStudent(self, studentID, studentName):
        stPath = "%s%s.json"%(STUDENT_DIR, studentID)
        self._initJSON(stPath, data = {'id': studentID,
                                       'name': studentName})

    def appendEventLog(self, studentID, eventTime, eventStatus = None):
        eventFile = eventTime.strftime("%Y-%m-%d-eventlog.json")
        eventPath = EVENT_DIR + eventFile
        self._initJSON(eventPath, data = [])

        event = {'id': studentID, 
                 'timestamp': eventTime.isoformat()}
        if not eventStatus == None:
            event.update({'status':eventStatus})

        with open(eventPath, 'r') as fHandle:
            data = json.load(fHandle)
            fHandle.close()
        data.append(event)
        with open(eventPath, 'w') as fHandle:
            json.dump(data, fHandle, indent=4)
            fHandle.close()

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

 