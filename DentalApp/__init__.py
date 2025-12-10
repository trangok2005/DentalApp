

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
from urllib.parse import quote_plus

password = quote_plus("Trang@0k2005")

app.config["SQLALCHEMY_DATABASE_URI"] =f"mysql+pymysql://root:{password}@localhost/dentaldb"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True

db = SQLAlchemy(app)
