from pydantic import BaseModel, EmailStr, conlist
from typing import List, Optional, Dict, Any
from enum import Enum

class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    
    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    message: str
    user: Optional[User] = None

class QuestionType(str, Enum):
    short_text = "short_text"
    long_text = "long_text"
    multiple_choice = "multiple_choice"
    number = "number"
    checkbox = "checkbox"
    date = "date"

class QuestionOptionBase(BaseModel):
    option_text: str
    is_correct: bool = False

class QuestionOptionCreate(QuestionOptionBase):
    pass

class QuestionOption(QuestionOptionBase):
    id: int
    question_id: int
    
    class Config:
        from_attributes = True

class QuestionBase(BaseModel):
    question_text: str
    question_type: QuestionType
    options: Optional[str] = None
    required: bool = False
    order: int = 0

class QuestionCreate(QuestionBase):
    pass

class Question(QuestionBase):
    id: int
    survey_id: int
    question_options: List[QuestionOption] = []
    
    class Config:
        from_attributes = True

class SurveyBase(BaseModel):
    title: str
    description: Optional[str] = None

class SurveyCreate(SurveyBase):
    questions: conlist(QuestionBase, min_length=1)  # Require at least one question

class Survey(SurveyBase):
    id: int
    questions: List[Question] = []
    
    class Config:
        from_attributes = True

class ResponseBase(BaseModel):
    response_data: Dict

class QuestionAnswer(BaseModel):
    question_text: str
    question_type: str
    answer: Any
    options: Optional[str] = None

class ResponseCreate(BaseModel):
    survey_id: int
    user_id: int
    answers: List[QuestionAnswer]

class Response(ResponseBase):
    id: int
    survey_id: int
    user_id: int
    response_data: Dict[str, Any]
    
    class Config:
        from_attributes = True

class SurveyResponse(BaseModel):
    message: str
    survey: Optional[Survey] = None

class QuestionResponse(BaseModel):
    message: str
    question: Optional[Question] = None

class ResponseResponse(BaseModel):
    message: str
    response: Optional[Response] = None

class QuestionInfo(BaseModel):
    question_text: str
    question_type: str
    order: int

class FormattedResponse(BaseModel):
    response_id: int
    user_id: int
    answers: Dict[str, Any]

class SurveyResponseDetail(BaseModel):
    survey_title: str
    total_responses: int
    questions: List[QuestionInfo]
    responses: List[FormattedResponse]

