"""
Audit Presentation Service

Transforms the raw (technical, machine-readable) audit log into a concise,
counselor-readable case history. The raw audit records are NEVER deleted or
modified; this service only produces a presentation layer on top of them.

Each presented event answers: WHO? WHAT? WHEN? WHAT CHANGED?
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.models.audit_event import AuditEvent, ActorType

RATER_LABELS = {
    "PARENT": "Parent",
    "TEACHER": "Teacher",
    "ADOLESCENT": "Adolescent",
}

ACTOR_LABELS = {
    "COUNSELOR": "Counselor",
    "ADMIN": "Admin",
    "RATER": "Rater",
    "SYSTEM": "MindLens",
}

# ---------------------------------------------------------------------------
# Category buckets used for the simple counselor filters
# ---------------------------------------------------------------------------
RATER_CATEGORY = "RATER_ACTIVITY"
SYSTEM_CATEGORY = "MIND_FORGE_PROCESSING"
COUNSELOR_CATEGORY = "COUNSELOR_ACTIVITY"
CASE_CATEGORY = "CASE_ACTIVITY"
SECURITY_CATEGORY = "SECURITY"

# ---------------------------------------------------------------------------
# Humanization table.
#
# Each raw event maps to:
#   title_fn  - builds the concise title (may use rater type / metadata)
#   desc_fn   - one-line description
#   category  - one of the five categories above
#   technical - whether this event should be shown in technical details only
#               (i.e. NOT a primary timeline entry by default)
# ---------------------------------------------------------------------------
def _actor_value(event: AuditEvent) -> str:
    at = event.actor_type
    return at.value if hasattr(at, "value") else str(at)


def _humanize_event(event: AuditEvent, rater_label: Optional[str]) -> Optional[dict]:
    et = event.event_type
    meta = event.event_metadata or {}
    actor_val = _actor_value(event)
    actor = ACTOR_LABELS.get(actor_val, actor_val)
    rt = rater_label or RATER_LABELS.get(meta.get("rater_type"), meta.get("rater_type"))

    def entry(t, d, cat, tech=False):
        return {
            "display_title": t,
            "description": d,
            "category": cat,
            "technical": tech,
        }

    if et == "CASE_CREATED":
        return entry("Case created", "Case created", CASE_CATEGORY)
    if et == "RATER_QR_GENERATED":
        return entry(f"{rt} invitation generated" if rt else "Rater invitation generated",
                     "Invitation link created", CASE_CATEGORY)
    if et == "RATER_LINK_REGENERATED":
        return entry(f"{rt} invitation link regenerated" if rt else "Invitation link regenerated",
                     "New invitation link issued", SECURITY_CATEGORY)
    if et == "RATER_INTAKE_STARTED":
        return entry(f"{rt} started questionnaire" if rt else "Rater started questionnaire",
                     "Intake opened", RATER_CATEGORY)
    if et == "QUESTIONNAIRE_SUBMITTED":
        return entry(f"{rt} completed questionnaire" if rt else "Rater completed questionnaire",
                     "Questionnaire submitted", RATER_CATEGORY)
    if et == "SCORES_CALCULATED":
        return entry("Perspective scores calculated",
                     "Rater scores computed", SYSTEM_CATEGORY)
    if et == "DISCREPANCY_CALCULATED":
        return entry("Perspective comparison completed",
                     "Perspectives compared", SYSTEM_CATEGORY)
    if et == "SIGNAL_GENERATED":
        return entry("A review signal was surfaced",
                     "Divergence surfaced for counselor review", SYSTEM_CATEGORY)
    if et == "EVIDENCE_VIEWED":
        return entry("Counselor reviewed evidence",
                     "Counselor viewed evidence chain", COUNSELOR_CATEGORY)
    if et == "REVIEW_CREATED":
        action = meta.get("action")
        return entry("Counselor recorded next step",
                     action and f"Action: {action}" or "Review recorded",
                     COUNSELOR_CATEGORY)
    if et == "REPORT_GENERATED":
        return entry("PDF report generated",
                     "Case report generated", COUNSELOR_CATEGORY)

    # Unknown / future event: fall back to a mild humanization but keep the
    # raw type available for technical details.
    pretty = et.replace("_", " ").title()
    return entry(pretty, "System event", CASE_CATEGORY, tech=True)


def _rater_label(event: AuditEvent) -> Optional[str]:
    meta = event.event_metadata or {}
    return RATER_LABELS.get(meta.get("rater_type"), meta.get("rater_type"))


def present_event(event: AuditEvent) -> Optional[dict]:
    """Return a single structured, counselor-readable event."""
    human = _humanize_event(event, _rater_label(event))
    if human is None:
        return None
    return {
        "id": str(event.id),
        "event_type": event.event_type,  # canonical raw type ALWAYS retained
        "actor_type": _actor_value(event),
        "actor": ACTOR_LABELS.get(_actor_value(event), _actor_value(event)),
        "rater_type": event.event_metadata.get("rater_type") if event.event_metadata else None,
        "occurred_at": event.created_at,
        "category": human["category"],
        "display_title": human["display_title"],
        "description": human["description"],
        "technical": human["technical"],
        "metadata": event.event_metadata or {},
    }


def present_audit_trail(events: list[AuditEvent]) -> dict:
    """
    Build the counselor-facing audit view from raw records.

    Returns:
        {
          "timeline": [...primary entries, grouped + deduped...],
          "technical": [...raw entries for the technical drawer...],
          "assessment_history": {rater: {status}},  // derived from real events
        }
    """
    ordered = sorted(events, key=lambda e: e.created_at)

    # Collapse burst events (e.g. QUESTIONNAIRE_SUBMITTED + SCORES_CALCULATED +
    # DISCREPANCY_CALCULATED within 2s after the 3rd submission) into a single
    # "Assessment processing completed" entry. Underlying records all remain.
    # Group candidacy: the last rater submission and the system processing
    # events that follow it within a short window.
    assessment_window_ms = 2000
    grouped: list[list[AuditEvent]] = []
    i = 0
    n = len(ordered)
    while i < n:
        e = ordered[i]
        if e.event_type == "QUESTIONNAIRE_SUBMITTED":
            group = [e]
            j = i + 1
            while j < n:
                nxt = ordered[j]
                if nxt.event_type in ("SCORES_CALCULATED", "DISCREPANCY_CALCULATED", "SIGNAL_GENERATED"):
                    delta = (nxt.created_at - e.created_at).total_seconds() * 1000
                    if delta <= assessment_window_ms:
                        group.append(nxt)
                        j += 1
                        continue
                break
            grouped.append(group)
            i = j
        else:
            grouped.append([e])
            i += 1

    timeline: list[dict] = []
    technical: list[dict] = []
    for group in grouped:
        if len(group) > 1:
            # A rater submission was immediately followed by system processing
            # — represent the whole burst as one readable event.
            sub = group[0]
            rt = _rater_label(sub) or "Rater"
            tl = present_event(sub)
            if tl:
                tl["display_title"] = f"Assessment processing completed"
                tl["description"] = f"{rt} questionnaire processed; scores and comparison generated"
                tl["category"] = SYSTEM_CATEGORY
                tl["technical"] = False
                timeline.append(tl)
            for raw in group[1:]:
                t = present_event(raw)
                if t:
                    technical.append(t)
        else:
            e = group[0]
            p = present_event(e)
            if p is None:
                continue
            if e.event_type in ("EVIDENCE_VIEWED",):
                # Evidence viewing is a low-level counselor action; keep it
                # out of the default timeline, available in technical details.
                technical.append(p)
            elif p["technical"]:
                technical.append(p)
            else:
                timeline.append(p)

    # Assessment history derived purely from the real submission events.
    assessment = {}
    for e in ordered:
        if e.event_type == "QUESTIONNAIRE_SUBMITTED":
            rt = (e.event_metadata or {}).get("rater_type")
            if rt:
                assessment[rt] = {"status": "Completed"}
    for e in ordered:
        if e.event_type in ("SCORES_CALCULATED", "DISCREPANCY_CALCULATED", "SIGNAL_GENERATED"):
            assessment["COMPARISON"] = {"status": "Completed"}
        if e.event_type == "REVIEW_CREATED":
            assessment["REVIEW"] = {"status": "Completed"}

    # Sort newest first for the timeline display.
    timeline.sort(key=lambda x: x["occurred_at"], reverse=True)
    technical.sort(key=lambda x: x["occurred_at"], reverse=True)

    return {
        "timeline": timeline,
        "technical": list(reversed(technical)),
        "assessment_history": assessment,
    }
