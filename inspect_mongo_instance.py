from flask import Flask
from database.db import mongo, init_db

app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb+srv://secureauth:strongpassword@cluster0.cg6dv.mongodb.net/?appName=Cluster0'
app.config['MONGO_DBNAME'] = 'cyper'
init_db(app)

print('mongo instance dict keys:', list(mongo.__dict__.keys()))
print('mongo instance dict:', mongo.__dict__)

with app.app_context():
    print('mongo.db inside context', mongo.db)
    print('type of mongo.db', type(mongo.db))
    try:
        print('mongo._db attr', getattr(mongo, '_db', None))
    except Exception as e:
        print('error reading _db', e)
