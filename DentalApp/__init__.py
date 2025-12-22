

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

app = Flask(__name__)
#csdl
from urllib.parse import quote_plus


password = quote_plus("Trang@0k2005")

app.config["SQLALCHEMY_DATABASE_URI"] =f"mysql+pymysql://root:{password}@localhost/dentaldb"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
db = SQLAlchemy(app)
#các slot giờ
STANDARD_SLOTS = ["07:00", "08:00", "09:00", "10:00","13:00", "14:00", "15:00", "16:00"]

#login
app.secret_key = 'f3400ddaead121d6ce559d5c73fd05b1'
login = LoginManager(app)

#VAT
VAT = 0.1

