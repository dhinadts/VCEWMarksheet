import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import JSON, Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserType(str, enum.Enum):
    ADMIN = "ADMIN"
    PROFESSOR = "PROFESSOR"
    STUDENT = "STUDENT"


class CourseCategory(str, enum.Enum):
    THEORY = "THEORY"
    PRACTICAL = "PRACTICAL"
    MANDATORY = "MANDATORY"
    CAREER_TRACK = "CAREER_TRACK"
    ELECTIVE = "ELECTIVE"


class UUIDMixin:
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Institution(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "institutions"
    name: Mapped[str] = mapped_column(String(255), unique=True)
    code: Mapped[str] = mapped_column(String(50), unique=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Department(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "departments"
    institution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("institutions.id"))
    name: Mapped[str] = mapped_column(String(255))
    code: Mapped[str] = mapped_column(String(50))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (UniqueConstraint("institution_id", "code"),)


class Programme(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "programmes"
    department_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("departments.id"))
    name: Mapped[str] = mapped_column(String(255))
    degree: Mapped[str] = mapped_column(String(100))
    code: Mapped[str] = mapped_column(String(50))
    regulation: Mapped[str] = mapped_column(String(20))
    duration_semesters: Mapped[int] = mapped_column(Integer, default=8)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (UniqueConstraint("department_id", "code", "regulation"),)


class AcademicYear(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "academic_years"
    name: Mapped[str] = mapped_column(String(20), unique=True)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Semester(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "semesters"
    programme_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("programmes.id"))
    number: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(50))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (UniqueConstraint("programme_id", "number"),)


class User(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "users"
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    user_type: Mapped[UserType] = mapped_column(Enum(UserType, native_enum=False))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Professor(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "professors"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True)
    employee_number: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    department_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("departments.id"))
    designation: Mapped[str] = mapped_column(String(100), default="Assistant Professor")
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Admin(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "admins"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True)
    employee_number: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(255))


class AcademicClass(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "classes"
    code: Mapped[str] = mapped_column(String(100), unique=True)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("academic_years.id"))
    department_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("departments.id"))
    programme_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("programmes.id"))
    semester_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("semesters.id"))
    section: Mapped[str] = mapped_column(String(10))
    batch: Mapped[str] = mapped_column(String(20))
    strength: Mapped[int] = mapped_column(Integer)
    class_advisor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("professors.id"), nullable=True)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)


class Student(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "students"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True)
    register_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    roll_number: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    programme_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("programmes.id"))
    department_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("departments.id"))
    class_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classes.id"))
    admission_year: Mapped[int] = mapped_column(Integer)
    current_semester: Mapped[int] = mapped_column(Integer)
    section: Mapped[str] = mapped_column(String(10))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Course(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "courses"
    programme_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("programmes.id"))
    code: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(255))
    curriculum_slot_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    actual_course_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    actual_course_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    category: Mapped[CourseCategory] = mapped_column(Enum(CourseCategory, native_enum=False))
    credits: Mapped[Decimal] = mapped_column(Numeric(4, 1), default=0)
    ca_max: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    ese_max: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    total_max: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    semester_number: Mapped[int] = mapped_column(Integer)
    regulation: Mapped[str] = mapped_column(String(20))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (UniqueConstraint("programme_id", "code", "regulation"),)


class CourseOffering(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "course_offerings"
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("courses.id"))
    academic_year_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("academic_years.id"))
    semester_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("semesters.id"))
    class_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classes.id"))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (UniqueConstraint("course_id", "academic_year_id", "class_id"),)


class ProfessorAssignment(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "professor_assignments"
    professor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("professors.id"))
    course_offering_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("course_offerings.id"))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (UniqueConstraint("professor_id", "course_offering_id"),)


class AssessmentType(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "assessment_types"
    name: Mapped[str] = mapped_column(String(100), unique=True)
    code: Mapped[str] = mapped_column(String(30), unique=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Assessment(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "assessments"
    course_offering_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("course_offerings.id"))
    assessment_type_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assessment_types.id"))
    name: Mapped[str] = mapped_column(String(100))
    maximum_marks: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    weightage: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    raw_maximum: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    converted_maximum: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    assessment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    published: Mapped[bool] = mapped_column(Boolean, default=False)
    __table_args__ = (UniqueConstraint("course_offering_id", "name"),)


class MarksheetUpload(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "marksheet_uploads"
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id"), index=True)
    assessment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assessments.id"), index=True)
    course_offering_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("course_offerings.id"), index=True)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    source: Mapped[str] = mapped_column(String(30), default="MOBILE_CAMERA")
    original_filename: Mapped[str] = mapped_column(String(255))
    storage_key: Mapped[str] = mapped_column(String(500), unique=True)
    mime_type: Mapped[str] = mapped_column(String(100))
    checksum_sha256: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    size_bytes: Mapped[int] = mapped_column(Integer)
    capture_quality_json: Mapped[dict] = mapped_column(JSON)
    processing_status: Mapped[str] = mapped_column(String(30), default="UPLOADED")
    review_status: Mapped[str] = mapped_column(String(30), default="PENDING")
    client_request_id: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    computerized_storage_key: Mapped[str | None] = mapped_column(String(500), unique=True, nullable=True)
    approved_total: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class OCRJob(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "ocr_jobs"
    marksheet_upload_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("marksheet_uploads.id"), unique=True)
    status: Mapped[str] = mapped_column(String(30), default="QUEUED")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    recognizer_version: Mapped[str | None] = mapped_column(String(255), nullable=True)


class OCRExtraction(UUIDMixin, Base):
    __tablename__ = "ocr_extractions"
    marksheet_upload_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("marksheet_uploads.id"), index=True)
    field_name: Mapped[str] = mapped_column(String(100))
    raw_text: Mapped[str] = mapped_column(String(100))
    numeric_value: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4))
    bounding_box_json: Mapped[dict] = mapped_column(JSON)
    recognizer_version: Mapped[str] = mapped_column(String(255))
    requires_review: Mapped[bool] = mapped_column(Boolean, default=True)
    reviewed_value: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint("marksheet_upload_id", "field_name"),)


class RefreshToken(UUIDMixin, Base):
    __tablename__ = "refresh_tokens"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    jti: Mapped[str] = mapped_column(String(100), unique=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditLog(UUIDMixin, Base):
    __tablename__ = "audit_logs"
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(100))
    entity_type: Mapped[str] = mapped_column(String(100))
    entity_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
