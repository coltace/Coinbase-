cat > app/__init__.py << 'EOF'
import os
from dotenv import load_dotenv
from flask import Flask
from .config import Config
from .extensions import db

def create_app(test_config=None):
    load_dotenv()
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    if test_config: app.config.update(test_config)
    os.makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)
    from .routes import bp
    app.register_blueprint(bp)
    with app.app_context():
        db.create_all()
        admin = User.query.get("ADMIN_DEFAULT")
        if not admin:
            admin = User(id="ADMIN_DEFAULT", balance_test=app.config["ADMIN_BALANCE_TEST"], balance_usdt=app.config["ADMIN_BALANCE_USDT"])
            db.session.add(admin)
            db.session.commit()
    return app

app = create_app()
EOF
