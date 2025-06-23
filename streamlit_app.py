import os
import streamlit as st
import requests
import pandas as pd
from datetime import datetime

API_BASE = os.getenv("API_BASE", "https://epochpa-app.onrender.com")
LOGO_PATH = "epochpa_logo.png"

st.set_page_config(page_title="EpochPA", page_icon="🏥", layout="wide")

def show_logo():
    try:
        st.image(LOGO_PATH, width=180)
    except Exception:
        st.write(":hospital:")

# SIDEBAR NAVIGATION
st.sidebar.title("EpochPA")
show_logo()
st.sidebar.subheader("Authentication")

if "auth_page" not in st.session_state:
    st.session_state["auth_page"] = "🔐 Login Page"
if "dash_page" not in st.session_state:
    st.session_state["dash_page"] = "🛠️ Admin Dashboard"

if "logged_provider" not in st.session_state:
    st.session_state.logged_provider = False
    st.session_state.logged_rep = False
    st.session_state.logged_admin = False
    st.session_state.email = None
    st.session_state.role = None
    st.session_state.username = None
    st.session_state.rep_last_seen = dict()

auth_pages = ["🔐 Login Page", "📝 Register Page", "🔒 Confirm Email"]
auth_page = st.sidebar.radio(
    "Go to:",
    auth_pages,
    index=auth_pages.index(st.session_state["auth_page"]),
    key="auth_nav"
)

dash_pages = ["👨‍⚕️ Provider Dashboard", "👥 Rep Dashboard", "🛠️ Admin Dashboard"]
dash_page = st.sidebar.radio(
    "Go to:",
    dash_pages,
    index=dash_pages.index(st.session_state["dash_page"]),
    key="dash_nav"
)


def show_status_timeline(status_history):
    st.markdown("**Status Timeline:**")
    for item in status_history:
        st.write(f"- `{item['timestamp']}` — **{item['status']}**")

def compute_turnaround(sub):
    sh = sub.get("status_history", [])
    approved = [h for h in sh if h["status"] in ["Approved", "Denied"]]
    if not approved:
        return None
    start = pd.to_datetime(sh[0]["timestamp"])
    end = pd.to_datetime(approved[-1]["timestamp"])
    return (end - start).total_seconds() / 3600

def status_count(subs):
    return pd.Series([s["status"] for s in subs]).value_counts() if subs else pd.Series()

def show_register():
    show_logo()
    st.title("📝 EpochPA Registration")
    with st.form("register_form"):
        form_role = st.selectbox("Select Role", ["provider", "rep"], key="form_role")
        form_username = st.text_input("Username (will be your login)", key="form_username")
        form_email = st.text_input("Email", key="form_email")
        form_pwd = st.text_input("Password", type="password", key="form_pwd")
        form_pwd2 = st.text_input("Confirm Password", type="password", key="form_pwd2")
        submit = st.form_submit_button("Sign Up")

        if submit:
            if form_pwd != form_pwd2:
                st.error("Passwords must match")
            else:
                payload = {
                    "email": form_email,
                    "password": form_pwd,
                    "role": form_role,
                    "username": form_username
                }
                try:
                    resp = requests.post(f"{API_BASE}/auth/register", json=payload)
                    if resp.status_code == 201:
                        st.success("Registration accepted — check your email to confirm.")
                    else:
                        try:
                            st.error(f"Registration failed: {resp.json()}")
                        except Exception:
                            st.error(f"Registration failed: {resp.text}")
                except Exception as e:
                    st.error(f"Request error: {e}")

def show_confirm():
    show_logo()
    st.title("🔒 Confirm Email")
    token = st.text_input("Confirmation Token")
    if st.button("Confirm"):
        resp = requests.post(f"{API_BASE}/auth/confirm", json={"token": token})
        if resp.status_code == 200:
            st.success("Email confirmed! You can now log in.")
        else:
            st.error(f"Confirmation failed: {resp.json()}")

def show_login():
    show_logo()
    st.title("🔐 EpochPA Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    role = st.selectbox("Role", ["provider", "rep", "admin"])
    if st.button("Login"):
        try:
            payload = {"email": email, "password": password}
            resp = requests.post(f"{API_BASE}/auth/login", json=payload)
            if resp.status_code == 200:
                user_data = resp.json().get("user", {})
                st.session_state.email = user_data.get("email")
                st.session_state.role = user_data.get("role")
                st.session_state.username = user_data.get("email")
                st.session_state.logged_provider = user_data.get("role") == "provider"
                st.session_state.logged_rep = user_data.get("role") == "rep"
                st.session_state.logged_admin = user_data.get("role") == "admin"
                st.success(f"Logged in as {user_data.get('role')}.")
            else:
                st.error("Login failed. Please check your credentials.")
        except Exception as e:
            st.error(f"Request error: {e}")

    # <-- This is now outside the if and except blocks!
    st.write("---")
    if st.button("Register Now"):
        st.session_state["auth_page"] = "📝 Register Page"
        st.rerun()




def show_provider():
    show_logo()
    if not st.session_state.logged_provider:
        st.warning("Please log in as provider first.")
        return

    st.title("👨‍⚕️ Provider Dashboard")
    st.header("Submit a New PA Request")
    provider_npi = st.session_state.username

    with st.form("submit_pa_form", clear_on_submit=True):
        patient_name = st.text_input("Patient Name", "")
        patient_dob = st.date_input("Patient DOB")
        insurance = st.text_input("Insurance/Payer ID", "")
        member_id = st.text_input("Member ID", "")
        service = st.text_input("Requested Service", "")
        diagnosis_code = st.text_input("Diagnosis Code", "")
        notes = st.text_area("Clinical Notes (optional)", "")
        submitted = st.form_submit_button("Submit Request")

        if submitted:
            payload = {
                "provider_npi": provider_npi,
                "patient_name": patient_name,
                "patient_dob": patient_dob.strftime("%Y-%m-%d"),
                "insurance": insurance,
                "member_id": member_id,
                "service": service,
                "diagnosis_code": diagnosis_code,
                "notes": notes
            }
            try:
                resp = requests.post(f"{API_BASE}/submit", json=payload)
                if resp.status_code == 201:
                    st.success("PA request submitted successfully.")
                    st.rerun()
                else:
                    st.error(f"Failed to submit PA request: {resp.text}")
            except Exception as e:
                st.error(f"Request error: {e}")

    st.markdown("---")
    st.subheader("Your PA Analytics")
    try:
        headers = {"Authorization": f"Bearer demo-token"}
        resp = requests.get(f"{API_BASE}/list", headers=headers)
        submissions = resp.json().get("submissions", [])
    except Exception as e:
        st.error(f"Error loading submissions: {e}")
        return

    my_submissions = [s for s in submissions if s["provider_npi"] == provider_npi]
    if not my_submissions:
        st.info("No PA requests submitted yet.")
        return

    status_counts = status_count(my_submissions)
    completed = [s for s in my_submissions if s["status"] in ["Approved", "Denied"]]
    avg_turn = pd.Series([compute_turnaround(s) for s in completed if compute_turnaround(s) is not None]).mean()
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Requests", len(my_submissions))
    col2.metric("Completed", len(completed))
    col3.metric("Avg Turnaround (hrs)", f"{avg_turn:.1f}" if avg_turn else "N/A")
    st.bar_chart(status_counts)
    st.markdown("---")
    for sub in my_submissions:
        st.markdown(f"### Patient: {sub['patient_name']}  \nSubmission ID: `{sub['id']}`")
        st.write(f"**Current Status:** {sub['status']}")
        show_status_timeline(sub["status_history"])
        notes = sub.get("notes")
        if notes:
            st.subheader("📝 Notes")
            st.write(notes)
        st.subheader("📎 Upload Supporting Documents")
        files = st.file_uploader(f"Select files for {sub['id']}", accept_multiple_files=True, key=f"file_{sub['id']}")
        if st.button(f"Upload Documents for {sub['id']}", key=f"upload_{sub['id']}") and files:
            for f in files:
                files_payload = {"file": (f.name, f.getvalue())}
                data = {"submission_id": sub['id']}
                resp = requests.post(f"{API_BASE}/upload-doc", files=files_payload, data=data)
                if resp.status_code == 200:
                    st.success(f"Uploaded {f.name}")
                else:
                    st.error(f"Failed to upload {f.name}: {resp.text}")
        st.subheader("Eligibility Verification (for this PA request)")
        st.write(f"Checked: {sub.get('eligibility_checked', False)}")
        st.write(f"Method: {sub.get('eligibility_method', '')}")
        st.write(f"Notes: {sub.get('eligibility_notes', '')}")
        evidence = sub.get("eligibility_evidence", [])
        if evidence:
            st.write("Eligibility Documents:")
            for doc in evidence:
                st.write(f"- {doc.get('filename', '')}")
        st.write("---")

    if st.button("Download My PA Requests (CSV)"):
        df = pd.DataFrame(my_submissions)
        df.to_csv("my_pas.csv", index=False)
        with open("my_pas.csv", "rb") as f:
            st.download_button("Download CSV", f, file_name="my_pas.csv")
    if st.button("Download My PA Requests (Excel)"):
        df = pd.DataFrame(my_submissions)
        df.to_excel("my_pas.xlsx", index=False)
        with open("my_pas.xlsx", "rb") as f:
            st.download_button("Download Excel", f, file_name="my_pas.xlsx")

def show_rep():
    show_logo()
    if not st.session_state.logged_rep:
        st.warning("Please log in as rep first.")
        return
    st.title("👥 Rep Dashboard")
    username = st.session_state.username
    try:
        resp = requests.get(f"{API_BASE}/list")
        submissions = resp.json().get("submissions", [])
    except Exception as e:
        st.error(f"Error loading submissions: {e}")
        return
    my_submissions = [s for s in submissions if s.get("assigned_rep") == username]
    last_seen = st.session_state.rep_last_seen.get(username)
    new_since = []
    if last_seen:
        last_seen_dt = pd.to_datetime(last_seen)
        new_since = [s["id"] for s in my_submissions if pd.to_datetime(s["status_history"][0]["timestamp"]) > last_seen_dt]
    completed = [s for s in my_submissions if s["status"] in ["Approved", "Denied"]]
    avg_turn = pd.Series([compute_turnaround(s) for s in completed if compute_turnaround(s) is not None]).mean()
    status_counts = status_count(my_submissions)
    col1, col2, col3 = st.columns(3)
    col1.metric("Assigned", len(my_submissions))
    col2.metric("Completed", len(completed))
    col3.metric("Avg Turnaround (hrs)", f"{avg_turn:.1f}" if avg_turn else "N/A")
    st.bar_chart(status_counts)
    st.markdown("---")
    if my_submissions:
        st.subheader("Bulk Status Update")
        options = {f"{s['patient_name']} ({s['id']})": s['id'] for s in my_submissions}
        selected_ids = st.multiselect("Select PA requests", list(options.keys()))
        if selected_ids:
            new_status = st.selectbox("Bulk Status", ["Submitted", "In Review", "Approved", "Denied"], key="bulk_status")
            notes = st.text_area("Bulk Notes", key="bulk_notes")
            if st.button("Update Selected"):
                for sel in selected_ids:
                    pa_id = options[sel]
                    resp = requests.post(
                        f"{API_BASE}/update-status",
                        data={"submission_id": pa_id, "new_status": new_status, "notes": notes}
                    )
                st.success(f"Updated {len(selected_ids)} requests.")
                st.rerun()
        st.markdown("---")
    for sub in my_submissions:
        is_new = sub["id"] in new_since
        sub_title = f"#### Submission ID: `{sub['id']}` | Patient: {sub['patient_name']}"
        if is_new:
            sub_title += "  \n:orange[NEW Assignment!]"
        st.markdown(sub_title)
        st.write(f"**Provider NPI:** {sub['provider_npi']}")
        st.write(f"**Current Status:** {sub['status']}")
        show_status_timeline(sub["status_history"])
        st.markdown("#### Manual Eligibility Update")
        eligibility_checked = sub.get("eligibility_checked", False)
        eligibility_method = sub.get("eligibility_method", "")
        eligibility_notes = sub.get("eligibility_notes", "")
        eligibility_evidence = sub.get("eligibility_evidence", [])
        col1, col2 = st.columns([1, 1])
        with col1:
            checked = st.checkbox("Eligibility Checked?", value=eligibility_checked, key=f"checked_{sub['id']}")
            method = st.selectbox(
                "Eligibility Method",
                ["", "Availity", "Phone", "Fax", "Online Portal", "Other"],
                index=["", "Availity", "Phone", "Fax", "Online Portal", "Other"].index(eligibility_method) if eligibility_method in ["Availity", "Phone", "Fax", "Online Portal", "Other"] else 0,
                key=f"method_{sub['id']}"
            )
        with col2:
            notes = st.text_area("Eligibility Notes", value=eligibility_notes, height=80, key=f"notes_{sub['id']}")
        uploaded_files = st.file_uploader(
            "Upload Eligibility Evidence",
            accept_multiple_files=True,
            key=f"evidence_{sub['id']}"
        )
        if st.button("Save Eligibility Info", key=f"save_elig_{sub['id']}"):
            payload = {
                "submission_id": sub["id"],
                "eligibility_checked": checked,
                "eligibility_method": method,
                "eligibility_notes": notes,
            }
            for file in uploaded_files:
                files = {"file": (file.name, file.getvalue())}
                data = {"submission_id": sub["id"]}
                resp = requests.post(f"{API_BASE}/upload-doc", files=files, data=data)
                if resp.status_code == 200:
                    st.success(f"Uploaded {file.name}")
                else:
                    st.error(f"Failed to upload {file.name}: {resp.text}")
            resp = requests.post(f"{API_BASE}/update-eligibility", json=payload)
            if resp.status_code == 200:
                st.success("Eligibility info updated!")
            else:
                st.error(f"Update failed: {resp.text}")
        if eligibility_evidence:
            st.write("Uploaded Eligibility Documents:")
            for doc in eligibility_evidence:
                st.write(f"- {doc['filename']}")
        st.write("---")
        new_status = st.selectbox(
            f"Update status for {sub['id']}",
            ["Submitted", "In Review", "Approved", "Denied"],
            index=["Submitted", "In Review", "Approved", "Denied"].index(sub["status"]) if sub["status"] in ["Submitted", "In Review", "Approved", "Denied"] else 0,
            key=f"status_{sub['id']}"
        )
        notes = st.text_input(f"Optional note for {sub['id']}", key=f"note_{sub['id']}")
        if st.button(f"Update Status for {sub['id']}", key=f"update_{sub['id']}"):
            resp = requests.post(
                f"{API_BASE}/update-status",
                data={"submission_id": sub['id'], "new_status": new_status, "notes": notes}
            )
            if resp.status_code == 200:
                st.success("Status updated!")
                st.rerun()
            else:
                st.error("Failed to update status.")
        st.write("---")
    if my_submissions:
        if st.button("Download My PA Requests (CSV)"):
            df = pd.DataFrame(my_submissions)
            df.to_csv(f"rep_{username}_pas.csv", index=False)
            with open(f"rep_{username}_pas.csv", "rb") as f:
                st.download_button("Download CSV", f, file_name=f"rep_{username}_pas.csv")
        if st.button("Download My PA Requests (Excel)"):
            df = pd.DataFrame(my_submissions)
            df.to_excel(f"rep_{username}_pas.xlsx", index=False)
            with open(f"rep_{username}_pas.xlsx", "rb") as f:
                st.download_button("Download Excel", f, file_name=f"rep_{username}_pas.xlsx")

def show_admin():
    show_logo()
    if not st.session_state.logged_admin:
        st.warning("Please log in as admin first.")
        return
    st.title("🛠️ Admin Dashboard")
    try:
        resp = requests.get(f"{API_BASE}/list")
        submissions = resp.json().get("submissions", [])
    except Exception as e:
        st.error(f"Error loading submissions: {e}")
        return
    df = pd.DataFrame(submissions)
    st.subheader("📊 PA Analytics Snapshot")
    total = len(df)
    by_status = df["status"].value_counts() if "status" in df else pd.Series()
    by_rep = df["assigned_rep"].value_counts() if "assigned_rep" in df else pd.Series()
    by_provider = df["provider_npi"].value_counts() if "provider_npi" in df else pd.Series()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total PA Requests", total)
    col2.metric("Submitted", int(by_status.get("Submitted", 0)))
    col3.metric("In Review", int(by_status.get("In Review", 0)))
    col4.metric("Approved/Denied", int(by_status.get("Approved", 0)) + int(by_status.get("Denied", 0)))
    st.markdown("#### PAs by Rep")
    st.bar_chart(by_rep)
    st.markdown("#### PAs by Provider")
    st.bar_chart(by_provider)

    def get_turnaround(row):
        times = [x for x in row.get("status_history", []) if x["status"] in ["Approved", "Denied"]]
        if not times:
            return None
        start = pd.to_datetime(row["status_history"][0]["timestamp"])
        end = pd.to_datetime(times[-1]["timestamp"])
        return (end - start).total_seconds() / 3600

    if len(df) and "status_history" in df.columns:
        df["turnaround_hours"] = df.apply(get_turnaround, axis=1)
        avg_turn = df["turnaround_hours"].dropna().mean()
        st.metric("Avg Turnaround (hrs)", f"{avg_turn:.2f}" if pd.notnull(avg_turn) else "N/A")

    st.markdown("---")
    all_reps = sorted(set(s.get("assigned_rep", "") for s in submissions if s.get("assigned_rep")))
    all_providers = sorted(set(s.get("provider_npi", "") for s in submissions))
    all_statuses = sorted(set(s.get("status", "") for s in submissions))
    st.sidebar.header("Admin Filters")
    selected_rep = st.sidebar.selectbox("Filter by Rep", ["All"] + all_reps, key="admin_filter_rep")
    selected_provider = st.sidebar.selectbox("Filter by Provider NPI", ["All"] + all_providers, key="admin_filter_provider")
    selected_status = st.sidebar.selectbox("Filter by Status", ["All"] + all_statuses, key="admin_filter_status")
    filtered_subs = submissions
    if selected_rep != "All":
        filtered_subs = [s for s in filtered_subs if s.get("assigned_rep") == selected_rep]
    if selected_provider != "All":
        filtered_subs = [s for s in filtered_subs if s.get("provider_npi") == selected_provider]
    if selected_status != "All":
        filtered_subs = [s for s in filtered_subs if s.get("status") == selected_status]
    if st.button("📥 Download All PA Data as Excel"):
        df = pd.DataFrame(filtered_subs)
        df.to_excel("PA_Requests.xlsx", index=False)
        with open("PA_Requests.xlsx", "rb") as f:
            st.download_button("Download Excel", f, file_name="PA_Requests.xlsx")
    st.markdown("## All PA Requests")
    status_choices = ["Submitted", "In Review", "Approved", "Denied"]
    rep_choices = ["Unassigned"] + all_reps
    for sub in filtered_subs:
        st.markdown(f"#### Submission ID: `{sub['id']}` | Patient: {sub['patient_name']}")
        st.write(f"**Provider NPI:** {sub['provider_npi']} | **Assigned Rep:** {sub.get('assigned_rep','Unassigned')}")
        st.write(f"**Current Status:** {sub['status']}")
        show_status_timeline(sub["status_history"])
        new_rep = st.selectbox(
            f"Assign Rep for {sub['id']}",
            rep_choices,
            index=rep_choices.index(sub.get("assigned_rep") or "Unassigned"),
            key=f"assign_{sub['id']}"
        )
        if st.button(f"Update Assignment for {sub['id']}", key=f"assignbtn_{sub['id']}"):
            data = {"submission_id": sub['id'], "assigned_rep": new_rep if new_rep != "Unassigned" else ""}
            resp = requests.post(f"{API_BASE}/assign-rep", data=data)
            if resp.status_code == 200:
                st.success(f"Assigned to {new_rep}")
                st.rerun()
            else:
                st.error(f"Assignment failed: {resp.text}")
        st.markdown("#### Manual Eligibility Update")
        eligibility_checked = sub.get("eligibility_checked", False)
        eligibility_method = sub.get("eligibility_method", "")
        eligibility_notes = sub.get("eligibility_notes", "")
        eligibility_evidence = sub.get("eligibility_evidence", [])
        col1, col2 = st.columns([1, 1])
        with col1:
            checked = st.checkbox("Eligibility Checked?", value=eligibility_checked, key=f"admin_checked_{sub['id']}")
            method = st.selectbox(
                "Eligibility Method",
                ["", "Availity", "Phone", "Fax", "Online Portal", "Other"],
                index=["", "Availity", "Phone", "Fax", "Online Portal", "Other"].index(eligibility_method) if eligibility_method in ["Availity", "Phone", "Fax", "Online Portal", "Other"] else 0,
                key=f"admin_method_{sub['id']}"
            )
        with col2:
            notes = st.text_area("Eligibility Notes", value=eligibility_notes, height=80, key=f"admin_notes_{sub['id']}")
        uploaded_files = st.file_uploader(
            "Upload Eligibility Evidence",
            accept_multiple_files=True,
            key=f"admin_evidence_{sub['id']}"
        )
        if st.button("Save Eligibility Info", key=f"admin_save_elig_{sub['id']}"):
            payload = {
                "submission_id": sub["id"],
                "eligibility_checked": checked,
                "eligibility_method": method,
                "eligibility_notes": notes,
            }
            for file in uploaded_files:
                files = {"file": (file.name, file.getvalue())}
                data = {"submission_id": sub["id"]}
                resp = requests.post(f"{API_BASE}/upload-doc", files=files, data=data)
                if resp.status_code == 200:
                    st.success(f"Uploaded {file.name}")
                else:
                    st.error(f"Failed to upload {file.name}: {resp.text}")
            resp = requests.post(f"{API_BASE}/update-eligibility", json=payload)
            if resp.status_code == 200:
                st.success("Eligibility info updated!")
            else:
                st.error(f"Update failed: {resp.text}")
        if eligibility_evidence:
            st.write("Uploaded Eligibility Documents:")
            for doc in eligibility_evidence:
                st.write(f"- {doc['filename']}")
        st.write("---")
        new_status = st.selectbox(
            f"Update status for {sub['id']}",
            status_choices,
            index=status_choices.index(sub["status"]) if sub["status"] in status_choices else 0,
            key=f"admin_status_{sub['id']}"
        )
        notes = st.text_area(f"Admin notes for {sub['id']}", value=sub.get("admin_notes", ""), key=f"admin_note_{sub['id']}")
        if st.button(f"Update Status for {sub['id']}", key=f"admin_update_{sub['id']}"):
            resp = requests.post(
                f"{API_BASE}/update-status",
                data={"submission_id": sub['id'], "new_status": new_status, "notes": notes}
            )
            if resp.status_code == 200:
                st.success("Status updated!")
                st.rerun()
            else:
                st.error("Failed to update status.")
        st.write("---")
    st.info("You can filter, assign, and update PA requests for full admin control. Download Excel for offline reporting.")

# ROUTING: Render correct page
if st.session_state["auth_page"] == "🔐 Login Page":
    show_login()
elif st.session_state["auth_page"] == "📝 Register Page":
    show_register()
elif st.session_state["auth_page"] == "🔒 Confirm Email":
    show_confirm()

if st.session_state.get("logged_provider"):
    show_provider()
elif st.session_state.get("logged_rep"):
    show_rep()
elif st.session_state.get("logged_admin"):
    show_admin()
