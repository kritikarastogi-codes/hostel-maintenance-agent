from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from main import understand_complaint, get_priority, get_team

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Complaint(BaseModel):
    student: str
    block: str
    room: str
    problem: str


@app.get("/")
def home():
    return {
        "message": "Hostel Maintenance Agent is running"
    }


@app.post("/complaints")
def create_complaint(complaint: Complaint):

    ai_data = understand_complaint(complaint.problem)

    category = ai_data["category"]
    safety = ai_data["safety"]
    severity = ai_data["severity"]

    priority = get_priority(
        category,
        complaint.problem,
        safety,
        severity
    )

    team = get_team(category)

    return {
        "student": complaint.student,
        "block": complaint.block,
        "room": complaint.room,
        "problem": complaint.problem,
        "category": category,
        "safety": safety,
        "severity": severity,
        "priority": priority,
        "team": team,
        "status": "Pending"
    }