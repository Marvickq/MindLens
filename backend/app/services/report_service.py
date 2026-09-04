"""
Report Service
Generates an auditable PDF report using ReportLab with mandatory disclaimer.
"""
import io
import uuid
from datetime import datetime
from sqlmodel import Session, select

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from app.models.case import StudentCase
from app.models.dimension_score import DimensionScore
from app.models.discrepancy import Signal
from app.models.counselor_review import CounselorReview
from app.models.assessment import Dimension

DISCLAIMER_TEXT = (
    "MindLens is a decision-support prototype. It does not provide a diagnosis "
    "or individual clinical risk prediction. Final interpretation and action remain "
    "with a qualified professional."
)


def generate_case_pdf_report(case_id: uuid.UUID, db: Session) -> bytes:
    case = db.get(StudentCase, case_id)
    if not case:
        raise ValueError("Case not found")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#013f53'),
    )
    h2_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#24566b'),
        spaceBefore=12,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#1a1c1d'),
    )
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Italic'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#71787d'),
    )

    story = []

    # Title & Metadata
    story.append(Paragraph("MindLens Assessment Review", title_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"Student Reference: <b>{case.display_name}</b> | Status: {case.status.value} | Date: {datetime.now().strftime('%Y-%m-%d')}", body_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#c1c7cc'), spaceAfter=15))

    # Mandatory Disclaimer Banner
    story.append(Paragraph(f"<b>Notice:</b> {DISCLAIMER_TEXT}", disclaimer_style))
    story.append(Spacer(1, 15))

    # Section 1: Multi-Rater Dimension Scores
    story.append(Paragraph("1. Six-Dimension Multi-Perspective Overview", h2_style))
    
    dimensions = db.exec(select(Dimension).where(Dimension.active == True).order_by(Dimension.display_order)).all()
    scores = db.exec(select(DimensionScore).where(DimensionScore.case_id == case_id)).all()
    
    score_lookup = {}
    for s in scores:
        score_lookup[(str(s.dimension_id), s.rater_type)] = f"{s.score:.1f}"

    table_data = [["Dimension", "Parent Score", "Teacher Score", "Adolescent Score"]]
    for d in dimensions:
        p_val = score_lookup.get((str(d.id), 'PARENT'), 'N/A')
        t_val = score_lookup.get((str(d.id), 'TEACHER'), 'N/A')
        a_val = score_lookup.get((str(d.id), 'ADOLESCENT'), 'N/A')
        table_data.append([d.label, p_val, t_val, a_val])

    t = Table(table_data, colWidths=[200, 100, 100, 100])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#c1e5f4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#013f53')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e2e4')),
    ]))
    story.append(t)
    story.append(Spacer(1, 15))

    # Section 2: Surfaced Signals
    story.append(Paragraph("2. Meaningful Discrepancy Signals", h2_style))
    signals = db.exec(select(Signal).where(Signal.case_id == case_id)).all()
    if not signals:
        story.append(Paragraph("No major perspective divergence detected.", body_style))
    else:
        for sig in signals:
            story.append(Paragraph(f"• <b>{sig.title}</b> ({sig.signal_level.value})", body_style))
            story.append(Paragraph(f"  {sig.description}", body_style))
            story.append(Spacer(1, 4))

    story.append(Spacer(1, 15))

    # Section 3: Counselor Review
    story.append(Paragraph("3. Counselor Review & Recommendation", h2_style))
    review = db.exec(select(CounselorReview).where(CounselorReview.case_id == case_id).order_by(CounselorReview.created_at.desc())).first()
    if review:
        story.append(Paragraph(f"<b>Action Selected:</b> {review.action.value}", body_style))
        story.append(Paragraph(f"<b>Notes:</b> {review.note or 'No notes provided.'}", body_style))
    else:
        story.append(Paragraph("Pending Counselor Review.", body_style))

    doc.build(story)
    return buffer.getvalue()
