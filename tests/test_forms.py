import sys
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.database.session import get_db
from app.models.form import Form, FormField, FormFieldOption

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="function")
def db_session():
    # Create the database
    Form.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Form.metadata.drop_all(bind=engine)

def test_create_form(db_session):
    response = client.post(
        "/api/v1/forms/",
        json={
            "name": "Test Form",
            "key": "test-form",
            "description": "A form for testing",
            "is_active": True,
            "fields": [
                {
                    "label": "Test Field",
                    "field_name": "test_field",
                    "field_type": "text",
                    "is_required": True,
                }
            ],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Form"
    assert data["key"] == "test-form"
    assert len(data["fields"]) == 1
    assert data["fields"][0]["label"] == "Test Field"

def test_get_form(db_session):
    # First, create a form to retrieve
    client.post(
        "/api/v1/forms/",
        json={"name": "Get Form", "key": "get-form", "is_active": True},
    )

    response = client.get("/api/v1/forms/get-form")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Get Form"
    assert data["key"] == "get-form"

def test_update_form(db_session):
    # First, create a form to update
    client.post(
        "/api/v1/forms/",
        json={"name": "Update Form", "key": "update-form", "is_active": True},
    )

    response = client.put(
        "/api/v1/forms/update-form",
        json={
            "name": "Update Form",
            "key": "update-form",
            "description": "Updated description",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Updated description"

def test_delete_form(db_session):
    # First, create a form to delete
    client.post(
        "/api/v1/forms/",
        json={"name": "Delete Form", "key": "delete-form", "is_active": True},
    )

    response = client.delete("/api/v1/forms/delete-form")
    assert response.status_code == 204

    # Verify the form is deleted
    response = client.get("/api/v1/forms/delete-form")
    assert response.status_code == 404


def test_get_form_for_rendering(db_session):
    # First, create a form to retrieve
    client.post(
        "/api/v1/forms/",
        json={"name": "Render Form", "key": "render-form", "is_active": True},
    )

    response = client.get("/api/v1/forms/render-form/render")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Render Form"
    assert data["key"] == "render-form"