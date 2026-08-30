from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.models import (AcademicClass, AcademicYear, Admin, Assessment, AssessmentType, Course, CourseCategory,
                               CourseOffering, Department, Institution, Professor, ProfessorAssignment, Programme,
                               Semester, Student, User, UserType)

PROFESSOR_NAMES = ["Anitha Raman", "Bharathi Selvam", "Chitra Devi", "Deepa Kumar", "Elakkiya Raj", "Farzana Begum", "Geetha Mani", "Hema Priya", "Indira Mohan", "Janani Ravi"]
SEM3 = [
    ("U23MA304", "Discrete Mathematics", "THEORY"), ("U23CT301", "Python for Machine Learning", "THEORY"),
    ("U23IT302", "Data Structures", "THEORY"), ("U23CT302", "Artificial Intelligence", "THEORY"),
    ("U23CS305", "Computer Organization and Architecture", "THEORY"), ("VQAR", "VQAR", "THEORY"),
    ("U23CT303", "Operating Systems", "THEORY"), ("U23CT304", "Python for Machine Learning Laboratory", "PRACTICAL"),
    ("U23IT303", "Data Structures Laboratory", "PRACTICAL"), ("PD-III", "Personality Development", "MANDATORY"),
]
SEM5 = [
    ("U23MA509", "Probability, Queueing Theory & Game Theory", "THEORY"), ("U23CT508", "Machine Learning", "THEORY"),
    ("U23CS513", "Microprocessor and Embedded System", "THEORY"), ("PE-I", "Professional Elective - I", "ELECTIVE"),
    ("OE-I", "Open Elective - I", "ELECTIVE"), ("U23CT509", "Machine Learning Laboratory", "PRACTICAL"),
    ("U23CS514", "Microprocessor and Embedded System Laboratory", "PRACTICAL"), ("U23CT510", "Mini Project - I", "PRACTICAL"),
    ("CT-II", "Career Track Course - II", "CAREER_TRACK"),
]
PHASE0_SUBJECT = [("U23BTV37", "Bioenergy and Biofuels", "THEORY")]


def one(db: Session, model, defaults=None, **keys):
    row = db.scalar(select(model).filter_by(**keys))
    if not row:
        row = model(**keys, **(defaults or {})); db.add(row); db.flush()
    return row


def seed(db: Session) -> dict:
    password = get_settings().demo_default_password
    if not password:
        raise RuntimeError("DEMO_DEFAULT_PASSWORD must be set before running the development seed")
    institution = one(db, Institution, name="Vivekanandha College of Engineering for Women", code="VCEW")

    department = one(db, Department, institution_id=institution.id, code="BT", defaults={"name": "Biotechnology"})
    programme = one(db, Programme, department_id=department.id, code="BTECH-BT", regulation="2023", defaults={"name": "Biotechnology", "degree": "B.Tech"})
    year = one(db, AcademicYear, name="2026-2027", defaults={"start_date": date(2026, 6, 1), "end_date": date(2027, 5, 31)})
    sem3 = one(db, Semester, programme_id=programme.id, number=3, defaults={"name": "Semester III"})
    sem5 = one(db, Semester, programme_id=programme.id, number=5, defaults={"name": "Semester V"})
    sem6 = one(db, Semester, programme_id=programme.id, number=6, defaults={"name": "Semester VI"})
    professors = []
    for index, name in enumerate(PROFESSOR_NAMES, 1):
        username = f"PROF{index:02d}"
        user = one(db, User, username=username, defaults={"email": f"{username.lower()}@demo.vcew.edu", "password_hash": hash_password(password), "user_type": UserType.PROFESSOR, "must_change_password": True})
        user.is_active = True
        professors.append(one(db, Professor, user_id=user.id, defaults={"employee_number": username, "name": name, "department_id": department.id}))
    legacy_email_user = db.scalar(select(User).where(User.username == "dhinadts@gmail.com"))
    if legacy_email_user:
        legacy_email_user.email = None
        legacy_email_user.is_active = False
        db.flush()
    for index in range(1, 4):
        username = f"ADMIN{index:02d}"
        email = "dhinadts@gmail.com" if index == 1 else f"{username.lower()}@demo.vcew.edu"
        initial_password = "1234" if index == 1 else password
        user = one(db, User, username=username, defaults={"email": email, "password_hash": hash_password(initial_password), "user_type": UserType.ADMIN, "must_change_password": False})
        user.email = email; user.password_hash = hash_password(initial_password); user.is_active = True; user.must_change_password = False
        one(db, Admin, user_id=user.id, defaults={"employee_number": username, "name": f"System Administrator {index}"})
    class3 = one(db, AcademicClass, code="CST-III-A", defaults={"academic_year_id": year.id, "department_id": department.id, "programme_id": programme.id, "semester_id": sem3.id, "section": "A", "batch": "2025-2029", "strength": 0, "class_advisor_id": professors[0].id})
    class5 = one(db, AcademicClass, code="BT-VI-A", defaults={"academic_year_id": year.id, "department_id": department.id, "programme_id": programme.id, "semester_id": sem6.id, "section": "A", "batch": "2024-2028", "strength": 50, "class_advisor_id": professors[0].id})
    class3.strength = 0
    class5.strength = 50
    student_password_hash = hash_password(password)
    for index in range(1, 51):
        roll_number = f"VCEW{1000 + index}"; semester_no = 6; assigned_class = class5
        user = one(db, User, username=roll_number, defaults={"email": None, "password_hash": student_password_hash, "user_type": UserType.STUDENT, "must_change_password": False})
        user.is_active = True; user.must_change_password = False
        student = one(db, Student, user_id=user.id, defaults={"register_number": roll_number, "roll_number": roll_number, "name": f"Student {index:02d}", "programme_id": programme.id, "department_id": department.id, "class_id": assigned_class.id, "admission_year": 2023, "current_semester": semester_no, "section": "A"})
        student.class_id = class5.id; student.current_semester = 6; student.section = "A"; student.programme_id = programme.id; student.department_id = department.id; student.active = True

    # Retire superseded demo identities so only the requested account names can
    # authenticate after an existing development database is reseeded.
    db.query(User).filter(User.username.like("PROF___")).update({User.is_active: False}, synchronize_session=False)
    db.query(User).filter(User.username.like("ADMIN___")).update({User.is_active: False}, synchronize_session=False)
    db.query(User).filter(User.username.like("STU___")).update({User.is_active: False}, synchronize_session=False)
    assessment_type = one(db, AssessmentType, code="CAT1", defaults={"name": "Continuous Assessment Test 1"})
    offerings = []
    for semester_no, semester, assigned_class, courses in [(6, sem6, class5, PHASE0_SUBJECT)]:
        for code, name, category_name in courses:
            category = CourseCategory(category_name)
            ca, ese = (Decimal("60"), Decimal("40")) if category == CourseCategory.PRACTICAL else ((Decimal("100"), Decimal("0")) if category in (CourseCategory.MANDATORY, CourseCategory.CAREER_TRACK) else (Decimal("40"), Decimal("60")))
            course = one(db, Course, programme_id=programme.id, code=code, regulation="2023", defaults={"name": name, "curriculum_slot_name": name if category == CourseCategory.ELECTIVE else None, "category": category, "credits": Decimal("3"), "ca_max": ca, "ese_max": ese, "total_max": Decimal("100"), "semester_number": semester_no})
            course.name = name
            course.semester_number = semester_no
            course.ca_max = ca
            course.ese_max = ese
            offering = one(db, CourseOffering, course_id=course.id, academic_year_id=year.id, class_id=assigned_class.id, defaults={"semester_id": semester.id})
            offerings.append(offering)
            professor = professors[0]
            one(db, ProfessorAssignment, professor_id=professor.id, course_offering_id=offering.id)
            one(db, Assessment, course_offering_id=offering.id, name="Internal Assessment", defaults={"assessment_type_id": assessment_type.id, "maximum_marks": Decimal("100"), "raw_maximum": Decimal("100"), "converted_maximum": Decimal("100"), "weightage": Decimal("100"), "published": False})
    active_course_ids = [offering.course_id for offering in offerings]
    old_offering_ids = select(CourseOffering.id).where(CourseOffering.course_id.not_in(active_course_ids))
    db.query(ProfessorAssignment).filter(ProfessorAssignment.course_offering_id.in_(old_offering_ids)).update({ProfessorAssignment.active: False}, synchronize_session=False)
    db.query(CourseOffering).filter(CourseOffering.course_id.not_in(active_course_ids)).update({CourseOffering.active: False}, synchronize_session=False)
    db.query(Course).filter(Course.id.not_in(active_course_ids)).update({Course.active: False}, synchronize_session=False)
    db.commit()
    return {"users": db.scalar(select(__import__('sqlalchemy').func.count()).select_from(User).where(User.is_active.is_(True))), "students": 50, "professors": 10, "admins": 3, "courses": 1}


def main():
    with SessionLocal() as db:
        print(seed(db))


if __name__ == "__main__": main()
