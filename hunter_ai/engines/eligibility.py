"""
Eligibility Engine
Compares opportunity terms and requirements directly against Arif Alam's profile:
- Country: India (verified)
- Current Role: AI Engineer at TCS (4.5 years exp)
- Student Status: NMIMS Mumbai MBA (Distance/Online) - TREATED AS VALID STUDENT STATUS
- Skills: Python, FastAPI, Docker, K8s, RAG, GenAI, LangGraph, etc.
- Content Creator: Data Science Reality

Classification:
- Eligible: Verified match on all known requirements
- Likely eligible: Meets general criteria with minor unverified details
- Eligibility unclear: Official terms ambiguous or missing country/role restrictions
- Not eligible: Explicitly restricted (e.g. US Citizens only, Undergrads only, Under 18 only)
"""

from typing import Dict, Any, List, Tuple
from datetime import datetime
from hunter_ai.profile_data import USER_PROFILE


def evaluate_eligibility(
    opportunity_data: Dict[str, Any],
    user_profile: Dict[str, Any] = USER_PROFILE,
) -> Tuple[str, List[str]]:
    """
    Evaluates whether Arif Alam is eligible for an opportunity.
    Returns (classification_label, list_of_reasons).
    """
    reasons: List[str] = []
    flags_ineligible: List[str] = []
    flags_unclear: List[str] = []
    flags_eligible: List[str] = []

    target_countries = opportunity_data.get("country", "Global")
    category = opportunity_data.get("category", "")
    req_skills = [s.lower() for s in opportunity_data.get("required_skills", [])]
    terms_text = (opportunity_data.get("official_terms_text", "") + " " + opportunity_data.get("description", "")).lower()

    # 1. Country & Geographic Check
    user_country = user_profile["personal"]["location"]["country"].lower()
    user_country_code = user_profile["personal"]["location"]["country_code"].lower()

    if isinstance(target_countries, str):
        target_countries_list = [c.strip().lower() for c in target_countries.split(",")]
    else:
        target_countries_list = [str(c).lower() for c in target_countries]

    is_global = any(c in ["global", "worldwide", "international", "all"] for c in target_countries_list)
    is_india_listed = any(c in ["india", "in", "apac", "asia", "south asia"] for c in target_countries_list)

    if not is_global and not is_india_listed:
        # Check if explicitly US/EU only
        us_only_terms = ["us only", "u.s. only", "united states residents only", "legal residents of us", "50 united states"]
        if any(term in terms_text for term in us_only_terms):
            flags_ineligible.append("Geographic restriction: Restricted to US residents only (India excluded).")
        else:
            flags_unclear.append(f"Geographic scope '{target_countries}' does not explicitly confirm Indian participants.")
    else:
        flags_eligible.append("Geographic match: Open to participants from India / Global.")

    # 2. Student Status Evaluation
    degree_info = user_profile.get("education", {}).get("degree_current", {})
    has_student_email = degree_info.get("has_student_email", False)
    nmims_student_status = degree_info.get("treat_as_valid_student", False)
    
    requires_student = any(k in terms_text for k in [
        "must be a student", "currently enrolled student", "enrolled in a university",
        "student developer", "student id required", "college students only", "university students"
    ]) or category in ["Student Benefits"]

    requires_edu_email = any(k in terms_text for k in [
        ".edu email required", "school-issued email required", "must have a .edu email address"
    ])

    requires_undergrad_only = any(k in terms_text for k in [
        "undergraduate students only", "undergrads only", "high school only", "k-12 students"
    ])

    if requires_undergrad_only:
        flags_ineligible.append("Restricted to undergraduate or high school students only; Arif is an experienced professional.")
    elif requires_edu_email and not has_student_email:
        flags_ineligible.append("Requires university .edu/academic email; Arif does not have a student email.")
    elif requires_student:
        if nmims_student_status:
            flags_eligible.append("Student status: Enrolled in NMIMS Mumbai MBA qualifies for general student screening.")
        else:
            flags_unclear.append("Student status required; no verified student email on file.")

    # 3. Working Professional / Experience Evaluation
    user_exp = user_profile["professional"]["years_of_experience"]
    user_title = user_profile["professional"]["current_title"]

    requires_professional = any(k in terms_text for k in ["working professional", "developers with experience", "industry professionals"])
    if requires_professional:
        flags_eligible.append(f"Professional status match: Currently working as {user_title} at TCS with {user_exp} years experience.")

    # Check maximum experience limits
    if "less than 2 years of experience" in terms_text or "0-2 years experience" in terms_text:
        flags_ineligible.append("Requires 0-2 years experience; Arif has ~4.5 years professional experience.")

    # 4. Technical Skills Match
    user_skills = set(s.lower() for s in user_profile.get("technical_skills", []))
    if req_skills:
        matched_skills = [s for s in req_skills if any(us in s or s in us for us in user_skills)]
        if matched_skills:
            flags_eligible.append(f"Skills match: Qualified in {', '.join(matched_skills[:4])}.")
        else:
            flags_unclear.append(f"Requires specific skills: {', '.join(req_skills[:3])}; profile may need alignment.")
    else:
        # Default skills for AI/ML/Software
        flags_eligible.append("Broad skill domain match: AI Engineering, Python, Cloud, LLMs.")

    # 5. Content Creator Match (if creator program)
    if category in ["Creator Programs"] or "ambassador" in terms_text or "creator" in terms_text:
        creator_brand = user_profile["creator"]["brand"]
        flags_eligible.append(f"Creator profile match: Active content creator under '{creator_brand}' (AI/Data Science community).")

    # 6. Deadlines Check
    reg_deadline_str = opportunity_data.get("registration_deadline")
    if reg_deadline_str:
        try:
            # Simple check if deadline has passed
            dl = datetime.fromisoformat(reg_deadline_str.replace("Z", "+00:00"))
            if dl < datetime.now(dl.tzinfo):
                flags_ineligible.append(f"Registration deadline has passed ({reg_deadline_str}).")
        except Exception:
            pass

    # Synthesis into Classification
    if flags_ineligible:
        classification = "Not eligible"
        reasons = flags_ineligible + flags_unclear
    elif flags_unclear and not flags_eligible:
        classification = "Eligibility unclear"
        reasons = flags_unclear
    elif flags_unclear and flags_eligible:
        classification = "Likely eligible"
        reasons = flags_eligible + flags_unclear
    else:
        classification = "Eligible"
        reasons = flags_eligible

    return classification, reasons
