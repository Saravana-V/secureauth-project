from flask import Flask
from database.db import mongo, init_db

app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb://localhost:27017/cyper'
init_db(app)

print('mongo object:', mongo)

with app.app_context():
    print('mongo.db inside context:', mongo.db)
    try:
        print('collections:', mongo.db.list_collection_names())
    except Exception as e:
        print('error listing collections', e)
