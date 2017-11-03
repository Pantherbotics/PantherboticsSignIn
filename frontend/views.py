from flask import render_template, send_from_directory
from flask import request
from frontend import frontend
from mimetypes import MimeTypes

from sessions import SessionTracker

@frontend.route('/')
@frontend.route('/index')
def index():

    s = SessionTracker()
    students = s.db.listStudents()
    sessions = [s.db.getLatestSessionFor(si) for si in students]
    names = {si:s.db.getNameFor(si) for si in students}

    return render_template('index.html',
                           title="Home",
                           students=students,
                           sessions=sessions,
                           names=names)

