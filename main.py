from fastapi import FastAPI, HTTPException, Depends
from typing import List, Optional
from sqlalchemy import Column, Integer, String, ForeignKey, Table, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session

app = FastAPI()

# ------------------ DATABASE SETUP ------------------
DATABASE_URL = "sqlite:///./data.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ------------------ MODELS ------------------

class_association = Table(
    "class_association", Base.metadata,
    Column("class_id", ForeignKey("classes.id"), primary_key=True),
    Column("student_id", ForeignKey("students.id"), primary_key=True),
)

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    middle_name = Column(String, nullable=True)
    age = Column(Integer)
    city = Column(String)
    classes = relationship("Class", secondary=class_association, back_populates="students")

class Class(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    subject = Column(String)
    students = relationship("Student", secondary=class_association, back_populates="classes")

Base.metadata.create_all(bind=engine)

# ------------------ SCHEMAS ------------------

from pydantic import BaseModel

class StudentCreate(BaseModel):
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    age: int
    city: str

class StudentResponse(StudentCreate):
    id: int
    class Config:
        orm_mode = True

class ClassCreate(BaseModel):
    name: str
    subject: str

class ClassResponse(ClassCreate):
    id: int
    class Config:
        orm_mode = True

# ------------------ ROUTES ------------------

# 1. Create Student
@app.post("/students", response_model=StudentResponse)
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    db_student = Student(**student.dict())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

# 2. Get All Students
@app.get("/students", response_model=List[StudentResponse])
def read_students(db: Session = Depends(get_db)):
    return db.query(Student).all()

# 3. Update Student
@app.put("/students/{student_id}", response_model=StudentResponse)
def update_student(student_id: int, student: StudentCreate, db: Session = Depends(get_db)):
    db_student = db.query(Student).filter(Student.id == student_id).first()
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")
    for key, value in student.dict().items():
        setattr(db_student, key, value)
    db.commit()
    db.refresh(db_student)
    return db_student

# 4. Delete Student
@app.delete("/students/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    db_student = db.query(Student).filter(Student.id == student_id).first()
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")
    db.delete(db_student)
    db.commit()
    return {"message": "Student deleted successfully"}

# 5. Create Class
@app.post("/classes", response_model=ClassResponse)
def create_class(class_data: ClassCreate, db: Session = Depends(get_db)):
    db_class = Class(**class_data.dict())
    db.add(db_class)
    db.commit()
    db.refresh(db_class)
    return db_class

# 6. Get All Classes
@app.get("/classes", response_model=List[ClassResponse])
def get_classes(db: Session = Depends(get_db)):
    return db.query(Class).all()

# 7. Register Student to Class
@app.post("/classes/{class_id}/students/{student_id}")
def register_student_to_class(class_id: int, student_id: int, db: Session = Depends(get_db)):
    class_obj = db.query(Class).filter(Class.id == class_id).first()
    student_obj = db.query(Student).filter(Student.id == student_id).first()

    if not class_obj:
        raise HTTPException(status_code=404, detail="Class not found")
    if not student_obj:
        raise HTTPException(status_code=404, detail="Student not found")
    if student_obj in class_obj.students:
        raise HTTPException(status_code=400, detail="Student already registered to this class")

    class_obj.students.append(student_obj)
    db.commit()
    return {"message": f"Student {student_id} registered to Class {class_id}"}

# 8. List Students in Class
@app.get("/classes/{class_id}/students", response_model=List[StudentResponse])
def list_students_in_class(class_id: int, db: Session = Depends(get_db)):
    class_obj = db.query(Class).filter(Class.id == class_id).first()
    if not class_obj:
        raise HTTPException(status_code=404, detail="Class not found")
    return class_obj.students
# 9. Delete Class
@app.delete("/classes/{class_id}")
def delete_class(class_id: int, db: Session = Depends(get_db)):
    db_class = db.query(Class).filter(Class.id == class_id).first()
    if not db_class:
        raise HTTPException(status_code=404, detail="Class not found")
    db.delete(db_class)
    db.commit()
    return {"message": "Class deleted successfully"}

