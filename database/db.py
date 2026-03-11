from flask_pymongo import PyMongo

mongo = PyMongo()


def init_db(app):
    """Initialize the PyMongo extension with the Flask app.

    After calling this in your application setup, you can safely use
    `mongo.db` inside request handlers and other application code.

    Flask-PyMongo will set ``mongo.db`` after it creates the client.  If the
    URI does not include a default database name (e.g. the cluster string
    used in `.env`), ``mongo.db`` may remain ``None``.  In that case we read
    ``MONGO_DBNAME`` from the config and manually attach the database from the
    underlying client.
    """
    mongo.init_app(app)
    # ensure default database exists when URI lacks explicit path
    if mongo.db is None:
        dbname = app.config.get("MONGO_DBNAME")
        if dbname:
            # attribute assignment is safe; ``mongo.db`` is a simple variable
            mongo.db = mongo.cx[dbname]
        else:
            # leaving db as None is acceptable; caller will handle errors
            pass

