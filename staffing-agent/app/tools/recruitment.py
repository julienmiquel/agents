"""Tools for the Staffing and Recruitment Agent."""
from typing import Any
from pathlib import Path

import os
import json

# Load mock database dynamically from mock_data.json
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(CURRENT_DIR, "mock_data.json")

CANDIDATES_DB = []
try:
    with open(JSON_PATH, "r") as f:
        db_data = json.load(f)
        for consultant in db_data.get("consultants", []):
            # Map consultant structure to candidates schema
            email = consultant["name"].lower().replace(" ", ".") + "@example.com"
            role = consultant.get("skills", ["Consultant"])[0] + " Engineer"
            CANDIDATES_DB.append({
                "id": consultant["id"],
                "name": consultant["name"],
                "role": role,
                "experience_years": consultant["experience_years"],
                "skills": consultant["skills"],
                "email": email,
                "location": consultant.get("location", ""),
                "availability": consultant.get("availability", ""),
                "cv_text": consultant.get("cv_text", ""),
            })
except Exception as e:
    # Fallback to simple in-memory mock data if file loading fails
    CANDIDATES_DB = [
        {
            "id": "cand_001",
            "name": "Alice Smith",
            "role": "Senior Python Developer",
            "experience_years": 8,
            "skills": ["Python", "FastAPI", "Google Cloud", "Kubernetes"],
            "email": "alice.smith@example.com",
        },
        {
            "id": "cand_002",
            "name": "Bob Jones",
            "role": "Frontend Engineer",
            "experience_years": 4,
            "skills": ["React", "TypeScript", "CSS", "Tailwind"],
            "email": "bob.jones@example.com",
        },
        {
            "id": "cand_003",
            "name": "Charlie Brown",
            "role": "Data Scientist",
            "experience_years": 6,
            "skills": ["Python", "TensorFlow", "SQL", "BigQuery"],
            "email": "charlie.brown@example.com",
        },
    ]

def search_candidates(query: str, min_experience_years: int = 0) -> list[dict[str, Any]]:
    """Search for candidates in the database matching skills or role.

    Args:
        query: Term or skill to search (e.g., 'Python', 'React', 'Data Scientist').
        min_experience_years: Minimum required years of experience.

    Returns:
        List of matching candidate profile dicts.
    """
    query_lower = query.lower()
    results = []
    for cand in CANDIDATES_DB:
        match_role = query_lower in cand["role"].lower()
        match_skills = any(query_lower in s.lower() for s in cand["skills"])
        match_exp = cand["experience_years"] >= min_experience_years
        
        if (match_role or match_skills) and match_exp:
            results.append(cand)
            
    return results

def evaluate_candidate(candidate_id: str, job_description: str) -> dict[str, Any]:
    """Evaluate a candidate's suitability against a job description.

    Args:
        candidate_id: The ID of the candidate to evaluate (e.g., 'cand_001').
        job_description: The description of the job requirements.

    Returns:
        A dictionary containing evaluation metrics: match score (0-100) and fit summary.
    """
    candidate = next((c for c in CANDIDATES_DB if c["id"] == candidate_id), None)
    if not candidate:
        return {"error": f"Candidate with ID {candidate_id} not found."}

    # Simple heuristic-based mock evaluation
    jd_lower = job_description.lower()
    matched_skills = [s for s in candidate["skills"] if s.lower() in jd_lower]
    score = len(matched_skills) * 25
    score = min(score, 100)
    if not matched_skills:
        score = 40  # Base score if matches role but not exact skills listed

    return {
        "candidate_id": candidate_id,
        "candidate_name": candidate["name"],
        "matched_skills": matched_skills,
        "score": score,
        "fit_status": "Strong Fit" if score >= 75 else "Moderate Fit" if score >= 50 else "Weak Fit",
        "comments": f"Candidate has {candidate['experience_years']} years of experience in matching fields."
    }

def schedule_interview(candidate_id: str, date_time: str) -> str:
    """Schedule an interview with a candidate.

    Args:
        candidate_id: The ID of the candidate to interview.
        date_time: The date and time for the interview (e.g., '2026-05-20 10:00 AM').

    Returns:
        Confirmation message with meeting link.
    """
    candidate = next((c for c in CANDIDATES_DB if c["id"] == candidate_id), None)
    if not candidate:
        return f"Error: Candidate with ID {candidate_id} not found."

    return (
        f"Successfully scheduled interview with {candidate['name']} "
        f"({candidate['email']}) for {date_time}. "
        f"Google Meet link: https://meet.google.com/abc-defg-hij"
    )



def get_open_positions(sector: str) -> list:
    """Returns a list of open project requirements from the CRM for a given sector.
    
    Args:
        sector: The business sector (e.g., 'Automotive', 'IT').
    """
    kb_path = Path(__file__).parent / "mock_data.json"
    try:
        with open(kb_path, "r") as f:
            data = json.load(f)
            positions = data.get("open_positions", [])
            return [p for p in positions if p.get("sector").lower() == sector.lower()]
    except Exception as e:
        return [{"error": f"Error loading data: {e}"}]

def search_consultant_database(skills: list, location: str) -> list:
    """Queries the Talent Pool for available consultants based on skills and location.
    
    Args:
        skills: A list of required skills.
        location: The desired location.
    """
    kb_path = Path(__file__).parent / "mock_data.json"
    try:
        with open(kb_path, "r") as f:
            data = json.load(f)
            consultants = data.get("consultants", [])
            results = []
            for c in consultants:
                if c.get("location").lower() == location.lower():
                    c_skills = [s.lower() for s in c.get("skills", [])]
                    overlap = set([s.lower() for s in skills]).intersection(set(c_skills))
                    if overlap:
                        results.append(c)
            return results
    except Exception as e:
        return [{"error": f"Error loading data: {e}"}]

def evaluate_match(cv_text: str, job_description: str) -> dict:
    """Performs a semantic analysis to provide a matching score (0-100%).
    
    Args:
        cv_text: The text of the candidate's CV.
        job_description: The job description.
    """
    score = 85
    if "C++" in cv_text and "Automotive" in job_description:
        score = 95
    return {"match_score": f"{score}%", "summary": "Strong match based on skills and sector experience."}

def schedule_hr_qualification(candidate_id: str, recruiter_name: str) -> dict:
    """Simulates booking a slot in the recruiter's calendar for an HR qualification.
    
    Args:
        candidate_id: The ID of the candidate.
        recruiter_name: The name of the recruiter.
    """
    return {
        "status": "Success",
        "message": f"HR qualification scheduled for candidate {candidate_id} with recruiter {recruiter_name}.",
        "date": "2026-04-15T10:00:00Z"
    }