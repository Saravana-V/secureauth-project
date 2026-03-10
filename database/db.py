from flask_pymongo import PyMongo
from pymongo import MongoClient

# Flask-PyMongo instance (used in app.py)
mongo = PyMongo()

# For direct pymongo access like users_collection
client = MongoClient('mongodb://localhost:27017/')
db = client['cyper']  # ✅ Make sure this matches your MongoDB DB name
users_collection = db['secureauth']  # ✅ Your user OTP collection
