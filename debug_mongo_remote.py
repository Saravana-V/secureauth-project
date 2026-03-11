from flask import Flask
from database.db import mongo, init_db

app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb+srv://secureauth:strongpassword@cluster0.cg6dv.mongodb.net/?appName=Cluster0'
app.config['MONGO_DBNAME'] = 'cyper'
init_db(app)

print('mongo object', mongo)
with app.app_context():
    print('mongo.cx', mongo.cx)
    print('mongo.db', mongo.db)
    print('type mongo.db', type(mongo.db))
