from app.database.database import SessionLocal
from app.models.models import User, Survey, Question, Response

db = SessionLocal()

# Add sample users if they don't exist
users = [
    User(username="johndoe", email="john@example.com", full_name="John Doe", password="password123"),
    User(username="janesmith", email="jane@example.com", full_name="Jane Smith", password="password123")
]

for user in users:
    if not db.query(User).filter(User.email == user.email).first():
        db.add(user)

# Add a sample survey
survey = Survey(
    title="Customer Feedback",
    description="Please provide your feedback about our service"
)
db.add(survey)
db.commit()

# Add sample questions
questions = [
    Question(
        survey_id=survey.id,
        question_text="How satisfied are you with our service?",
        question_type="single_choice",
        options='["Very Satisfied", "Satisfied", "Neutral", "Dissatisfied", "Very Dissatisfied"]',
        required=1,
        order=1
    ),
    Question(
        survey_id=survey.id,
        question_text="What improvements would you suggest?",
        question_type="text",
        required=0,
        order=2
    )
]

for question in questions:
    db.add(question)

db.commit()
db.close()

print("Sample data has been added successfully!")
