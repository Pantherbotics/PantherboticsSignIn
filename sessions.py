# PantherboticsSignIn
#   Tracks sign-in / sign-out of club members at the NPHS Robotics Club
#   sessions.py: Keeps track of login / logout sessions over time
# Originally written by Roger Fachini

import logging, datetime, pprint, time

#--------Configuration--------
# If > 1, sign-in / sign-out times will be rounded to this increment in minutes
TIME_INCREMENTS = datetime.timedelta(minutes=5)

# Time to begin accepting new sign-ins
SESSION_START_TIME = datetime.time(hour=11, minute=30, second=0)

SESSION_END_TIME = datetime.time(hour=17, minute=0, second=0)

#--------Database Selection--------
from database_json import Database


class SessionTracker:
    STATE = {}
    def __init__(self):
        self.logger = logging.getLogger('session')
        self.db = Database()
        

    def studentScanEvent(self, studentID, eventTime = None):
        #process student login / logout. returns false if student is not in existing database
        studentPresent = self.db.isStudentInDatabase(studentID)
        if not studentPresent: return studentPresent

        if eventTime == None:  eventTime = datetime.datetime.now()
        reTime = self.roundTime(eventTime, TIME_INCREMENTS) 

        if not studentID in self.STATE.keys():
            self.rescanStudents()

        if studentID in self.STATE.keys():
            currentState = self.STATE[studentID]['state']
            currentTime = self.STATE[studentID]['timestamp']
            newState = not currentState
            self.db.appendEventLog(studentID, eventTime, eventStatus = newState)
            self.STATE[studentID].update({'timestamp': eventTime, 
                                          'state': newState})
            if newState:
                self.logger.info('Student %s signed in at %s', studentID, eventTime.isoformat())
            else:
                self.logger.info('Student %s signed out at %s', studentID, eventTime.isoformat())

        #pprint.pprint(self.STATE)        
        return studentPresent

    def roundTime(self, dt=None, dateDelta=datetime.timedelta(minutes=1)):
        roundTo = dateDelta.total_seconds()

        if dt == None : dt = datetime.datetime.now()
        seconds = (dt - dt.min).seconds
        # // is a floor division, not a comment on following line:
        rounding = (seconds+roundTo/2) // roundTo * roundTo
        return dt + datetime.timedelta(0,rounding-seconds,-dt.microsecond)

    def rescanStudents(self):
        for studentID in self.db.listStudents():
            data = {int(studentID):{'state': False,
                               'timestamp': None}}
            self.STATE.update(data)

def consoleTrack():
    s = SessionTracker()
    while True:
        a = input('#>')
        a = int(a)
        suc = s.studentScanEvent(a)
        if not suc:
            name = raw_input("ID not in database; enter student name: ")
            s.db.createStudent(a, name)
            s.studentScanEvent(a)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    consoleTrack()

    s = SessionTracker()
    print s.studentScanEvent(123456)
    time.sleep(1)
    print s.studentScanEvent(123456)