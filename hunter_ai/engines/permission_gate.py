"""
Permission & Approval Gatekeeper
Enforces strict boundaries between automatically allowed actions and actions
that mandate explicit user approval by Arif Alam.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone


class ActionPermissionPolicy:
    # Categories that require explicit approval
    SENSITIVE_ACTIONS = {
        "UPLOAD_ID": {
            "risk_level": "High",
            "description": "Uploading Student ID card, Government ID, Passport or Aadhaar.",
            "requires_approval": True,
        },
        "SHARE_SENSITIVE_INFO": {
            "risk_level": "High",
            "description": "Sharing phone number, residential address, or confidential tax/financial identifiers.",
            "requires_approval": True,
        },
        "CREATE_NEW_ACCOUNT": {
            "risk_level": "Medium",
            "description": "Registering a new account credentials or agreeing to new portal Terms of Service.",
            "requires_approval": True,
        },
        "PASSWORDS_OTP_MFA": {
            "risk_level": "Critical",
            "description": "Supplying password, OTP, 2FA code, or OAuth grant permission.",
            "requires_approval": True,
        },
        "PAYMENTS_OR_FINANCIAL": {
            "risk_level": "Critical",
            "description": "Any transaction involving card details, payment tokens, or billing authorization.",
            "requires_approval": True,
        },
        "LEGAL_BINDING_AGREEMENT": {
            "risk_level": "High",
            "description": "Accepting terms granting IP rights, exclusivity, or legal liability to third parties.",
            "requires_approval": True,
        },
        "PUBLIC_SOCIAL_RELEASE": {
            "risk_level": "Medium",
            "description": "Publishing public LinkedIn posts, social media updates, or making repositories public.",
            "requires_approval": True,
        },
        "FINAL_SUBMISSION": {
            "risk_level": "Medium",
            "description": "Final irreversible submission of hackathon project or competitive proposal.",
            "requires_approval": True,
        },
    }

    # Automatically allowed actions
    SAFE_ACTIONS = {
        "DISCOVERY": "Discovering publicly listed opportunities",
        "ELIGIBILITY_CHECK": "Checking eligibility against local profile",
        "PREPARE_FORM": "Parsing web form and mapping non-sensitive profile fields",
        "FILL_NON_SENSITIVE": "Pre-filling name, email, GitHub, LinkedIn, portfolio, skills",
        "SAVE_DRAFT": "Saving application draft state locally without final binding submit",
        "FREE_NON_BINDING_REGISTRATION": "Submitting free non-binding registrations with pre-authorized accounts",
    }


def evaluate_action_permission(
    action_type: str,
    form_data: Optional[Dict[str, Any]] = None,
    details: str = "",
) -> Dict[str, Any]:
    """
    Evaluates whether an action can proceed automatically or requires creating an ApprovalRequest.
    """
    form_data = form_data or {}
    
    # Check if form requires file upload (e.g. ID card)
    requires_id_upload = any(
        k in form_data.keys() for k in ["student_id", "college_id", "id_card", "govt_id", "id_proof", "document"]
    )
    if requires_id_upload and action_type != "UPLOAD_ID":
        action_type = "UPLOAD_ID"

    # Check if action is sensitive
    if action_type in ActionPermissionPolicy.SENSITIVE_ACTIONS:
        config = ActionPermissionPolicy.SENSITIVE_ACTIONS[action_type]
        return {
            "allowed_automatically": False,
            "requires_approval": True,
            "action_type": action_type,
            "risk_level": config["risk_level"],
            "description": f"{config['description']} {details}".strip(),
            "sensitive_fields": list(form_data.keys()),
        }

    # Safe action
    return {
        "allowed_automatically": True,
        "requires_approval": False,
        "action_type": action_type,
        "risk_level": "Low",
        "description": ActionPermissionPolicy.SAFE_ACTIONS.get(action_type, "Standard automated operation"),
        "sensitive_fields": [],
    }
