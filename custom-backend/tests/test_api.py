import os
import sys
import tempfile
import uuid
from uuid import UUID
import pytest

# Bootstrapping import path so running directly or via IDE handles imports properly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models import User, File, RevokedToken
from app.rate_limit import clear_all_failures

# Setup SQLite in-memory database for testing
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Override get_db in FastAPI
app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_db():
    # Create tables before each test
    Base.metadata.create_all(bind=engine)
    yield
    # Drop tables after each test
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(autouse=True)
def clear_rate_limit():
    clear_all_failures()
    yield
    clear_all_failures()

client = TestClient(app)

def test_register_and_login():
    # 1. Register a user
    resp = client.post("/register", json={"email": "test@example.com", "password": "Password123!"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

    # Try duplicate email registration
    resp = client.post("/register", json={"email": "test@example.com", "password": "Password123!"})
    assert resp.status_code == 409

    # 2. Login with correct credentials
    resp = client.post("/login", json={"email": "test@example.com", "password": "Password123!"})
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert data["user"]["email"] == "test@example.com"

    # Login with wrong credentials
    resp = client.post("/login", json={"email": "test@example.com", "password": "WrongPassword"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid email or password"

def test_login_lockout():
    # Register user
    client.post("/register", json={"email": "lockout@example.com", "password": "Password123!"})

    # Fail login 5 times
    for _ in range(5):
        resp = client.post("/login", json={"email": "lockout@example.com", "password": "wrong"})
        assert resp.status_code == 401

    # 6th attempt should be locked out (429)
    resp = client.post("/login", json={"email": "lockout@example.com", "password": "wrong"})
    assert resp.status_code == 429
    assert "Too many failed login attempts" in resp.json()["detail"]

def test_me_endpoint():
    # Register and login
    client.post("/register", json={"email": "me@example.com", "password": "Password123!"})
    login_resp = client.post("/login", json={"email": "me@example.com", "password": "Password123!"})
    token = login_resp.json()["token"]

    # Access /me
    resp = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@example.com"

    # Access /me without auth
    resp = client.get("/me")
    assert resp.status_code == 401

    # Access /me with invalid token
    resp = client.get("/me", headers={"Authorization": "Bearer invalidtoken"})
    assert resp.status_code == 401

def test_files_endpoints():
    # Register and login Alice
    client.post("/register", json={"email": "alice@example.com", "password": "Password123!"})
    alice_login = client.post("/login", json={"email": "alice@example.com", "password": "Password123!"})
    alice_token = alice_login.json()["token"]
    alice_id = alice_login.json()["user"]["id"]

    # Register and login Bob
    client.post("/register", json={"email": "bob@example.com", "password": "Password123!"})
    bob_login = client.post("/login", json={"email": "bob@example.com", "password": "Password123!"})
    bob_token = bob_login.json()["token"]

    # Seed some files in SQLite test db
    db = TestingSessionLocal()
    
    # Create temp files for storage path
    temp_dir = tempfile.mkdtemp()
    alice_file_path = os.path.join(temp_dir, "alice_file.txt")
    with open(alice_file_path, "w") as f:
        f.write("Alice private data")
        
    bob_file_path = os.path.join(temp_dir, "bob_file.txt")
    with open(bob_file_path, "w") as f:
        f.write("Bob private data")

    alice_file_id = uuid.uuid4()
    bob_file_id = uuid.uuid4()

    db.add(File(
        id=alice_file_id,
        owner_id=UUID(alice_id),
        file_name="alice_file.txt",
        mime_type="text/plain",
        size_bytes=len("Alice private data"),
        storage_path=alice_file_path
    ))
    db.add(File(
        id=bob_file_id,
        owner_id=UUID(bob_login.json()["user"]["id"]),
        file_name="bob_file.txt",
        mime_type="text/plain",
        size_bytes=len("Bob private data"),
        storage_path=bob_file_path
    ))
    db.commit()
    db.close()

    # 1. Alice gets her files list
    resp = client.get("/files", headers={"Authorization": f"Bearer {alice_token}"})
    assert resp.status_code == 200
    files = resp.json()
    assert len(files) == 1
    assert files[0]["id"] == str(alice_file_id)

    # 2. Alice requests her own file detail
    resp = client.get(f"/files/{alice_file_id}", headers={"Authorization": f"Bearer {alice_token}"})
    assert resp.status_code == 200
    assert resp.json()["fileName"] == "alice_file.txt"

    # 3. Alice requests Bob's file detail (should be 403)
    resp = client.get(f"/files/{bob_file_id}", headers={"Authorization": f"Bearer {alice_token}"})
    assert resp.status_code == 403

    # 4. Alice requests a nonexistent file UUID (should be 404)
    nonexistent_id = uuid.uuid4()
    resp = client.get(f"/files/{nonexistent_id}", headers={"Authorization": f"Bearer {alice_token}"})
    assert resp.status_code == 404

    # 5. Alice downloads her own file
    resp = client.get(f"/files/{alice_file_id}/download", headers={"Authorization": f"Bearer {alice_token}"})
    assert resp.status_code == 200
    assert resp.content == b"Alice private data"

    # 6. Alice tries to download Bob's file (should be 403)
    resp = client.get(f"/files/{bob_file_id}/download", headers={"Authorization": f"Bearer {alice_token}"})
    assert resp.status_code == 403

def test_logout_revocation():
    client.post("/register", json={"email": "logout@example.com", "password": "Password123!"})
    login_resp = client.post("/login", json={"email": "logout@example.com", "password": "Password123!"})
    token = login_resp.json()["token"]

    # Verify we can access /me
    resp = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

    # Logout
    logout_resp = client.post("/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout_resp.status_code == 200
    assert logout_resp.json()["message"] == "Logout successful"

    # Verify we CANNOT access /me anymore with that token
    resp = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
