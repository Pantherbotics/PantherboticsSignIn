# PantherboticsSignIn
#   Tracks sign-in / sign-out of club members at the NPHS Robotics Club
#   server.py: Serves the webpage and takes input from students
# Originally written by Roger Fachini

#--------Imports--------
import datetime, logging, pprint, os, time, locale, json, cgi, random
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from mimetypes import MimeTypes


#----------------------------------------

class CustomHTTPRequestHandler(BaseHTTPRequestHandler):
    mimeOBJ = MimeTypes()
    def do_GET(self):
        try:
            if '/api/barcode?id=' in self.path: :
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                studentID = int(self.path.split('?id=')[1])

            else:
                self.path = self.path.split('?')[0]
                f = open(WEB_DIR + self.path) #open requested file
                mime = self.mimeOBJ.guess_type(self.path)
                self.send_response(200)
                self.send_header('Content-type',mime[0])
                self.end_headers()
                self.wfile.write(f.read())
                f.close()
                
                return
        except IOError:
            self.send_error(404, 'file not found: %s'%self.path)

class StatusWebServer:
    def __init__(self):
        self.logger = logging.getLogger('http')
        addr = ('', 8080)
        httpd = HTTPServer(addr, CustomHTTPRequestHandler)
        self.logger.debug('Serving HTTP requests on %s:%s',addr[0],addr[1])
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print " <--- Escape character entered, exiting..."
            pass

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    StatusWebServer()
