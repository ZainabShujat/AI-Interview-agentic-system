import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # Header (skip on page 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, "Career Readiness & Performance Report")
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.5)
            self.line(54, 742, 558, 742)
            
        # Footer
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 40, page_text)
        self.drawString(54, 40, "Confidential • HireIntel AI Assessment Services")
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(54, 52, 558, 52)
        
        self.restoreState()

def generate_report_pdf(report_data: dict) -> bytes:
    buffer = io.BytesIO()
    
    # 0.75 in margin
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=72,
        bottomMargin=72
    )
    
    styles = getSampleStyleSheet()
    
    # Custom elegant styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=15
    )
    
    section_style = ParagraphStyle(
        'DocSection',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=18,
        spaceAfter=8,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#334155"),
        spaceAfter=8
    )
    
    bullet_style = ParagraphStyle(
        'DocBullet',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=6
    )

    meta_label_style = ParagraphStyle(
        'MetaLabel',
        parent=body_style,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor("#475569")
    )

    story = []
    
    # Title / Header
    story.append(Paragraph("Career Readiness Report", title_style))
    story.append(Spacer(1, 10))
    
    # Metadata Block Table
    overall_score = report_data.get("overallScore", 80)
    recommendation = report_data.get("recommendation", "Hire")
    
    meta_data = [
        [Paragraph("Target Role Title:", meta_label_style), Paragraph("Senior Software Engineer", body_style)],
        [Paragraph("Readiness Index:", meta_label_style), Paragraph(f"<b>{overall_score} / 100</b>", body_style)],
        [Paragraph("Hiring Outlook:", meta_label_style), Paragraph(f"<b>{recommendation}</b>", body_style)],
        [Paragraph("Assessment Date:", meta_label_style), Paragraph("June 23, 2026", body_style)]
    ]
    
    meta_table = Table(meta_data, colWidths=[110, 394])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 4),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor("#f1f5f9")),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 15))
    
    # Executive Summary
    story.append(Paragraph("Executive Summary", section_style))
    summary_text = report_data.get("summary", "Summary not available.")
    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 15))
    
    # Capabilities Scores Table
    story.append(Paragraph("Dimension Performance Rating", section_style))
    scores_data = [["Dimension", "Rating / 100"]]
    for item in report_data.get("dimensionScores", []):
        scores_data.append([item.get("subject"), f"{item.get('A')}%"])
        
    scores_table = Table(scores_data, colWidths=[250, 254])
    scores_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f8fafc")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#0f172a")),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(scores_table)
    story.append(Spacer(1, 15))

    # Executive Communication & Presence Review
    story.append(Paragraph("Communication & Executive Presence Review", section_style))
    story.append(Paragraph("This section evaluates delivery pacing, articulation latency, response structure, and executive presence indicators against standard professional communication benchmarks.", body_style))
    story.append(Spacer(1, 4))
    
    comm_profile = report_data.get("communicationProfile") or {}
    
    # Table for Qualitative Insights
    insights_data = [
        [Paragraph("<b>Communication Style:</b>", meta_label_style), Paragraph(comm_profile.get("style", "Structured & Technical"), body_style)],
        [Paragraph("<b>Executive Presence:</b>", meta_label_style), Paragraph(comm_profile.get("presence", "Measured & Authoritative"), body_style)],
        [Paragraph("<b>Interview Readiness:</b>", meta_label_style), Paragraph(comm_profile.get("readiness", "Highly Proficient"), body_style)],
        [Paragraph("<b>Response Quality:</b>", meta_label_style), Paragraph(comm_profile.get("quality", "Exhibits clear microservice design principles"), body_style)],
    ]
    insights_table = Table(insights_data, colWidths=[140, 364])
    insights_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 4),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor("#f1f5f9")),
    ]))
    story.append(insights_table)
    story.append(Spacer(1, 10))
    
    # 1. STAR Framework Table
    star_fw = comm_profile.get("starFramework") or {"situation": True, "task": True, "action": True, "result": True}
    def get_status_str(flag):
        return "<b>Covered</b>" if flag else "<font color='#ef4444'>Missing / Not Detected</font>"
        
    star_data = [
        [Paragraph("<b>STAR Framework Phase</b>", meta_label_style), Paragraph("<b>Assessment Status</b>", meta_label_style)],
        [Paragraph("<b>Situation</b> (Context, background and scenario setup)", body_style), Paragraph(get_status_str(star_fw.get('situation')), body_style)],
        [Paragraph("<b>Task</b> (Defined responsibilities, scope, and objectives)", body_style), Paragraph(get_status_str(star_fw.get('task')), body_style)],
        [Paragraph("<b>Action</b> (Execution steps, technical design, and collaboration)", body_style), Paragraph(get_status_str(star_fw.get('action')), body_style)],
        [Paragraph("<b>Result</b> (Performance metrics, business outcomes, and key learnings)", body_style), Paragraph(get_status_str(star_fw.get('result')), body_style)]
    ]
    star_table = Table(star_data, colWidths=[350, 154])
    star_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f8fafc")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    
    story.append(Paragraph("STAR Framework Structure Alignment", ParagraphStyle('SubSectionSTAR', parent=section_style, fontSize=11, spaceBefore=8, spaceAfter=4)))
    story.append(Paragraph("Evaluates the structural completeness of explanations using the standard Situation, Task, Action, and Result (STAR) model.", body_style))
    story.append(Spacer(1, 4))
    story.append(star_table)
    story.append(Spacer(1, 10))
    
    # 2. Advanced Executive Metrics Table
    exec_scores = comm_profile.get("executiveScores") or {"practicality": 80, "problemSolving": 78, "businessThinking": 75}
    exec_data = [
        [Paragraph("<b>Executive Performance Metric</b>", meta_label_style), Paragraph("<b>Score / 100</b>", meta_label_style)],
        [Paragraph("<b>Practicality</b> (Demonstrates realistic and executable engineering approaches)", body_style), Paragraph(f"{exec_scores.get('practicality')}%", body_style)],
        [Paragraph("<b>Problem Solving</b> (Core query constraints and technical hurdles resolved)", body_style), Paragraph(f"{exec_scores.get('problemSolving')}%", body_style)],
        [Paragraph("<b>Business Thinking</b> (Alignment of system design trade-offs with commercial strategy)", body_style), Paragraph(f"{exec_scores.get('businessThinking')}%", body_style)]
    ]
    exec_table = Table(exec_data, colWidths=[380, 124])
    exec_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f8fafc")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    
    story.append(Paragraph("Advanced Executive Presence Metrics", ParagraphStyle('SubSectionExec', parent=section_style, fontSize=11, spaceBefore=8, spaceAfter=4)))
    story.append(Paragraph("Averages technical practicality, problem solving skills, and high-level commercial alignment across all simulation questions.", body_style))
    story.append(Spacer(1, 4))
    story.append(exec_table)
    story.append(Spacer(1, 10))
    
    # Table for Delivery Assessment Metrics
    story.append(Paragraph("Delivery Assessment Metrics", ParagraphStyle('SubSection', parent=section_style, fontSize=11, spaceBefore=8, spaceAfter=4)))
    
    metrics = comm_profile.get("metrics") or {}
    metrics_rows = [["Metric", "Value", "Rating", "Feedback"]]
    
    metrics_keys = [
        ("speakingPace", "Speaking Pace"),
        ("responseLength", "Response Length"),
        ("fillerWords", "Filler Word Frequency"),
        ("hesitation", "Hesitation & Latency"),
        ("completeness", "Answer Completeness")
    ]
    
    for key, label in metrics_keys:
        m = metrics.get(key) or {}
        val = m.get("value", "N/A")
        rat = m.get("rating", "N/A")
        fb = m.get("feedback", "N/A")
        metrics_rows.append([label, val, rat, fb])
        
    metrics_table = Table(metrics_rows, colWidths=[110, 80, 80, 234])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f8fafc")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#0f172a")),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 5),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 10))
    
    # Observations
    story.append(Paragraph("Behavioral & Delivery Observations", ParagraphStyle('SubSection2', parent=section_style, fontSize=11, spaceBefore=8, spaceAfter=4)))
    for obs in comm_profile.get("observations", []):
        story.append(Paragraph(f"• {obs}", bullet_style))
    story.append(Spacer(1, 15))
    
    # Strengths
    story.append(Paragraph("Competitive Advantages", section_style))
    for str_text in report_data.get("strengths", []):
        story.append(Paragraph(f"• {str_text}", bullet_style))
    story.append(Spacer(1, 15))
    
    # Gap Analysis Recommendations
    story.append(Paragraph("Development Areas", section_style))
    for rec_text in report_data.get("recommendations", []):
        story.append(Paragraph(f"• {rec_text}", bullet_style))
        
    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
