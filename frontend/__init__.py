from flask import Flask

frontend = Flask(__name__)
from frontend import views
