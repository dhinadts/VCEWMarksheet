import math
import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.database import get_db
from app.core.security import hash_password
from app.models.models import (AcademicClass, AcademicYear, Assessment, AssessmentType, Course, CourseCategory,
                               CourseOffering, Department, MarksheetUpload, OCRExtraction, Professor,
                               ProfessorAssignment, Programme, Semester, Student, User, UserType)
from app.schemas.academic import (AssessmentCreate, AssignmentCreate, ClassCreate, CourseCreate, OfferingCreate,
                                  ProfessorCreate, StudentCreate)
from app.schemas.common import ok

router = APIRouter()
admin_only = require_roles(UserType.ADMIN)
staff = require_roles(UserType.ADMIN, UserType.PROFESSOR)


@router.get("/academic-years")
def list_academic_years(_: User = Depends(staff), db: Session = Depends(get_db)):
    return ok([serialize(row) for row in db.scalars(select(AcademicYear).order_by(AcademicYear.start_date.desc())).all()])


@router.get("/departments")
def list_departments(_: User = Depends(staff), db: Session = Depends(get_db)):
    return ok([serialize(row) for row in db.scalars(select(Department).order_by(Department.name)).all()])


@router.get("/programmes")
def list_programmes(_: User = Depends(staff), db: Session = Depends(get_db)):
    return ok([serialize(row) for row in db.scalars(select(Programme).order_by(Programme.name)).all()])


@router.get("/semesters")
def list_semesters(_: User = Depends(staff), db: Session = Depends(get_db)):
    return ok([serialize(row) for row in db.scalars(select(Semester).order_by(Semester.number)).all()])


@router.get("/assessment-types")
def list_assessment_types(_: User = Depends(staff), db: Session = Depends(get_db)):
    return ok([serialize(row) for row in db.scalars(select(AssessmentType).order_by(AssessmentType.name)).all()])


def serialize(row) -> dict:
    result = {}
    for column in row.__table__.columns:
        value = getattr(row, column.name)
        if isinstance(value, uuid.UUID): value = str(value)
        elif isinstance(value, Decimal): value = float(value)
        elif hasattr(value, "value"): value = value.value
        result[column.name] = value
    return result


def page(db: Session, model, page_number: int, page_size: int, *filters):
    query = select(model).where(*filters).order_by(model.created_at.desc())
    total = db.scalar(select(func.count()).select_from(model).where(*filters)) or 0
    items = db.scalars(query.offset((page_number - 1) * page_size).limit(page_size)).all()
    return {"items": [serialize(item) for item in items], "page": page_number, "page_size": page_size, "total": total, "total_pages": math.ceil(total / page_size) if total else 0}


@router.get("/classes")
def list_classes(page_number: int = Query(1, alias="page", ge=1), page_size: int = Query(20, ge=1, le=100), user: User = Depends(staff), db: Session = Depends(get_db)):
    if user.user_type == UserType.PROFESSOR:
        professor = db.scalar(select(Professor).where(Professor.user_id == user.id))
        query = select(AcademicClass).join(CourseOffering).join(ProfessorAssignment).where(ProfessorAssignment.professor_id == professor.id, ProfessorAssignment.active.is_(True)).distinct().order_by(AcademicClass.created_at.desc())
        all_rows = db.scalars(query).all(); total = len(all_rows); items = all_rows[(page_number - 1) * page_size:page_number * page_size]
        return ok({"items": [serialize(row) for row in items], "page": page_number, "page_size": page_size, "total": total, "total_pages": math.ceil(total / page_size) if total else 0})
    return ok(page(db, AcademicClass, page_number, page_size))


@router.post("/classes", status_code=201)
def create_class(body: ClassCreate, _: User = Depends(admin_only), db: Session = Depends(get_db)):
    row = AcademicClass(**body.model_dump()); db.add(row); db.commit(); db.refresh(row)
    return ok(serialize(row), "Class created")


@router.patch("/classes/{class_id}/archive")
def archive_class(class_id: uuid.UUID, _: User = Depends(admin_only), db: Session = Depends(get_db)):
    row = db.get(AcademicClass, class_id)
    if not row: raise HTTPException(404, detail={"code": "CLASS_NOT_FOUND", "message": "Class not found"})
    row.archived = True; db.commit()
    return ok(serialize(row), "Class archived")


@router.get("/students")
def list_students(register_number: str | None = None, page_number: int = Query(1, alias="page", ge=1), page_size: int = Query(20, ge=1, le=100), user: User = Depends(staff), db: Session = Depends(get_db)):
    filters = (Student.register_number.ilike(f"%{register_number}%"),) if register_number else ()
    if user.user_type == UserType.PROFESSOR:
        professor = db.scalar(select(Professor).where(Professor.user_id == user.id))
        query = select(Student).join(AcademicClass).join(CourseOffering).join(ProfessorAssignment).where(ProfessorAssignment.professor_id == professor.id, ProfessorAssignment.active.is_(True), *filters).distinct().order_by(Student.created_at.desc())
        all_rows = db.scalars(query).all(); total = len(all_rows); items = all_rows[(page_number - 1) * page_size:page_number * page_size]
        return ok({"items": [serialize(row) for row in items], "page": page_number, "page_size": page_size, "total": total, "total_pages": math.ceil(total / page_size) if total else 0})
    return ok(page(db, Student, page_number, page_size, *filters))


@router.post("/students", status_code=201)
def create_student(body: StudentCreate, _: User = Depends(admin_only), db: Session = Depends(get_db)):
    values = body.model_dump(); user = User(username=values.pop("username"), email=values.pop("email"), password_hash=hash_password(values.pop("password")), user_type=UserType.STUDENT, must_change_password=True)
    db.add(user); db.flush(); row = Student(user_id=user.id, **values); db.add(row); db.commit(); db.refresh(row)
    return ok(serialize(row), "Student created")


@router.get("/professors")
def list_professors(page_number: int = Query(1, alias="page", ge=1), page_size: int = Query(20, ge=1, le=100), _: User = Depends(staff), db: Session = Depends(get_db)):
    return ok(page(db, Professor, page_number, page_size))


@router.post("/professors", status_code=201)
def create_professor(body: ProfessorCreate, _: User = Depends(admin_only), db: Session = Depends(get_db)):
    values = body.model_dump(); user = User(username=values.pop("username"), email=values.pop("email"), password_hash=hash_password(values.pop("password")), user_type=UserType.PROFESSOR, must_change_password=True)
    db.add(user); db.flush(); row = Professor(user_id=user.id, **values); db.add(row); db.commit(); db.refresh(row)
    return ok(serialize(row), "Professor created")


@router.get("/courses")
def list_courses(semester_number: int | None = None, page_number: int = Query(1, alias="page", ge=1), page_size: int = Query(50, ge=1, le=100), user: User = Depends(staff), db: Session = Depends(get_db)):
    filters = (Course.active.is_(True), *((Course.semester_number == semester_number,) if semester_number else ()))
    if user.user_type == UserType.PROFESSOR:
        professor = db.scalar(select(Professor).where(Professor.user_id == user.id))
        query = select(Course).join(CourseOffering).join(ProfessorAssignment).where(ProfessorAssignment.professor_id == professor.id, ProfessorAssignment.active.is_(True), *filters).distinct().order_by(Course.created_at.desc())
        all_rows = db.scalars(query).all(); total = len(all_rows); items = all_rows[(page_number - 1) * page_size:page_number * page_size]
        return ok({"items": [serialize(row) for row in items], "page": page_number, "page_size": page_size, "total": total, "total_pages": math.ceil(total / page_size) if total else 0})
    return ok(page(db, Course, page_number, page_size, *filters))


@router.post("/courses", status_code=201)
def create_course(body: CourseCreate, _: User = Depends(admin_only), db: Session = Depends(get_db)):
    try: category = CourseCategory(body.category)
    except ValueError: raise HTTPException(422, detail={"code": "INVALID_COURSE_CATEGORY", "message": "Invalid course category"})
    row = Course(**body.model_dump(exclude={"category"}), category=category); db.add(row); db.commit(); db.refresh(row)
    return ok(serialize(row), "Course created")


@router.get("/course-offerings")
def list_offerings(user: User = Depends(staff), db: Session = Depends(get_db)):
    query = select(CourseOffering).where(CourseOffering.active.is_(True))
    if user.user_type == UserType.PROFESSOR:
        professor = db.scalar(select(Professor).where(Professor.user_id == user.id))
        query = query.join(ProfessorAssignment).where(ProfessorAssignment.professor_id == professor.id, ProfessorAssignment.active.is_(True))
    return ok([serialize(x) for x in db.scalars(query).all()])


@router.get("/my-subjects")
def list_my_subjects(user: User = Depends(require_roles(UserType.PROFESSOR)), db: Session = Depends(get_db)):
    professor = db.scalar(select(Professor).where(Professor.user_id == user.id))
    if not professor:
        raise HTTPException(404, detail={"code": "PROFESSOR_NOT_FOUND", "message": "Professor profile not found"})

    offerings = db.scalars(
        select(CourseOffering)
        .join(ProfessorAssignment)
        .where(
            ProfessorAssignment.professor_id == professor.id,
            ProfessorAssignment.active.is_(True),
            CourseOffering.active.is_(True),
        )
        .order_by(CourseOffering.created_at.desc())
    ).all()

    subjects = []
    for offering in offerings:
        course = db.get(Course, offering.course_id)
        academic_class = db.get(AcademicClass, offering.class_id)
        assessments = db.scalars(
            select(Assessment)
            .where(Assessment.course_offering_id == offering.id)
            .order_by(Assessment.assessment_date, Assessment.created_at)
        ).all()
        students = db.scalars(
            select(Student)
            .join(User, Student.user_id == User.id)
            .where(Student.class_id == offering.class_id, Student.active.is_(True), User.is_active.is_(True))
            .order_by(Student.register_number)
        ).all()

        student_rows = []
        for student in students:
            marks = {}
            for assessment in assessments:
                upload = db.scalar(
                    select(MarksheetUpload)
                    .where(
                        MarksheetUpload.student_id == student.id,
                        MarksheetUpload.assessment_id == assessment.id,
                        MarksheetUpload.course_offering_id == offering.id,
                    )
                    .order_by(MarksheetUpload.created_at.desc())
                    .limit(1)
                )
                total = None
                status = "NOT_CAPTURED"
                extracted_values = []
                if upload:
                    values = db.scalars(
                        select(OCRExtraction)
                        .where(OCRExtraction.marksheet_upload_id == upload.id)
                        .order_by(OCRExtraction.field_name)
                    ).all()
                    numeric_values = [row.reviewed_value if row.reviewed_value is not None else row.numeric_value for row in values]
                    extracted_values = [
                        {
                            "field": row.field_name,
                            "value": float(row.reviewed_value if row.reviewed_value is not None else row.numeric_value),
                            "confidence": float(row.confidence),
                        }
                        for row in values
                        if row.reviewed_value is not None or row.numeric_value is not None
                    ]
                    if numeric_values and all(value is not None for value in numeric_values):
                        total = float(sum(numeric_values, Decimal("0")))
                    status = upload.review_status
                marks[str(assessment.id)] = {"total": total, "status": status, "values": extracted_values}

            student_rows.append({
                "id": str(student.id),
                "register_number": student.register_number,
                "roll_number": student.roll_number,
                "name": student.name,
                "marks": marks,
            })

        subjects.append({
            "id": str(offering.id),
            "course_code": course.code,
            "course_name": course.name,
            "class_code": academic_class.code,
            "section": academic_class.section,
            "assessments": [
                {"id": str(row.id), "name": row.name, "maximum_marks": float(row.maximum_marks)}
                for row in assessments
            ],
            "students": student_rows,
        })
    return ok(subjects)


@router.post("/course-offerings", status_code=201)
def create_offering(body: OfferingCreate, _: User = Depends(admin_only), db: Session = Depends(get_db)):
    row = CourseOffering(**body.model_dump()); db.add(row); db.commit(); db.refresh(row); return ok(serialize(row), "Course offering created")


@router.post("/professor-assignments", status_code=201)
def create_assignment(body: AssignmentCreate, _: User = Depends(admin_only), db: Session = Depends(get_db)):
    row = ProfessorAssignment(**body.model_dump()); db.add(row); db.commit(); db.refresh(row); return ok(serialize(row), "Professor assigned")


@router.get("/professor-assignments")
def list_assignments(user: User = Depends(staff), db: Session = Depends(get_db)):
    query = select(ProfessorAssignment)
    if user.user_type == UserType.PROFESSOR:
        professor = db.scalar(select(Professor).where(Professor.user_id == user.id))
        query = query.where(ProfessorAssignment.professor_id == professor.id)
    return ok([serialize(row) for row in db.scalars(query.order_by(ProfessorAssignment.created_at.desc())).all()])


@router.get("/assessments")
def list_assessments(user: User = Depends(staff), db: Session = Depends(get_db)):
    query = select(Assessment)
    if user.user_type == UserType.PROFESSOR:
        professor = db.scalar(select(Professor).where(Professor.user_id == user.id))
        query = query.join(CourseOffering).join(ProfessorAssignment).where(ProfessorAssignment.professor_id == professor.id, ProfessorAssignment.active.is_(True))
    return ok([serialize(x) for x in db.scalars(query).all()])


@router.post("/assessments", status_code=201)
def create_assessment(body: AssessmentCreate, user: User = Depends(staff), db: Session = Depends(get_db)):
    if user.user_type == UserType.PROFESSOR:
        professor = db.scalar(select(Professor).where(Professor.user_id == user.id))
        assigned = db.scalar(select(ProfessorAssignment).where(ProfessorAssignment.professor_id == professor.id, ProfessorAssignment.course_offering_id == body.course_offering_id, ProfessorAssignment.active.is_(True)))
        if not assigned: raise HTTPException(403, detail={"code": "UNASSIGNED_COURSE", "message": "Professor is not assigned to this course offering"})
    row = Assessment(**body.model_dump()); db.add(row); db.commit(); db.refresh(row); return ok(serialize(row), "Assessment created")
