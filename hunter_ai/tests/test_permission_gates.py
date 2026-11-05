"""
Tests for Permission & Approval Gatekeeper
"""

import pytest
from hunter_ai.engines.permission_gate import evaluate_action_permission


def test_safe_operations_allowed_automatically():
    perm = evaluate_action_permission(
        action_type="FILL_NON_SENSITIVE",
        form_data={"full_name": "Arif Alam", "email": "iamarifalam@gmail.com", "github": "iamarifalam"},
    )
    assert perm["allowed_automatically"] is True
    assert perm["requires_approval"] is False


def test_id_upload_requires_explicit_user_approval():
    perm = evaluate_action_permission(
        action_type="UPLOAD_ID",
        form_data={"student_id": "NMIMS_ID_PROOF.pdf"},
        details="Uploading Student ID for student developer pack verification",
    )
    assert perm["allowed_automatically"] is False
    assert perm["requires_approval"] is True
    assert perm["risk_level"] in ["High", "Critical"]


def test_detects_embedded_id_field_in_form_payload():
    perm = evaluate_action_permission(
        action_type="PREPARE_FORM",
        form_data={"name": "Arif Alam", "govt_id": "Aadhaar.pdf"},
    )
    assert perm["requires_approval"] is True
    assert perm["action_type"] == "UPLOAD_ID"


def test_legal_binding_terms_require_explicit_approval():
    perm = evaluate_action_permission(
        action_type="LEGAL_BINDING_AGREEMENT",
        form_data={},
        details="Assigning exclusive intellectual property rights to sponsor",
    )
    assert perm["requires_approval"] is True
    assert perm["risk_level"] == "High"
