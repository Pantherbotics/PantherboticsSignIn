# PantherboticsSignIn
#   Tracks sign-in / sign-out of club members at the NPHS Robotics Club
#   server.py: Serves the webpage and takes input from students
# Originally written by Roger Fachini

#--------Imports--------
import datetime, logging, pprint, os, time, locale, json, cgi, random
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from mimetypes import MimeTypes

from sessions import SessionTracker
#----------------------------------------

WEB_DIR = 'web/'

SessionInstance = None

class CustomHTTPRequestHandler(BaseHTTPRequestHandler):
    mimeOBJ = MimeTypes()
    logger = logging.getLogger('http')

    def send_standard_response(self, status, content_type):
        self.send_response(status)
        self.send_header('Content-type',content_type)
        self.end_headers()

    def log_message(self, format, *args):
        msg = format % args
        self.logger.debug("[%s] %s",self.address_string(), msg)

    def do_GET(self):
        if SessionInstance == None: 
            self.send_error(500, "Session Instance is not Initalized!")
            return
        try:
            if self.path[-1] == '/' and not os.path.isfile(WEB_DIR + self.path):
                self.path += 'index.html'
            if '/api/barcode?id=' in self.path: 
                try:
                    studentID = cgi.parse_qs(self.path.split('?')[1])['id']
                    inDB = SessionInstance.studentScanEvent(int(studentID[0]))
                    self.send_standard_response(200, 'text/plain')
                except KeyError as er:
                    logging.exception(er)
                    inDB = False
                    studentID = None
                    self.send_standard_response(500, 'text/plain')
                self.wfile.write(json.dumps({'id': studentID, 'inDatabase': inDB}))

            elif '/api/newstudent?' in self.path: 
                try:
                    c = cgi.parse_qs(self.path.split('?')[1])
                    name = c['name'][0]
                    id = c['id'][0]
                    SessionInstance.db.createStudent(id, name)
                    self.send_standard_response(200, 'text/plain')
                    self.wfile.write('OK')
                except KeyError:
                    self.send_standard_response(500, 'text/plain')
                    self.wfile.write('ERR')

            elif '/api/getinfo?id=' in self.path: 
                try:
                    studentID = cgi.parse_qs(self.path.split('?')[1])['id']
                    studentID = int(studentID[0])

                    name = SessionInstance.db.getNameFor(studentID)
                    lastSession = SessionInstance.db.getLatestSessionFor(studentID)
                    if lastSession and 'start_time' in lastSession.keys():
                        lastSession['start_time'] = lastSession['start_time'].isoformat()
                    if lastSession and 'end_time' in lastSession.keys():
                        lastSession['end_time'] = lastSession['end_time'].isoformat()
                    
                    state = SessionInstance.getCurrentState(studentID)
                    if state and 'timestamp' in state.keys() and not type(state['timestamp']) == str and not state['timestamp'] == None:
                        state['timestamp'] = state['timestamp'].isoformat()
                    data = {'name': name, 'id': studentID, 'lastSession': lastSession, 'state': state}
                    self.send_standard_response(200, 'text/plain')
                    self.wfile.write(json.dumps(data, indent=4))
                except KeyError as er:
                    logging.exception(er)
                    self.send_standard_response(500, 'text/plain')
                    self.wfile.write("ERROR")

            elif '/api/liststudents' in self.path: 
                    students = SessionInstance.db.listStudents()
                    self.send_standard_response(200, 'text/plain')
                    self.wfile.write(json.dumps(students, indent=4))
                
            else:
                self.path = self.path.split('?')[0]
                f = open(WEB_DIR + self.path) #open requested file
                mime = self.mimeOBJ.guess_type(self.path)
                self.send_standard_response(200, mime[0])
                self.wfile.write(f.read())
                f.close()
        except IOError:
            self.send_error(404, 'file not found: %s'%self.path)
#END OF CLASS CustomHTTPRequestHandler()

class StatusWebServer:
    def __init__(self):
        self.logger = logging.getLogger('http')
        addr = ('', 8080)
        httpd = HTTPServer(addr, CustomHTTPRequestHandler)
        self.logger.info('Serving HTTP requests on %s:%s',addr[0],addr[1])
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print " <--- Escape character entered, exiting..."
            pass
#END OF CLASS StatusWebServer()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    SessionInstance = SessionTracker()
    StatusWebServer()