from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database.database import Base, get_db
import pytest
import json

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def create_test_survey():
    """Helper function to create a test survey with questions"""
    survey_response = client.post(
        "/surveys/",
        json={
            "title": "Job Application Survey",
            "description": "Test job application survey",
            "questions": [
                {
                    "question_text": "What is your name?",
                    "question_type": "short_text",
                    "required": True,
                    "order": 1
                },
                {
                    "question_text": "Years of experience?",
                    "question_type": "number",
                    "required": True,
                    "order": 2
                },
                {
                    "question_text": "Preferred programming languages?",
                    "question_type": "multiple_choice",
                    "options": '["Python", "Java", "JavaScript"]',
                    "required": True,
                    "order": 3
                }
            ]
        }
    )
    return survey_response.json()

# Test survey creation
def test_create_survey_with_questions():
    survey = create_test_survey()
    assert survey["title"] == "Job Application Survey"
    assert len(survey["questions"]) == 3
    assert survey["questions"][0]["question_type"] == "short_text"
    assert survey["questions"][1]["question_type"] == "number"
    assert survey["questions"][2]["question_type"] == "multiple_choice"

def test_create_survey_without_questions():
    response = client.post(
        "/surveys/",
        json={
            "title": "Invalid Survey",
            "description": "Survey without questions"
        }
    )
    assert response.status_code == 422  # Validation error

def test_get_survey():
    survey = create_test_survey()
    response = client.get(f"/surveys/{survey['id']}")
    assert response.status_code == 200
    assert response.json()["title"] == "Job Application Survey"
    assert len(response.json()["questions"]) == 3

def test_get_nonexistent_survey():
    response = client.get("/surveys/99999")
    assert response.status_code == 404

# Test response submission
def test_submit_valid_response():
    survey = create_test_survey()
    response = client.post(
        "/responses/",
        json={
            "survey_id": survey["id"],
            "user_id": 1,
            "answers": [
                {
                    "question_text": "What is your name?",
                    "question_type": "short_text",
                    "answer": "John Doe"
                },
                {
                    "question_text": "Years of experience?",
                    "question_type": "number",
                    "answer": "5"
                },
                {
                    "question_text": "Preferred programming languages?",
                    "question_type": "multiple_choice",
                    "answer": ["Python", "Java"],
                    "options": '["Python", "Java", "JavaScript"]'
                }
            ]
        }
    )
    assert response.status_code == 200
    assert "Response submitted successfully" in response.json()["message"]

def test_submit_response_missing_required():
    survey = create_test_survey()
    response = client.post(
        "/responses/",
        json={
            "survey_id": survey["id"],
            "user_id": 1,
            "answers": [
                {
                    "question_text": "What is your name?",
                    "question_type": "short_text",
                    "answer": "John Doe"
                }
                # Missing other required questions
            ]
        }
    )
    assert response.status_code == 400
    assert "Required question not answered" in response.json()["detail"]

def test_submit_response_invalid_multiple_choice():
    survey = create_test_survey()
    response = client.post(
        "/responses/",
        json={
            "survey_id": survey["id"],
            "user_id": 1,
            "answers": [
                {
                    "question_text": "What is your name?",
                    "question_type": "short_text",
                    "answer": "John Doe"
                },
                {
                    "question_text": "Years of experience?",
                    "question_type": "number",
                    "answer": "5"
                },
                {
                    "question_text": "Preferred programming languages?",
                    "question_type": "multiple_choice",
                    "answer": ["InvalidLanguage"],
                    "options": '["Python", "Java", "JavaScript"]'
                }
            ]
        }
    )
    assert response.status_code == 400
    assert "Invalid option" in response.json()["detail"]

def test_get_survey_responses():
    survey = create_test_survey()
    # Submit a response
    client.post(
        "/responses/",
        json={
            "survey_id": survey["id"],
            "user_id": 1,
            "answers": [
                {
                    "question_text": "What is your name?",
                    "question_type": "short_text",
                    "answer": "John Doe"
                },
                {
                    "question_text": "Years of experience?",
                    "question_type": "number",
                    "answer": "5"
                },
                {
                    "question_text": "Preferred programming languages?",
                    "question_type": "multiple_choice",
                    "answer": ["Python", "Java"],
                    "options": '["Python", "Java", "JavaScript"]'
                }
            ]
        }
    )
    
    response = client.get(f"/responses/{survey['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["survey_title"] == "Job Application Survey"
    assert data["total_responses"] == 1
    assert len(data["questions"]) == 3
    assert len(data["responses"]) == 1
    assert data["responses"][0]["answers"]["What is your name?"] == "John Doe"

def test_get_responses_nonexistent_survey():
    response = client.get("/responses/99999")
    assert response.status_code == 404

def test_submit_response_nonexistent_survey():
    response = client.post(
        "/responses/",
        json={
            "survey_id": 99999,
            "user_id": 1,
            "answers": []
        }
    )
    assert response.status_code == 404
    assert "Survey not found" in response.json()["detail"]