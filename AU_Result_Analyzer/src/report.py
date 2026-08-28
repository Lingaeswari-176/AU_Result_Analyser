from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io

def generate_pdf_report(students, analysis, sem_no, subject_names, credits, institution, observations):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=1.5*cm, leftMargin=1.5*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=16, textColor=colors.HexColor('#1a1a2e'), spaceAfter=6)
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=13, textColor=colors.HexColor('#1D9E75'), spaceAfter=4)
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontSize=9, spaceAfter=3)
    center_style = ParagraphStyle('Center', parent=styles['Normal'], alignment=TA_CENTER, fontSize=9)

    elements = []

    # PAGE 1 — SUMMARY
    elements.append(Paragraph(f"{institution.get('institution_name','Anna University Result Analysis')}", title_style))
    elements.append(Paragraph(f"Semester {sem_no} Result Analysis Report", heading_style))
    elements.append(Paragraph(f"Branch: {institution.get('branch','CSE')}  |  Institution Code: {institution.get('institution_code','')}", normal_style))
    elements.append(Spacer(1, 0.4*cm))

    summary_data = [
        ['Metric', 'Value'],
        ['Total Students', str(analysis['total'])],
        ['Students Passed', str(analysis['passed'])],
        ['Pass Percentage', f"{analysis['pass_pct']}%"],
        ['Students with Arrears', str(analysis['arrear_students'])],
        ['Arrear Percentage', f"{analysis['arrear_pct']}%"],
        ['Students with Absences', str(analysis['absent_students'])],
        ['Absent Percentage', f"{analysis['absent_pct']}%"],
    ]
    t = Table(summary_data, colWidths=[9*cm, 7*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1a1a2e')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#f5f5fa'), colors.white]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 0.5*cm))

    elements.append(Paragraph("Key Observations", heading_style))
    for obs in observations:
        elements.append(Paragraph(f"• {obs}", normal_style))

    elements.append(PageBreak())

    # PAGE 2 — RANK LIST
    elements.append(Paragraph("Rank List", heading_style))
    rank_data = [['Rank', 'Register Number', 'Name', 'GPA', 'Status']]
    rank_map = analysis.get('rank_map', {})
    from src.analytics import calculate_gpa, get_arrears, get_absences
    for i, (reg, name, gpa) in enumerate(analysis['rank_list'], 1):
        sem_data = students.get(reg, {}).get('semesters', {}).get(sem_no, {})
        grades = sem_data.get('grades', {})
        arr = get_arrears(grades)
        status = 'PASS' if not arr and not get_absences(grades) else 'ARREAR'
        rank_data.append([str(i), reg, name, str(gpa), status])

    rt = Table(rank_data, colWidths=[1.5*cm, 4*cm, 6*cm, 2.5*cm, 2.5*cm])
    rt.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1a1a2e')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#f5f5fa'), colors.white]),
        ('GRID', (0,0), (-1,-1), 0.3, colors.HexColor('#cccccc')),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(rt)
    elements.append(PageBreak())

    # STUDENT-WISE RESULTS
    elements.append(Paragraph("Student-wise Results", heading_style))
    from src.analytics import student_semester_summary
    for reg, data in students.items():
        if sem_no not in data.get('semesters', {}):
            continue
        sem = data['semesters'][sem_no]
        summary = student_semester_summary(sem, credits)
        rank = rank_map.get(reg, '-')
        elements.append(Paragraph(f"Reg No: {reg}  |  Name: {data.get('name','')}  |  Rank: {rank}  |  GPA: {summary['gpa']}  |  Status: {summary['status']}", normal_style))
        grade_rows = [['Subject Code', 'Subject Name', 'Grade', 'Result']]
        for code, grade in summary['grades'].items():
            result = 'PASS' if grade not in ['U', 'UA'] else ('ARREAR' if grade == 'U' else 'ABSENT')
            grade_rows.append([code, subject_names.get(code, '-'), grade, result])
        if grade_rows:
            gt = Table(grade_rows, colWidths=[3*cm, 6*cm, 2*cm, 3*cm])
            gt.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2e2e5e')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('FONTSIZE', (0,0), (-1,-1), 8),
                ('GRID', (0,0), (-1,-1), 0.3, colors.HexColor('#cccccc')),
                ('PADDING', (0,0), (-1,-1), 4),
            ]))
            elements.append(gt)
        elements.append(Paragraph(f"U: {summary['u_count']}  UA: {summary['ua_count']}  Arrears: {', '.join(summary['arrears']) or 'None'}", normal_style))
        elements.append(Spacer(1, 0.3*cm))

    elements.append(PageBreak())

    # SUBJECT-WISE ANALYSIS
    elements.append(Paragraph("Subject-wise Performance", heading_style))
    sub_data = [['Subject Code', 'Subject Name', 'Total', 'Pass', 'U', 'UA', 'Pass%', 'U%']]
    for code, stat in analysis['subject_stats'].items():
        sub_data.append([
            code, subject_names.get(code, '-'),
            str(stat['total']), str(stat['pass']),
            str(stat['u']), str(stat['ua']),
            f"{stat['pass_pct']}%", f"{stat['u_pct']}%"
        ])
    st = Table(sub_data, colWidths=[2.5*cm, 5*cm, 1.5*cm, 1.5*cm, 1*cm, 1*cm, 1.8*cm, 1.8*cm])
    st.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1a1a2e')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#f5f5fa'), colors.white]),
        ('GRID', (0,0), (-1,-1), 0.3, colors.HexColor('#cccccc')),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(st)

    doc.build(elements)
    buffer.seek(0)
    return buffer

