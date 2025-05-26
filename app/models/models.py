from sqlalchemy import Column, Integer, String, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from app.database.database import Base
import enum

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    full_name = Column(String)

class QuestionType(str, enum.Enum):
    short_text = "short_test"
    long_text = "long_text"
    multiple_choice = "multiple_choice"
    number = "number"
    checkbox = "checkbox"
    date = "date"

class Survey(Base):
    __tablename__ = "surveys"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, nullable=True)
    questions = relationship("Question", back_populates="survey")
    responses = relationship("Response", back_populates="survey")

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    survey_id = Column(Integer, ForeignKey("surveys.id"))
    question_text = Column(String)
    question_type = Column(String)  # e.g., 'text', 'multiple_choice', 'single_choice'
    options = Column(String, nullable=True)  # JSON string for choices
    required = Column(Integer, default=0)  # 0 for False, 1 for True
    order = Column(Integer, default=0)
    
    survey = relationship("Survey", back_populates="questions")
    question_options = relationship("QuestionOption", back_populates="question")

class QuestionOption(Base):
    __tablename__ = "question_options"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    option_text = Column(String)
    is_correct = Column(Integer, default=0)  # For quiz-type questions
    
    question = relationship("Question", back_populates="question_options")

class Response(Base):
    __tablename__ = "responses"
    
    id = Column(Integer, primary_key=True, index=True)
    survey_id = Column(Integer, ForeignKey("surveys.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    response_data = Column(JSON)  # Store response data as JSON
    
    survey = relationship("Survey", back_populates="responses")
    user = relationship("User")