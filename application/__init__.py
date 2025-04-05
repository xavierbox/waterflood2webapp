
import os
from flask import (Flask, redirect, render_template, request,
                   send_from_directory, url_for)

from flask_cors import CORS

 


app_var = Flask(__name__)
CORS(app_var)  #
#from application import routes