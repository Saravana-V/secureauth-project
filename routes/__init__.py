
from .auth_routes import auth_bp
from .shop_routes import shop_bp

def init_routes(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(shop_bp)
