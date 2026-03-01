from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict
from typing import List
import datetime
import os
import uvicorn

DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Student(Base):
    __tablename__ = "students_py"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    math = Column(Float, nullable=False)
    english = Column(Float, nullable=False)
    science = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class StudentCreate(BaseModel):
    name: str
    math: float
    english: float
    science: float

class StudentResponse(StudentCreate):
    id: int
    average: float
    mathStatus: str
    englishStatus: str
    scienceStatus: str
    overallStatus: str
    model_config = ConfigDict(from_attributes=True)

def analyze_grade(grade: float) -> str:
    if grade < 50: return "Needs Improvement"
    if grade < 70: return "Average"
    return "Good"

def calculate_analysis(student: Student):
    avg = (student.math + student.english + student.science) / 3
    return {
        "id": student.id, "name": student.name, "math": student.math,
        "english": student.english, "science": student.science,
        "average": round(avg, 2),
        "mathStatus": analyze_grade(student.math),
        "englishStatus": analyze_grade(student.english),
        "scienceStatus": analyze_grade(student.science),
        "overallStatus": "At Risk" if avg < 60 else "Stable"
    }

@app.get("/api/students", response_model=List[StudentResponse])
def list_students(db: Session = Depends(get_db)):
    students = db.query(Student).all()
    return [calculate_analysis(s) for s in students]

@app.post("/api/students", response_model=StudentResponse)
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    db_student = Student(**student.model_dump())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return calculate_analysis(db_student)

@app.delete("/api/students/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    db_student = db.query(Student).filter(Student.id == student_id).first()
    if not db_student: raise HTTPException(status_code=404, detail="Student not found")
    db.delete(db_student)
    db.commit()
    return {"message": "Deleted"}

# Static file serving
dist_path = "dist/public"
if os.path.exists(dist_path):
    assets_path = os.path.join(dist_path, "assets")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")
    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        if full_path.startswith("api/"): raise HTTPException(status_code=404)
        file_path = os.path.join(dist_path, full_path)
        if full_path and os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(dist_path, "index.html"))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
