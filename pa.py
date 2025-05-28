from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Header
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid
import requests

router = APIRouter()

# In-memory submissions store
_submissions: List[dict] = []

class PARequest(BaseModel):
    provider_npi: str
    patient_name: str
    patient_dob: str
    insurance: str
    member_id: str
    service: str
    diagnosis_code: str
    notes: Optional[str] = None

# ------ Availity Eligibility Integration ------
def get_eligibility_from_availity(access_token: str, coverage_payload: dict):
    url = "https://api.availity.com/availity/v1/coverages"
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        resp = requests.get(url, headers=headers, params=coverage_payload, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        else:
            return {"error": resp.text, "status_code": resp.status_code}
    except Exception as e:
        return {"error": str(e)}

@router.post("/submit", status_code=201)
def submit(
    request: PARequest,
    authorization: Optional[str] = Header(None)
):
    """Provider submits new PA request. Each request gets a unique ID and status history.
    Optionally calls Availity for eligibility if an Authorization header (Bearer token) is present."""
    data = request.dict()
    data["id"] = str(uuid.uuid4())
    data["status"] = "Submitted"
    data["status_history"] = [{
        "status": "Submitted",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }]
    data["documents"] = []
    data["assigned_rep"] = None  # Add this field for assignment

    # --- New: Check for Availity Token ---
    eligibility_response = None
    if authorization and authorization.lower().startswith("bearer "):
        access_token = authorization.split()[1]
        # You can build out this payload with the correct fields for Availity
        coverage_payload = {
            "providerNpi": data["provider_npi"],
            "memberId": data["member_id"],
            "payerId": data["insurance"],   # You might want to map this
            "birthDate": data["patient_dob"]
        }
        eligibility_response = get_eligibility_from_availity(access_token, coverage_payload)
        data["eligibility_response"] = eligibility_response
    else:
        data["eligibility_response"] = "No Availity token provided. Skipped eligibility check."
    
    _submissions.append(data)
    return {"message": "PA request submitted successfully.", "data": data}

@router.get("/list")
def list_submissions():
    """List all PA submissions (for dashboard views)."""
    return {"submissions": _submissions}

@router.post("/update-status")
def update_status(
    submission_id: str = Form(...),
    new_status: str = Form(...),
    notes: Optional[str] = Form(None)
):
    """
    Reps/Admins update PA request status by ID. Adds to status_history and notes.
    """
    for s in _submissions:
        if s["id"] == submission_id:
            s["status"] = new_status
            s["status_history"].append({
                "status": new_status,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
            if notes:
                s.setdefault("notes", "")
                s["notes"] += f"\n[{datetime.utcnow().isoformat()}] {notes}"
            return {"message": "Status updated", "status_history": s["status_history"]}
    raise HTTPException(404, "Submission not found.")

@router.post("/upload-doc")
def upload_doc(
    submission_id: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Attach a document to an existing PA submission.
    """
    for s in _submissions:
        if s["id"] == submission_id:
            s.setdefault("documents", []).append({
                "filename": file.filename,
                "data": file.file.read()  # In-memory; production should use storage!
            })
            return {"message": f"Uploaded {file.filename}"}
    raise HTTPException(404, "Submission not found.")

@router.get("/get")
def get_submission(submission_id: str):
    """Get one submission by ID (for detail/timeline views)."""
    for s in _submissions:
        if s["id"] == submission_id:
            return {"submission": s}
    raise HTTPException(404, "Submission not found.")

@router.post("/assign-rep")
def assign_rep(
    submission_id: str = Form(...),
    assigned_rep: str = Form(...)
):
    for s in _submissions:
        if s["id"] == submission_id:
            s["assigned_rep"] = assigned_rep if assigned_rep != "Unassigned" else None
            return {"message": f"Assigned rep set to {assigned_rep or 'Unassigned'}."}
    raise HTTPException(404, "Submission not found.")
