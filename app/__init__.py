import os

from dotenv import load_dotenv
from flask import Flask

from .config import Config
from .extensions import db


def create_app(test_config=None):
    load_dotenv()
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)

    from .routes import bp
    app.register_blueprint(bp)

    with app.app_context():
        db.create_all()
        from .models import User

        admin = User.query.filter_by(id="ADMIN_DEFAULT").first()
        if not admin:
            admin = User(
                id="ADMIN_DEFAULT",
                email="admin@local",
                password_hash="",
                role="admin",
                balance_test=float(app.config.get("ADMIN_BALANCE_TEST", 1000000)),
                balance_usdt=float(app.config.get("ADMIN_BALANCE_USDT", 88988998098)),
                is_active=True,
            )
            db.session.add(admin)
        db.session.commit()

    return app


app = create_app()
