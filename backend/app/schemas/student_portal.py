from pydantic import BaseModel, Field


class StudentResultsRequest(BaseModel):
    roll_number: str = Field(min_length=4, max_length=50)
