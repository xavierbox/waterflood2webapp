
import os
from flask import (Flask, redirect, render_template, request,
                   send_from_directory, url_for)

app_var = Flask(__name__)

#from application import routes