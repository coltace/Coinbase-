import pytest
from app import create_app
from app.extensions import db
from app.models import User


@pytest.fixture()
def app(tmp_path):
    database_path = tmp_path / "test.db"
    application = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret-key",
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database_path}",
        "SEPOLIA_RPC_URL": "",
        "PTC_CONTRACT_ADDRESS": "0x3333333333333333333333333333333333333333",
        "RATELIMIT_ENABLED": False,
        "SESSION_COOKIE_SECURE": False,
        "ADMIN_EMAIL": "",
        "ADMIN_BOOTSTRAP_TOKEN": "",
    })
    yield application
    with application.app_context():
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def register(client, email="user@example.com", password="correct horse battery staple"):
    response = client.post("/api/auth/register", json={"email": email, "password": password})
    assert response.status_code == 201
    return response.get_json()


def csrf(client):
    response = client.get("/api/auth/csrf")
    assert response.status_code == 200
    return response.get_json()["csrfToken"]


def test_health_check(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_registration_and_user_specific_transfer_intent(client):
    data = register(client)
    token = data["csrfToken"]
    response = client.post("/api/transfers/prepare", headers={"X-CSRF-Token": token}, json={"sender": "0x1111111111111111111111111111111111111111", "recipient": "0x2222222222222222222222222222222222222222", "amount": "0.001"})
    assert response.status_code == 201
    assert response.get_json()["amountWei"] == "1000000000000000"


def test_transfer_requires_authentication_and_csrf(client):
    payload = {"sender": "0x1111111111111111111111111111111111111111", "recipient": "0x2222222222222222222222222222222222222222", "amount": "0.001"}
    assert client.post("/api/transfers/prepare", json=payload).status_code == 401
    register(client)
    assert client.post("/api/transfers/prepare", json=payload).status_code == 403


def test_prepare_rejects_invalid_address(client):
    token = register(client)["csrfToken"]
    response = client.post("/api/transfers/prepare", headers={"X-CSRF-Token": token}, json={"sender": "not-an-address", "recipient": "0x1111111111111111111111111111111111111111", "amount": "0.001"})
    assert response.status_code == 400


def test_prepare_rejects_amount_over_demo_limit(client):
    token = register(client)["csrfToken"]
    response = client.post("/api/transfers/prepare", headers={"X-CSRF-Token": token}, json={"sender": "0x1111111111111111111111111111111111111111", "recipient": "0x2222222222222222222222222222222222222222", "amount": "0.06"})
    assert response.status_code == 400


def test_admin_distribution_is_forbidden_for_normal_user(client):
    token = register(client)["csrfToken"]
    response = client.post("/api/admin/distributions/prepare", headers={"X-CSRF-Token": token}, json={"recipientAddress": "0x2222222222222222222222222222222222222222", "amount": "10"})
    assert response.status_code == 403


def test_admin_can_prepare_distribution_and_audit_log(app, client):
    with app.app_context():
        admin = User(id="admin1", email="admin@example.com", password_hash="unused", role="admin")
        db.session.add(admin)
        db.session.commit()
    client.post("/api/auth/login", json={"email": "admin@example.com", "password": "wrong"})
    # Set a known password through the supported registration hash helper.
    from werkzeug.security import generate_password_hash
    with app.app_context():
        admin = User.query.filter_by(email="admin@example.com").first()
        admin.password_hash = generate_password_hash("correct horse battery staple")
        db.session.commit()
    login = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "correct horse battery staple"})
    token = login.get_json()["csrfToken"]
    response = client.post("/api/admin/distributions/prepare", headers={"X-CSRF-Token": token}, json={"recipientAddress": "0x2222222222222222222222222222222222222222", "amount": "10"})
    assert response.status_code == 201
    logs = client.get("/api/admin/audit-logs")
    assert logs.status_code == 200
    assert any(log["action"] == "token_distribution_intent_created" for log in logs.get_json()["logs"])
