import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class ClassCreate(BaseModel):
    code: str
    academic_year_id: uuid.UUID
    department_id: uuid.UUID
    programme_id: uuid.UUID
    semester_id: uuid.UUID
    section: str
    batch: str
    strength: int = Field(gt=0)
    class_advisor_id: uuid.UUID | None = None


class StudentCreate(BaseModel):
    username: str
    email: str | None = None
    password: str = Field(min_length=8)
    register_number: str
    roll_number: str
    name: str
    programme_id: uuid.UUID
    department_id: uuid.UUID
    class_id: uuid.UUID
    admission_year: int
    current_semester: int = Field(ge=1, le=8)
    section: str


class ProfessorCreate(BaseModel):
    username: str
    email: str | None = None
    password: str = Field(min_length=8)
    employee_number: str
    name: str
    department_id: uuid.UUID
    designation: str = "Assistant Professor"


class CourseCreate(BaseModel):
    programme_id: uuid.UUID
    code: str
    name: str
    curriculum_slot_name: str | None = None
    actual_course_code: str | None = None
    actual_course_name: str | None = None
    category: str
    credits: Decimal = Decimal("0")
    ca_max: Decimal = Field(ge=0)
    ese_max: Decimal = Field(ge=0)
    total_max: Decimal = Field(gt=0)
    semester_number: int = Field(ge=1, le=8)
    regulation: str

    @model_validator(mode="after")
    def validate_total(self):
        if self.ca_max + self.ese_max != self.total_max:
            raise ValueError("ca_max plus ese_max must equal total_max")
        return self


class OfferingCreate(BaseModel):
    course_id: uuid.UUID
    academic_year_id: uuid.UUID
    semester_id: uuid.UUID
    class_id: uuid.UUID


class AssignmentCreate(BaseModel):
    professor_id: uuid.UUID
    course_offering_id: uuid.UUID


class AssessmentCreate(BaseModel):
    course_offering_id: uuid.UUID
    assessment_type_id: uuid.UUID
    name: str
    maximum_marks: Decimal = Field(gt=0)
    weightage: Decimal | None = Field(default=None, ge=0)
    raw_maximum: Decimal | None = Field(default=None, gt=0)
    converted_maximum: Decimal | None = Field(default=None, gt=0)
    assessment_date: date | None = None

    @model_validator(mode="after")
    def scaling_pair(self):
        if (self.raw_maximum is None) != (self.converted_maximum is None):
            raise ValueError("raw_maximum and converted_maximum must be provided together")
        return self
