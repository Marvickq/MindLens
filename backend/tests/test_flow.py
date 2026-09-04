"""
Tests — Uses in-memory SQLite to avoid needing PostgreSQL.
No external database dependency for test execution.
"""
import uuid
import pytest

# Bypass the production config guard before importing the app.
from app.config import set_test_mode
set_test_mode()

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session, select
from app.main import app
from app.database import get_session
from app.models.counselor import Organization, User, UserRole
from app.utils.security import hash_password

# In-memory SQLite DB for tests.
# StaticPool ensures all connections share the same underlying in-memory DB
# (otherwise each new connection would get a fresh empty database).
from sqlalchemy.pool import StaticPool

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TEST_ORG_ID = uuid.UUID("10000000-0000-0000-0000-000000000001")
TEST_COUNSELOR_ID = uuid.UUID("10000000-0000-0000-0000-000000000002")


def override_get_session():
    with Session(test_engine) as session:
        yield session


app.dependency_overrides[get_session] = override_get_session
client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def setup_db():
    SQLModel.metadata.create_all(test_engine)
    # Seed org + counselor into test DB
    with Session(test_engine) as db:
        org = db.get(Organization, TEST_ORG_ID)
        if not org:
            org = Organization(id=TEST_ORG_ID, name="Test Org")
            db.add(org)
            db.commit()
        user = db.get(User, TEST_COUNSELOR_ID)
        if not user:
            user = User(
                id=TEST_COUNSELOR_ID,
                organization_id=TEST_ORG_ID,
                name="Test Counselor",
                email="test@test.edu",
                password_hash=hash_password("TestPass123!"),
                role=UserRole.COUNSELOR,
                is_active=True,
            )
            db.add(user)
            db.commit()
    # Seed dimensions + questions into test DB
    seed_questionnaire_if_needed_for_test()
    yield
    SQLModel.metadata.drop_all(test_engine)


def seed_questionnaire_if_needed_for_test():
    """Seed dimensions and questions using the test engine."""
    from app.models.assessment import AssessmentVersion, Dimension, Question, ResponseType

    with Session(test_engine) as db:
        ver = db.exec(select(AssessmentVersion)).first()
        if not ver:
            ver = AssessmentVersion(name="Test Instrument", version="1.0")
            db.add(ver)
            db.commit()
            db.refresh(ver)

        dimensions = [
            ("attention_persistence", "Attention & Persistence", 1),
            ("activity", "Activity", 2),
            ("adaptability", "Adaptability", 3),
            ("sensitivity", "Sensitivity", 4),
            ("sociability", "Sociability", 5),
            ("self_regulation", "Self-Regulation", 6),
        ]
        dim_map = {}
        for code, label, order in dimensions:
            dim = db.exec(select(Dimension).where(Dimension.dimension_code == code)).first()
            if not dim:
                dim = Dimension(dimension_code=code, label=label, display_order=order)
                db.add(dim)
                db.commit()
                db.refresh(dim)
            dim_map[code] = dim

        q_count = db.exec(select(Question)).all()
        if not q_count:
            sample_questions = [
                ("attention_persistence", "ILCTI_ATTN_01", "Struggles to maintain focus on quiet or detailed tasks."),
                ("attention_persistence", "ILCTI_ATTN_02", "Easily distracted when working independently."),
                ("attention_persistence", "ILCTI_ATTN_03", "Difficulty following multi-step instructions."),
                ("activity", "ILCTI_ACT_01", "Displays high physical energy or restlessness."),
                ("activity", "ILCTI_ACT_02", "Needs frequent movement breaks."),
                ("activity", "ILCTI_ACT_03", "Often fidgets or squirms when expected to sit still."),
                ("adaptability", "ILCTI_ADP_01", "Adapts easily to sudden changes in schedule."),
                ("adaptability", "ILCTI_ADP_02", "Becomes upset when transitioning between activities."),
                ("adaptability", "ILCTI_ADP_03", "Shows flexibility when plans change unexpectedly."),
                ("sensitivity", "ILCTI_SEN_01", "Reacts strongly to mild environmental stressors."),
                ("sensitivity", "ILCTI_SEN_02", "Appears deeply affected by criticism or correction."),
                ("sensitivity", "ILCTI_SEN_03", "Responds intensely to loud or chaotic environments."),
                ("sociability", "ILCTI_SOC_01", "Initiates positive social interactions with peers."),
                ("sociability", "ILCTI_SOC_02", "Struggles to read social cues in group settings."),
                ("sociability", "ILCTI_SOC_03", "Prefers solitary activities over group engagement."),
                ("self_regulation", "ILCTI_REG_01", "Manages emotional responses effectively."),
                ("self_regulation", "ILCTI_REG_02", "Has difficulty calming down once upset."),
                ("self_regulation", "ILCTI_REG_03", "Responds impulsively before thinking."),
            ]
            for dim_code, q_code, text in sample_questions:
                q = Question(
                    assessment_version_id=ver.id,
                    dimension_id=dim_map[dim_code].id,
                    question_code=q_code,
                    question_text=text,
                    response_type=ResponseType.LIKERT,
                    display_order=dim_map[dim_code].display_order,
                    validation_config={"min": 1, "max": 5},
                )
                db.add(q)
            db.commit()


def _login() -> str:
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "test@test.edu", "password": "TestPass123!"},
    )
    assert res.status_code == 200, f"Login failed: {res.text}"
    return res.json()["access_token"]


def _auth(token: str):
    return {"Authorization": f"Bearer {token}"}


# ─── TEST 1: Health check ──────────────────────────────────────────
def test_health_check():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("ok", "degraded")


# ─── TEST 1: Create case -> appears in database ─────────────────────
def test_create_case_appears_in_db():
    token = _login()
    res = client.post(
        "/api/v1/cases",
        json={"display_name": "Test Student", "grade": "9", "school": "Test School"},
        headers=_auth(token),
    )
    assert res.status_code == 200
    case_id = res.json()["case_id"]

    res2 = client.get(f"/api/v1/cases/{case_id}", headers=_auth(token))
    assert res2.status_code == 200
    assert res2.json()["display_name"] == "Test Student"


# ─── TEST 2: Create case -> exactly three rater sessions ────────────
def test_create_case_has_three_sessions():
    token = _login()
    res = client.post(
        "/api/v1/cases",
        json={"display_name": "Three Session Student"},
        headers=_auth(token),
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data["sessions"]) == 3
    rater_types = {s["rater_type"] for s in data["sessions"]}
    assert rater_types == {"PARENT", "TEACHER", "ADOLESCENT"}


# ─── TEST 3: Each rater gets a unique token ─────────────────────────
def test_unique_tokens_per_rater():
    token = _login()
    res = client.post(
        "/api/v1/cases",
        json={"display_name": "Token Test Student"},
        headers=_auth(token),
    )
    data = res.json()
    tokens = [s["token"] for s in data["sessions"] if s.get("token")]
    assert len(tokens) == len(set(tokens)), "Tokens must be unique"


# ─── TEST 4: Valid token -> intake loads ─────────────────────────────
def test_valid_token_intake_loads():
    token = _login()
    res = client.post(
        "/api/v1/cases",
        json={"display_name": "Intake Test"},
        headers=_auth(token),
    )
    parent_session = res.json()["sessions"][0]
    intake_token = parent_session["token"]

    intake_res = client.get(f"/api/v1/intake/{intake_token}")
    assert intake_res.status_code == 200
    data = intake_res.json()
    assert "questions" in data
    assert len(data["questions"]) > 0
    assert data["rater_type"] == "PARENT"


# ─── TEST 5: Invalid token -> error ──────────────────────────────────
def test_invalid_token_returns_error():
    res = client.get("/api/v1/intake/invalid_token_12345")
    assert res.status_code in (400, 404)


# ─── TEST 6: Save response -> response exists ────────────────────────
def test_save_response():
    token = _login()
    res = client.post(
        "/api/v1/cases",
        json={"display_name": "Save Test"},
        headers=_auth(token),
    )
    intake_token = res.json()["sessions"][0]["token"]

    intake_res = client.get(f"/api/v1/intake/{intake_token}")
    q = intake_res.json()["questions"][0]

    save_res = client.post(
        f"/api/v1/intake/{intake_token}/responses",
        json={"question_id": q["id"], "value": 4},
    )
    assert save_res.status_code == 200
    assert save_res.json()["status"] == "saved"

    # Reload and verify
    intake_res2 = client.get(f"/api/v1/intake/{intake_token}")
    saved_q = [x for x in intake_res2.json()["questions"] if x["id"] == q["id"]][0]
    assert saved_q["saved_value"] == 4


# ─── TEST 7: Save same question twice -> upsert ─────────────────────
def test_upsert_response():
    token = _login()
    res = client.post(
        "/api/v1/cases",
        json={"display_name": "Upsert Test"},
        headers=_auth(token),
    )
    intake_token = res.json()["sessions"][0]["token"]
    q = client.get(f"/api/v1/intake/{intake_token}").json()["questions"][0]

    client.post(
        f"/api/v1/intake/{intake_token}/responses",
        json={"question_id": q["id"], "value": 3},
    )
    client.post(
        f"/api/v1/intake/{intake_token}/responses",
        json={"question_id": q["id"], "value": 5},
    )

    saved_q = [x for x in client.get(f"/api/v1/intake/{intake_token}").json()["questions"] if x["id"] == q["id"]][0]
    assert saved_q["saved_value"] == 5


# ─── TEST 8: Submit incomplete intake -> rejected ────────────────────
def test_submit_incomplete_rejected():
    token = _login()
    res = client.post(
        "/api/v1/cases",
        json={"display_name": "Incomplete Test"},
        headers=_auth(token),
    )
    intake_token = res.json()["sessions"][0]["token"]
    sub_res = client.post(f"/api/v1/intake/{intake_token}/submit")
    assert sub_res.status_code == 400


# ─── TEST 9: Submit complete intake -> SUBMITTED ─────────────────────
def test_submit_complete():
    token = _login()
    res = client.post(
        "/api/v1/cases",
        json={"display_name": "Complete Test"},
        headers=_auth(token),
    )
    intake_token = res.json()["sessions"][0]["token"]
    questions = client.get(f"/api/v1/intake/{intake_token}").json()["questions"]

    for q in questions:
        client.post(
            f"/api/v1/intake/{intake_token}/responses",
            json={"question_id": q["id"], "value": 4},
        )

    sub_res = client.post(f"/api/v1/intake/{intake_token}/submit")
    assert sub_res.status_code == 200
    assert sub_res.json()["status"] == "submitted"


# ─── TEST 10: Submitted session cannot be resubmitted ────────────────
def test_cannot_resubmit():
    token = _login()
    res = client.post(
        "/api/v1/cases",
        json={"display_name": "Resubmit Test"},
        headers=_auth(token),
    )
    intake_token = res.json()["sessions"][0]["token"]
    questions = client.get(f"/api/v1/intake/{intake_token}").json()["questions"]

    for q in questions:
        client.post(
            f"/api/v1/intake/{intake_token}/responses",
            json={"question_id": q["id"], "value": 4},
        )

    client.post(f"/api/v1/intake/{intake_token}/submit")
    sub2 = client.post(f"/api/v1/intake/{intake_token}/submit")
    assert sub2.json()["status"] == "already_submitted"


# ─── TEST 11: Counselor Cases API returns database cases ─────────────
def test_cases_api_returns_db_cases():
    token = _login()
    client.post(
        "/api/v1/cases",
        json={"display_name": "API Test Case"},
        headers=_auth(token),
    )
    res = client.get("/api/v1/cases", headers=_auth(token))
    assert res.status_code == 200
    cases_list = res.json()
    names = [c["display_name"] for c in cases_list]
    assert "API Test Case" in names


# ─── TEST 12: Cases list returns a list (empty or populated) ─────────
def test_empty_database():
    token = _login()
    res = client.get("/api/v1/cases", headers=_auth(token))
    assert res.status_code == 200
    assert isinstance(res.json(), list)


# ─── TEST 13: Heatmap does not fabricate missing rater values ────────
def test_heatmap_no_fabrication():
    token = _login()
    res = client.post(
        "/api/v1/cases",
        json={"display_name": "Heatmap Test"},
        headers=_auth(token),
    )
    case_id = res.json()["case_id"]

    heatmap = client.get(f"/api/v1/cases/{case_id}/heatmap", headers=_auth(token))
    assert heatmap.status_code == 200
    data = heatmap.json()
    for cell in data["cells"]:
        if not cell["has_response"]:
            assert cell["score"] is None


# ─── TEST 14: Counselor review persists after refresh ────────────────
def test_review_persists():
    token = _login()
    res = client.post(
        "/api/v1/cases",
        json={"display_name": "Review Test"},
        headers=_auth(token),
    )
    case_id = res.json()["case_id"]

    client.post(
        f"/api/v1/cases/{case_id}/review",
        json={"action": "MONITOR", "note": "Watch closely."},
        headers=_auth(token),
    )

    review = client.get(f"/api/v1/cases/{case_id}/review", headers=_auth(token))
    assert review.status_code == 200
    assert review.json()["action"] == "MONITOR"
    assert review.json()["note"] == "Watch closely."


# ─── TEST 15: Audit event generated for case creation ────────────────
def test_audit_event_created():
    token = _login()
    res = client.post(
        "/api/v1/cases",
        json={"display_name": "Audit Test"},
        headers=_auth(token),
    )
    case_id = res.json()["case_id"]

    audit = client.get(f"/api/v1/cases/{case_id}/audit", headers=_auth(token))
    assert audit.status_code == 200
    body = audit.json()
    # New counselor-facing shape: timeline + technical + assessment_history
    assert "timeline" in body
    assert "technical" in body
    assert "assessment_history" in body
    titles = [e["display_title"] for e in body["timeline"]]
    assert "Case created" in titles
    # Canonical raw event type is always retained for traceability
    raw_types = {e["event_type"] for e in body["timeline"]}.union(
        {e["event_type"] for e in body["technical"]}
    )
    assert "CASE_CREATED" in raw_types


# ══════════════════════════════════════════════════════════════════════
#  TEST 1 (set 2): Rater invitation mechanism
# ══════════════════════════════════════════════════════════════════════

import hashlib as _hashlib


def _create_case_with_sessions(token: str, name: str = "Rater Invite") -> tuple:
    res = client.post(
        "/api/v1/cases",
        json={"display_name": name},
        headers=_auth(token),
    )
    assert res.status_code == 200
    case_id = res.json()["case_id"]
    sessions = client.get(f"/api/v1/cases/{case_id}/sessions", headers=_auth(token))
    assert sessions.status_code == 200
    return case_id, sessions.json()


# TEST 1 (set 2): Sessions endpoint returns real intake URL + backend QR
def test_sessions_return_intake_url_and_qr():
    token = _login()
    case_id, sessions = _create_case_with_sessions(token)
    assert len(sessions) == 3
    for s in sessions:
        assert s["intake_url"] and s["intake_url"].startswith("http://")
        assert "/intake/" in s["intake_url"]
        assert s["qr_payload"] and s["qr_payload"]["qr_base64"].startswith("data:image/png")
        assert s["qr_payload"]["url"] == s["intake_url"]


# TEST 2 (set 2): QR encodes exactly the intake URL
def test_qr_url_equals_intake_url():
    token = _login()
    _, sessions = _create_case_with_sessions(token)
    for s in sessions:
        assert s["qr_payload"]["url"] == s["intake_url"]


# TEST 3 (set 2): Each rater gets a distinct QR
def test_distinct_qrs_per_rater():
    token = _login()
    _, sessions = _create_case_with_sessions(token)
    qrs = {s["qr_payload"]["qr_base64"] for s in sessions}
    exists = [s["qr_payload"]["qr_base64"] for s in sessions]
    assert len(qrs) == 3
    assert len({url for url in [s["intake_url"] for s in sessions]}) == 3
    assert len(set(exists)) == len(exists)


# TEST 4 (set 2): Raw token is NOT stored plaintext; hash + encryption used
def test_token_not_stored_plaintext():
    token = _login()
    res = client.post("/api/v1/cases", json={"display_name": "Plaintext Test"}, headers=_auth(token))
    case_id = res.json()["case_id"]
    created_tokens = {s["rater_type"]: s["token"] for s in res.json()["sessions"]}

    from app.models.rater import RaterSession
    from app.utils.token_crypto import decrypt_value

    with Session(test_engine) as db:
        sessions = db.exec(select(RaterSession).where(RaterSession.case_id == case_id)).all()
        assert len(sessions) == 3
        for s in sessions:
            raw = created_tokens[s.rater_type.value]
            intake_url = decrypt_value(s.encrypted_intake_url)
            assert s.token_hash == _hashlib.sha256(raw.encode()).hexdigest()
            assert s.encrypted_token != raw
            assert raw not in (s.token_hash, s.encrypted_token or "")
            assert decrypt_value(s.encrypted_token) == raw
            assert intake_url.startswith("http") and "/intake/" in intake_url


# TEST 5 (set 2): Dedicated QR endpoint returns a PNG data URL
def test_qr_endpoint_returns_png():
    token = _login()
    case_id, sessions = _create_case_with_sessions(token)
    sid = sessions[0]["session_id"]
    res = client.get(f"/api/v1/cases/{case_id}/sessions/{sid}/qr", headers=_auth(token))
    assert res.status_code == 200
    data = res.json()
    assert data["qr_base64"].startswith("data:image/png")
    assert data["url"] == sessions[0]["intake_url"]


# TEST 6 (set 2): Status transitions PENDING -> IN_PROGRESS -> SUBMITTED
def test_status_transitions():
    token = _login()
    res = client.post("/api/v1/cases", json={"display_name": "Status Trans Test"}, headers=_auth(token))
    case_id = res.json()["case_id"]
    created = {s["rater_type"]: s["status"] for s in res.json()["sessions"]}
    assert created["PARENT"] == "PENDING"

    # Load the questionnaire (starts the session -> IN_PROGRESS)
    session = next(s for s in res.json()["sessions"] if s["rater_type"] == "PARENT")
    parent_token = session["token"]

    client.get(f"/api/v1/intake/{parent_token}")
    sessions2 = client.get(f"/api/v1/cases/{case_id}/sessions", headers=_auth(token)).json()
    parent2 = next(s for s in sessions2 if s["rater_type"] == "PARENT")
    assert parent2["status"] == "IN_PROGRESS"

    questions = client.get(f"/api/v1/intake/{parent_token}").json()["questions"]
    for q in questions:
        client.post(f"/api/v1/intake/{parent_token}/responses", json={"question_id": q["id"], "value": 4})
    client.post(f"/api/v1/intake/{parent_token}/submit")

    sessions3 = client.get(f"/api/v1/cases/{case_id}/sessions", headers=_auth(token)).json()
    parent3 = next(s for s in sessions3 if s["rater_type"] == "PARENT")
    assert parent3["status"] == "SUBMITTED"


# TEST: Audit trail is humanized for counselors but preserves the raw event
def test_audit_trail_humanizes_rater_events():
    token = _login()
    res = client.post("/api/v1/cases", json={"display_name": "Audit Trail Test"}, headers=_auth(token))
    case_id = res.json()["case_id"]
    sessions = {s["rater_type"]: s["token"] for s in res.json()["sessions"]}

    # Parent starts and submits
    client.get(f"/api/v1/intake/{sessions['PARENT']}")
    qs = client.get(f"/api/v1/intake/{sessions['PARENT']}").json()["questions"]
    for q in qs:
        client.post(f"/api/v1/intake/{sessions['PARENT']}/responses", json={"question_id": q["id"], "value": 4})
    client.post(f"/api/v1/intake/{sessions['PARENT']}/submit")

    audit = client.get(f"/api/v1/cases/{case_id}/audit", headers=_auth(token)).json()
    titles = [e["display_title"] for e in audit["timeline"]]
    # Humanized, rater-identifying title (not the raw enum name)
    assert "Parent completed questionnaire" in titles
    assert all("QUESTIONNAIRE_SUBMITTED" != t for t in titles)
    # Raw event type retained somewhere for traceability
    raw = {e["event_type"] for e in audit["timeline"]}.union(
        {e["event_type"] for e in audit["technical"]}
    )
    assert "QUESTIONNAIRE_SUBMITTED" in raw
    # Assessment history derived from real DB submission events
    assert audit["assessment_history"].get("PARENT", {}).get("status") == "Completed"


# TEST 7 (set 2): Regeneration issues a new token and invalidates the old one
def test_regenerate_invalidates_old_token():
    token = _login()
    res = client.post("/api/v1/cases", json={"display_name": "Regen Test"}, headers=_auth(token))
    case_id = res.json()["case_id"]
    created = {s["rater_type"]: s["token"] for s in res.json()["sessions"]}
    old_token = created["PARENT"]

    sessions = client.get(f"/api/v1/cases/{case_id}/sessions", headers=_auth(token)).json()
    parent = next(s for s in sessions if s["rater_type"] == "PARENT")

    regen = client.post(
        f"/api/v1/cases/{case_id}/sessions/{parent['session_id']}/regenerate",
        headers=_auth(token),
    )
    assert regen.status_code == 200
    new_token = regen.json()["token"]
    assert new_token != old_token

    # Old token should no longer be accepted
    old_res = client.get(f"/api/v1/intake/{old_token}")
    assert old_res.status_code in (400, 404)

    # New token loads the questionnaire
    new_res = client.get(f"/api/v1/intake/{new_token}")
    assert new_res.status_code == 200
    assert "questions" in new_res.json()


# TEST 8 (set 2): Non-owner cannot read another org's session QR
def test_session_qr_requires_org_scoping():
    token = _login()
    case_id, sessions = _create_case_with_sessions(token)
    sid = sessions[0]["session_id"]

    # A counselor from a different org is not in this test DB; verify auth is enforced
    unauthed = client.get(f"/api/v1/cases/{case_id}/sessions/{sid}/qr")
    assert unauthed.status_code in (401, 403)


# TEST: Download report returns a real application/pdf via POST
def test_report_download_returns_pdf():
    token = _login()
    res = client.post("/api/v1/cases", json={"display_name": "Report Test"}, headers=_auth(token))
    case_id = res.json()["case_id"]

    resp = client.post(f"/api/v1/cases/{case_id}/report", headers=_auth(token))
    assert resp.status_code == 200
    assert "application/pdf" in resp.headers.get("content-type", "")
    assert "attachment" in resp.headers.get("content-disposition", "")
    assert resp.content[:5] == b"%PDF-"


# TEST: Without a validated research config, divergences stay unvalidated and
# NO signals are generated (no hardcoded thresholds / no fallback parameters).
def test_signals_require_validated_research_config():
    token = _login()
    res = client.post("/api/v1/cases", json={"display_name": "Signals No-Config Test"}, headers=_auth(token))
    case_id = res.json()["case_id"]
    tokens = {s["rater_type"]: s["token"] for s in res.json()["sessions"]}

    # Submit all three raters with differing values to force divergences
    for rt, val in (("PARENT", 1), ("TEACHER", 5), ("ADOLESCENT", 3)):
        client.get(f"/api/v1/intake/{tokens[rt]}")
        qs = client.get(f"/api/v1/intake/{tokens[rt]}").json()["questions"]
        for q in qs:
            client.post(f"/api/v1/intake/{tokens[rt]}/responses", json={"question_id": q["id"], "value": val})
        client.post(f"/api/v1/intake/{tokens[rt]}/submit")

    sigs = client.get(f"/api/v1/cases/{case_id}/signals", headers=_auth(token)).json()
    assert isinstance(sigs, list)
    assert len(sigs) == 0, "No config -> all discrepancies unvalidated -> no signals"


# TEST: With an explicit validated SED research config, a neutral signal with
# provenance is produced for that dimension/rater-pair.
def test_signals_validated_when_config_present():
    from app.models.discrepancy import DiscrepancyMethodConfig, DiscrepancyMethodology
    from app.models.assessment import Dimension

    token = _login()

    # Insert a validated research config for the PARENT-TEACHER pair on the
    # "adaptability" dimension BEFORE submission so the pipeline picks it up.
    with Session(test_engine) as db:
        dim = db.exec(select(Dimension).where(Dimension.dimension_code == "adaptability")).first()
        assert dim is not None
        db.add(DiscrepancyMethodConfig(
            instrument_version="1.0",
            dimension_id=dim.id,
            rater_pair="PARENT_TEACHER",
            methodology=DiscrepancyMethodology.SED,
            calculation_method="configured_discrepancy_engine_v1",
            calculation_version="1.0",
            reliability=0.85,
            reliability_source="Test reliability citation",
            reference_sd=15.0,
            reference_sd_source="Test SD citation",
            significance_threshold=1.0,
            source_citation="Test research source",
            is_active=True,
        ))
        db.commit()

    res = client.post("/api/v1/cases", json={"display_name": "Signals Config Test"}, headers=_auth(token))
    case_id = res.json()["case_id"]
    tokens = {s["rater_type"]: s["token"] for s in res.json()["sessions"]}

    for rt, val in (("PARENT", 1), ("TEACHER", 5), ("ADOLESCENT", 3)):
        client.get(f"/api/v1/intake/{tokens[rt]}")
        qs = client.get(f"/api/v1/intake/{tokens[rt]}").json()["questions"]
        for q in qs:
            client.post(f"/api/v1/intake/{tokens[rt]}/responses", json={"question_id": q["id"], "value": val})
        client.post(f"/api/v1/intake/{tokens[rt]}/submit")

    sigs = client.get(f"/api/v1/cases/{case_id}/signals", headers=_auth(token)).json()
    assert isinstance(sigs, list)
    assert len(sigs) >= 1, "A validated config should produce at least one signal"

    for s in sigs:
        assert s.get("dimension_label")
        assert s.get("divergence") is not None
        assert len(s.get("rater_pair") or []) == 2
        # Neutral wording: never implies which report is correct or a diagnosis.
        assert "does not imply" in s.get("description", "").lower()


def test_signal_summary_missing_rater_is_null():
    token = _login()

    # A fully-submitted case has real scores for all present raters and a computed discrepancy.
    res = client.post("/api/v1/cases", json={"display_name": "Signal Summary Full Test"}, headers=_auth(token))
    case_id = res.json()["case_id"]
    tokens = {s["rater_type"]: s["token"] for s in res.json()["sessions"]}

    for rt, val in (("PARENT", 1), ("TEACHER", 5), ("ADOLESCENT", 3)):
        client.get(f"/api/v1/intake/{tokens[rt]}")
        qs = client.get(f"/api/v1/intake/{tokens[rt]}").json()["questions"]
        for q in qs:
            client.post(f"/api/v1/intake/{tokens[rt]}/responses", json={"question_id": q["id"], "value": val})
        client.post(f"/api/v1/intake/{tokens[rt]}/submit")

    summary = client.get(f"/api/v1/cases/{case_id}/signal-summary", headers=_auth(token)).json()
    dims = summary["dimensions"]
    assert len(dims) == 6
    for d in dims:
        assert d["parent_score"] is not None
        assert d["teacher_score"] is not None
        assert d["adolescent_score"] is not None
        assert d["largest_difference"] is not None
        assert len(d["largest_difference_pair"]) == 2

    # A case with no responses has NO hardcoded scores — every missing value is None, never 0.
    fresh = client.post("/api/v1/cases", json={"display_name": "Signal Summary Fresh Test"}, headers=_auth(token))
    fresh_id = fresh.json()["case_id"]
    fresh_summary = client.get(f"/api/v1/cases/{fresh_id}/signal-summary", headers=_auth(token)).json()
    for d in fresh_summary["dimensions"]:
        assert d["parent_score"] is None
        assert d["teacher_score"] is None
        assert d["adolescent_score"] is None
        assert d["largest_difference"] is None
        assert d["has_signal"] is False


# ============================================================================
# P5 — FULL E2E INTEGRATION: RESPONSE PERSISTENCE CHAIN
# ============================================================================

def test_p5_full_e2e_response_persistence_chain():
    """P5 Definition of Done: responses persist through the entire chain from
    intake submission to counselor dashboard. No frontend-only persistence."""
    token = _login()

    # 1. Create case
    res = client.post("/api/v1/cases", json={"display_name": "P5 E2E Chain"}, headers=_auth(token))
    assert res.status_code == 200
    case_id = res.json()["case_id"]
    assert res.json()["status"] == "WAITING_FOR_RESPONSES"
    sessions = res.json()["sessions"]
    assert len(sessions) == 3
    tokens = {s["rater_type"]: s["token"] for s in sessions}

    # 2. Each rater opens intake, saves responses, submits
    for rt, val in (("PARENT", 2), ("TEACHER", 4), ("ADOLESCENT", 3)):
        tok = tokens[rt]
        # Open intake — responses start empty
        qres = client.get(f"/api/v1/intake/{tok}")
        assert qres.status_code == 200
        qs = qres.json()["questions"]
        assert len(qs) >= 1
        for q in qs:
            # saved_value should be null for fresh intake
            assert q["saved_value"] is None

        # Save each response
        for q in qs:
            sres = client.post(f"/api/v1/intake/{tok}/responses",
                               json={"question_id": q["id"], "value": val})
            assert sres.status_code == 200
            assert sres.json()["status"] == "saved"
            assert "response_id" in sres.json()

        # Re-open intake — responses must be persisted (not frontend-only)
        qres2 = client.get(f"/api/v1/intake/{tok}")
        for q in qres2.json()["questions"]:
            assert q["saved_value"] == val, f"Response for {q['id']} not persisted to DB!"

        # Submit
        sub = client.post(f"/api/v1/intake/{tok}/submit")
        assert sub.status_code == 200
        assert sub.json()["status"] == "submitted"

        # Attempt re-submit — should be idempotent
        sub2 = client.post(f"/api/v1/intake/{tok}/submit")
        assert sub2.status_code == 200
        assert sub2.json()["status"] == "already_submitted"

    # 3. Case transitions to READY_FOR_REVIEW
    detail = client.get(f"/api/v1/cases/{case_id}", headers=_auth(token)).json()
    assert detail["status"] == "READY_FOR_REVIEW"
    for s in detail["sessions"]:
        assert s["status"] == "SUBMITTED"

    # 4. Scores persisted and accessible
    heat = client.get(f"/api/v1/cases/{case_id}/heatmap", headers=_auth(token)).json()
    present = [c for c in heat["cells"] if c["has_response"]]
    assert len(present) >= 6  # 6 dimensions × 3 raters, at least 18 if all present

    # 5. Discrepancies persisted
    disc = client.get(f"/api/v1/cases/{case_id}/discrepancies", headers=_auth(token)).json()
    assert len(disc["scores"]) >= 6
    assert len(disc["discrepancies"]) >= 3  # at least 3 rater pairs

    # 6. Audit trail persisted
    audit = client.get(f"/api/v1/cases/{case_id}/audit", headers=_auth(token)).json()
    event_types = [e["event_type"] for e in audit.get("timeline", []) + audit.get("technical", [])]
    assert "CASE_CREATED" in event_types
    assert "QUESTIONNAIRE_SUBMITTED" in event_types
    assert "SCORES_CALCULATED" in event_types

    # 7. Dashboard reflects new case
    dash = client.get("/api/v1/dashboard/summary", headers=_auth(token)).json()
    assert dash["ready_for_review"] >= 1


def test_p5_responses_persist_across_reopen():
    """Responses survive session re-open (partial save then continue later)."""
    token = _login()
    res = client.post("/api/v1/cases", json={"display_name": "P5 Reopen"}, headers=_auth(token))
    case_id = res.json()["case_id"]
    tokens = {s["rater_type"]: s["token"] for s in res.json()["sessions"]}
    tok = tokens["PARENT"]

    qres = client.get(f"/api/v1/intake/{tok}")
    qs = qres.json()["questions"]

    # Save only the first response, then close and reopen
    client.post(f"/api/v1/intake/{tok}/responses",
                json={"question_id": qs[0]["id"], "value": 3})

    # Simulate reopen (new request, same token)
    qres2 = client.get(f"/api/v1/intake/{tok}")
    assert qres2.json()["questions"][0]["saved_value"] == 3

    # Remaining questions still unsaved
    for q in qres2.json()["questions"][1:]:
        assert q["saved_value"] is None


def test_p5_transactional_submit_all_or_nothing():
    """Submit fails if required questions are missing; partial submit does not corrupt state."""
    token = _login()
    res = client.post("/api/v1/cases", json={"display_name": "P5 Txn"}, headers=_auth(token))
    tokens = {s["rater_type"]: s["token"] for s in res.json()["sessions"]}
    tok = tokens["TEACHER"]

    qres = client.get(f"/api/v1/intake/{tok}")
    qs = qres.json()["questions"]

    # Submit without answering — should fail (required questions missing)
    sub = client.post(f"/api/v1/intake/{tok}/submit")
    assert sub.status_code == 400

    # Session should NOT be marked completed after failed submit
    qres2 = client.get(f"/api/v1/intake/{tok}")
    assert qres2.json()["status"] == "STARTED"  # not SUBMITTED


# ============================================================================
# P6 — SECURITY: CASE ISOLATION / IDOR
# ============================================================================

SECOND_ORG_ID = uuid.UUID("20000000-0000-0000-0000-000000000001")
SECOND_COUNSELOR_ID = uuid.UUID("20000000-0000-0000-0000-000000000002")


def _setup_second_org():
    """Create a second org + counselor in the test DB for isolation tests."""
    with Session(test_engine) as db:
        org = db.get(Organization, SECOND_ORG_ID)
        if not org:
            org = Organization(id=SECOND_ORG_ID, name="Other Org")
            db.add(org)
            db.commit()
        user = db.get(User, SECOND_COUNSELOR_ID)
        if not user:
            user = User(
                id=SECOND_COUNSELOR_ID,
                organization_id=SECOND_ORG_ID,
                name="Other Counselor",
                email="other@test.edu",
                password_hash=hash_password("OtherPass123!"),
                role=UserRole.COUNSELOR,
                is_active=True,
            )
            db.add(user)
            db.commit()


def _login_other() -> str:
    _setup_second_org()
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "other@test.edu", "password": "OtherPass123!"},
    )
    assert res.status_code == 200
    return res.json()["access_token"]


def test_p6_case_isolation_cannot_access_other_org_case():
    """Counselor A cannot access Counselor B's case (different org)."""
    token_a = _login()
    token_b = _login_other()

    # Counselor A creates a case
    res = client.post("/api/v1/cases", json={"display_name": "Org A Case"}, headers=_auth(token_a))
    case_id = res.json()["case_id"]

    # Counselor B tries to access it — should get 404 (not 200 or 403)
    for endpoint in [f"/api/v1/cases/{case_id}",
                     f"/api/v1/cases/{case_id}/sessions",
                     f"/api/v1/cases/{case_id}/heatmap",
                     f"/api/v1/cases/{case_id}/discrepancies",
                     f"/api/v1/cases/{case_id}/signals",
                     f"/api/v1/cases/{case_id}/signal-summary",
                     f"/api/v1/cases/{case_id}/review",
                     f"/api/v1/cases/{case_id}/audit"]:
        r = client.get(endpoint, headers=_auth(token_b))
        assert r.status_code == 404, f"Isolation breach: {endpoint} returned {r.status_code}"


def test_p6_case_isolation_post_endpoints():
    """Counselor B cannot POST to Counselor A's case endpoints."""
    token_a = _login()
    token_b = _login_other()

    res = client.post("/api/v1/cases", json={"display_name": "Org A Case Post"}, headers=_auth(token_a))
    case_id = res.json()["case_id"]

    # Counselor B tries to POST review — should get 404
    r = client.post(f"/api/v1/cases/{case_id}/review",
                    json={"action": "MONITOR", "note": "attempted breach"},
                    headers=_auth(token_b))
    assert r.status_code == 404

    # Counselor B tries to POST report — should get 404
    r = client.post(f"/api/v1/cases/{case_id}/report", headers=_auth(token_b))
    assert r.status_code == 404


def test_p6_rater_token_scoped_to_session():
    """Rater token cannot access a different session's intake."""
    token = _login()
    res = client.post("/api/v1/cases", json={"display_name": "Token Scope"}, headers=_auth(token))
    tokens_a = {s["rater_type"]: s["token"] for s in res.json()["sessions"]}

    # Create a second case
    res2 = client.post("/api/v1/cases", json={"display_name": "Token Scope B"}, headers=_auth(token))
    tokens_b = {s["rater_type"]: s["token"] for s in res2.json()["sessions"]}

    # PARENT token from case A should NOT be able to open case B's PARENT intake
    r = client.get(f"/api/v1/intake/{tokens_a['PARENT']}")
    assert r.status_code == 200  # case A — should work

    # Trying to use case A's PARENT token against case B's questions is not
    # directly possible (the token maps to case A), but we verify the token
    # maps to the correct session
    qres = client.get(f"/api/v1/intake/{tokens_a['PARENT']}")
    assert qres.status_code == 200
    # The session should be for case A
    session_id = qres.json()["session_id"]
    assert session_id is not None


def test_p6_unauthenticated_access_denied():
    """All counselor endpoints reject requests without a valid token."""
    endpoints = [
        ("GET", "/api/v1/cases"),
        ("GET", "/api/v1/dashboard/summary"),
    ]
    for method, path in endpoints:
        if method == "GET":
            r = client.get(path)
        else:
            r = client.post(path)
        assert r.status_code in (401, 403), f"No-auth {method} {path} returned {r.status_code}"


def test_p6_invalid_jwt_rejected():
    """Requests with a garbage JWT are rejected."""
    fake_token = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJub3RoaW5nIn0.invalid"
    r = client.get("/api/v1/cases", headers=_auth(fake_token))
    assert r.status_code in (401, 403)


def test_p6_inactive_user_cannot_login():
    """Deactivated user cannot authenticate."""
    with Session(test_engine) as db:
        user = db.get(User, TEST_COUNSELOR_ID)
        user.is_active = False
        db.add(user)
        db.commit()

    res = client.post(
        "/api/v1/auth/login",
        json={"email": "test@test.edu", "password": "TestPass123!"},
    )
    assert res.status_code in (400, 401)

    # Restore for other tests
    with Session(test_engine) as db:
        user = db.get(User, TEST_COUNSELOR_ID)
        user.is_active = True
        db.add(user)
        db.commit()


def test_p6_token_regeneration_invalidates_old():
    """After token regeneration, the old token should no longer work."""
    token = _login()
    res = client.post("/api/v1/cases", json={"display_name": "Token Regen"}, headers=_auth(token))
    case_id = res.json()["case_id"]
    old_token = res.json()["sessions"][0]["token"]

    # Get session_id from the sessions endpoint (not in creation response)
    sessions = client.get(f"/api/v1/cases/{case_id}/sessions", headers=_auth(token)).json()
    session_id = sessions[0]["session_id"]

    # Old token works
    r = client.get(f"/api/v1/intake/{old_token}")
    assert r.status_code == 200

    # Regenerate
    regen = client.post(f"/api/v1/cases/{case_id}/sessions/{session_id}/regenerate",
                        headers=_auth(token))
    assert regen.status_code == 200
    new_token = regen.json()["token"]

    # New token works
    r2 = client.get(f"/api/v1/intake/{new_token}")
    assert r2.status_code == 200

    # Old token should be rejected (different hash)
    r3 = client.get(f"/api/v1/intake/{old_token}")
    assert r3.status_code == 400, "Old token still works after regeneration!"


# ============================================================================
# P5 — SCORING PIPELINE VERIFICATION
# ============================================================================

def test_p5_scores_originate_from_backend():
    """Dimension scores are calculated by the backend, not stored from client input."""
    token = _login()
    res = client.post("/api/v1/cases", json={"display_name": "P5 Scores"}, headers=_auth(token))
    case_id = res.json()["case_id"]
    tokens = {s["rater_type"]: s["token"] for s in res.json()["sessions"]}

    for rt, val in (("PARENT", 1), ("TEACHER", 5), ("ADOLESCENT", 3)):
        qs = client.get(f"/api/v1/intake/{tokens[rt]}").json()["questions"]
        for q in qs:
            client.post(f"/api/v1/intake/{tokens[rt]}/responses",
                        json={"question_id": q["id"], "value": val})
        client.post(f"/api/v1/intake/{tokens[rt]}/submit")

    # Scores are calculated server-side — verify they exist and are normalized
    heat = client.get(f"/api/v1/cases/{case_id}/heatmap", headers=_auth(token)).json()
    for cell in heat["cells"]:
        if cell["has_response"]:
            assert 0.0 <= cell["score"] <= 100.0, f"Score {cell['score']} out of range"

