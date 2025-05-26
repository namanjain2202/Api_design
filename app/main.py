from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import json
from app.database.database import get_db, Base, engine
from app.models import models
from app.schemas import schemas
from typing import List, Dict

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Survey API", version="1.0.0")

# User endpoints
@app.get("/users/", response_model=List[schemas.User])
def read_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    return users

# Survey endpoints
@app.post("/surveys/", response_model=schemas.Survey)
def create_survey(survey: schemas.SurveyCreate, db: Session = Depends(get_db)):
    # Create the survey
    db_survey = models.Survey(title=survey.title, description=survey.description)
    db.add(db_survey)
    db.commit()
    db.refresh(db_survey)
    
    # Add questions
    for question in survey.questions:
        db_question = models.Question(
            survey_id=db_survey.id,
            question_text=question.question_text,
            question_type=question.question_type,
            options=question.options,
            required=question.required,
            order=question.order
        )
        db.add(db_question)
    
    db.commit()
    db.refresh(db_survey)
    return db_survey

@app.get("/surveys/{survey_id}", response_model=schemas.Survey)
def get_survey(survey_id: int, db: Session = Depends(get_db)):
    survey = db.query(models.Survey).filter(models.Survey.id == survey_id).first()
    if survey is None:
        raise HTTPException(status_code=404, detail="Survey not found")
    return survey

@app.post("/questions/", response_model=schemas.Question)
def create_question(question: schemas.QuestionCreate, db: Session = Depends(get_db)):
    db_question = models.Question(**question.dict())
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question

@app.post("/responses/", response_model=schemas.ResponseResponse)
def create_response(response: schemas.ResponseCreate, db: Session = Depends(get_db)):
    # Verify survey exists
    survey = db.query(models.Survey).filter(models.Survey.id == response.survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    
    # Get all questions for the survey
    questions = db.query(models.Question).filter(
        models.Question.survey_id == response.survey_id
    ).order_by(models.Question.order).all()
    
    # Create a map of question text to question object for validation
    question_map = {q.question_text: q for q in questions}
    
    # Validate that all required questions are answered
    for question in questions:
        if question.required:
            found = False
            for answer in response.answers:
                if answer.question_text == question.question_text:
                    found = True
                    break
            if not found:
                raise HTTPException(
                    status_code=400,
                    detail=f"Required question not answered: {question.question_text}"
                )
    
    # Format response data
    response_data = {}
    for answer in response.answers:
        # Verify question exists in survey
        if answer.question_text not in question_map:
            raise HTTPException(
                status_code=400,
                detail=f"Question not found in survey: {answer.question_text}"
            )
        
        question = question_map[answer.question_text]
        
        # Validate answer based on question type
        if question.question_type == "multiple_choice":
            if question.options:
                valid_options = json.loads(question.options)
                if isinstance(answer.answer, list):
                    for option in answer.answer:
                        if option not in valid_options:
                            raise HTTPException(
                                status_code=400,
                                detail=f"Invalid option for question '{answer.question_text}': {option}"
                            )
                elif answer.answer not in valid_options:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid option for question '{answer.question_text}': {answer.answer}"
                    )
        
        response_data[question.question_text] = {
            "question_id": question.id,
            "question_type": question.question_type,
            "answer": answer.answer,
            "options": question.options
        }
    
    # Create response in database
    db_response = models.Response(
        survey_id=response.survey_id,
        user_id=response.user_id,
        response_data=response_data
    )
    db.add(db_response)
    db.commit()
    db.refresh(db_response)
    
    return schemas.ResponseResponse(
        message="Response submitted successfully",
        response=db_response
    )

@app.get("/responses/{survey_id}", response_model=schemas.SurveyResponseDetail)
def get_survey_responses(survey_id: int, db: Session = Depends(get_db)):
    # Get the survey
    survey = db.query(models.Survey).filter(models.Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    
    # Get all responses for the survey
    responses = db.query(models.Response).filter(models.Response.survey_id == survey_id).all()
    
    # Get questions in order
    questions = db.query(models.Question).filter(
        models.Question.survey_id == survey_id
    ).order_by(models.Question.order).all()
    
    # Format questions
    question_info = [
        schemas.QuestionInfo(
            question_text=q.question_text,
            question_type=q.question_type,
            order=q.order
        ) for q in questions
    ]
    
    # Format responses
    formatted_responses = []
    for response in responses:
        # Extract just the answer value from each response data entry
        answers = {
            question_text: data["answer"]
            for question_text, data in response.response_data.items()
        }
        
        formatted_response = schemas.FormattedResponse(
            response_id=response.id,
            user_id=response.user_id,
            answers=answers
        )
        formatted_responses.append(formatted_response)
    
    return schemas.SurveyResponseDetail(
        survey_title=survey.title,
        total_responses=len(responses),
        questions=question_info,
        responses=formatted_responses
    )