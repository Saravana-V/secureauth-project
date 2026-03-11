from flask_pymongo import PyMongo
import inspect

print('db attr', PyMongo.db)
print('db doc', inspect.getdoc(PyMongo.db))
print('dir includes db', [k for k in dir(PyMongo) if 'db' in k])
