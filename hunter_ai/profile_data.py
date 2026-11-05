"""
Arif Alam's Verified Professional Profile & Eligibility Constraints
This is the single source of truth for Arif Alam's background.
Never fabricate qualifications, achievements, or employment details.
"""

from typing import Dict, List, Any

USER_PROFILE: Dict[str, Any] = {
    "personal": {
        "full_name": "Arif Alam",
        "email": "iamarifalam@gmail.com",
        "phone": "+91-8954739708",
        "location": {
            "city": "New Delhi",
            "state": "Delhi",
            "country": "India",
            "country_code": "IN",
            "timezone": "Asia/Kolkata",
        },
        "gender": "Male",
        "citizenship": "Indian",
    },
    "professional": {
        "current_title": "AI Engineer",
        "current_company": "Tata Consultancy Services (TCS)",
        "years_of_experience": 4.5,
        "domains": [
            "AI Engineering",
            "Generative AI",
            "Agentic AI",
            "Large Language Models (LLMs)",
            "Retrieval-Augmented Generation (RAG)",
            "Model Context Protocol (MCP)",
            "Agent-to-Agent (A2A)",
            "Software Engineering",
            "Cloud Computing",
            "DevOps / MLOps",
        ],
        "is_working_professional": True,
    },
    "education": {
        "degree_current": {
            "degree": "Master of Business Administration (MBA)",
            "specialization": "Operations and Data Science",
            "institution": "NMIMS (Narsee Monjee Institute of Management Studies)",
            "location": "Mumbai, India",
            "duration": "2025–2027",
            "mode": "Online / Distance Programme",
            # Online/Distance programme - Valid student status for degree-granting screening, no .edu email
            "treat_as_valid_student": True,
            "has_student_email": False,
            "status": "Currently Enrolled",
        },
        "degree_undergrad": {
            "degree": "Bachelor of Technology (B.Tech)",
            "specialization": "Information Technology",
            "institution": "APJ Abdul Kalam Technical University (AKTU)",
            "duration": "2018–2022",
            "status": "Graduated",
        },
    },
    "technical_skills": [
        "Python",
        "FastAPI",
        "Docker",
        "Kubernetes",
        "Terraform",
        "Jenkins",
        "MLflow",
        "Azure",
        "AWS",
        "GCP",
        "Streamlit",
        "LangChain",
        "LangGraph",
        "RAG",
        "LLM Application Development",
        "SQL",
        "Git",
        "REST APIs",
        "Playwright",
        "TypeScript",
    ],
    "projects": [
        {
            "name": "AI Interview Copilot",
            "description": "Real-time intelligent assistant for interview prep with question generation and answer evaluation.",
            "tech_stack": ["Python", "FastAPI", "LangChain", "OpenAI / Claude", "Streamlit"],
        },
        {
            "name": "Semantic Resume Matcher",
            "description": "Vector embedding search tool that scores resume compatibility with job descriptions using semantic similarity.",
            "tech_stack": ["Python", "RAG", "ChromaDB", "FastAPI", "Transformers"],
        },
        {
            "name": "Fraud Detection System",
            "description": "High-throughput machine learning pipeline to identify anomalous financial transactions.",
            "tech_stack": ["Python", "MLflow", "Docker", "Scikit-Learn", "FastAPI"],
        },
        {
            "name": "Predictive Maintenance Forecasting",
            "description": "IoT sensor telemetry analysis for early equipment breakdown warning.",
            "tech_stack": ["Python", "Azure", "Docker", "Kubernetes", "Time Series ML"],
        },
    ],
    "creator": {
        "brand": "Data Science Reality",
        "niche": [
            "Data Science",
            "Artificial Intelligence",
            "Machine Learning",
            "Generative AI",
            "AI Engineering",
            "Agentic AI",
        ],
        "activities": [
            "LinkedIn Content Creation",
            "Technical Education & Tutorials",
            "Community Mentoring",
            "Developer Evangelism",
        ],
        "community": "Data Science Reality WhatsApp Community & Network",
    },
    "links": {
        "linkedin": "https://www.linkedin.com/in/iamarifalam/",
        "github": "https://github.com/iamarifalam",
        "portfolio": "https://iamarifalam.github.io",
        "website": "https://damnreality.websites.co.in",
        "instagram": "https://www.instagram.com/arif.codes",
        "medium": "https://iamarifalam.medium.com",
        "linktree": "https://linktr.ee/iamarifalam",
    },
    # Verified physical shipping profile for Swag Hunter Engine
    "shipping": {
        "recipient_name": "Arif Alam",
        "phone": "+91-8954739708",
        "street": "F-12/21, Jogabai Extension, Batla House",
        "city": "New Delhi",
        "state": "Delhi",
        "postal_code": "110025",
        "country": "India",
        "country_code": "IN",
        "preferred_tshirt_size": "M",
        "waist_size": 32,
        "height": "5'10\"",
        "swag_preference": "ALL_SWAG_MAXIMIZATION",  # Maximize all rewards: Hoodies, T-Shirts, Dev Kits, Hardware, Stickers & Swag packs!
        "delivery_instructions": "Residential address",
        "privacy_rule": "Avoid providing phone number or address where optional on forms",
    },
    # Pre-registered events reported by user (awaiting authenticated email confirmation)
    "pre_registered_events": [
        {
            "name": "Homingo Hack Days Edition 01",
            "category": "Hackathons",
            "status": "USER_REPORTED_REGISTERED",
            "confirmation_evidence": "User-reported registration. Awaiting live Gmail OAuth/IMAP confirmation.",
            "confirmation_identifier": None,
            "registration_date": "2026-10-15",
            "organizer": "Homingo Inc.",
        },
        {
            "name": "Arthaton 2026 AI for Finance Hackathon",
            "category": "Hackathons",
            "status": "USER_REPORTED_REGISTERED",
            "confirmation_evidence": "User-reported registration. Awaiting live Gmail OAuth/IMAP confirmation.",
            "confirmation_identifier": None,
            "registration_date": "2026-10-20",
            "organizer": "Arthaton Global",
        },
    ],
}
