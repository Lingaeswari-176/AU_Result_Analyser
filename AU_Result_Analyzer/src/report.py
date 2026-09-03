from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, PageBreak
)
from reportlab.lib.enums import TA_CENTER
import io

from src.analytics import (
    calculate_gpa,
    get_arrears,
    get_absences,
    student_semester_summary
)


# ============================================================
# HELPERS
# ============================================================

def P(text, style):
    return Paragraph(str(text), style)


def generate_pdf_report(
    students,
    analysis,
    sem_no,
    subject_names,
    credits,
    institution,
    observations,
    section_name=None
):
    """
    Generate GPA-based result report.

    Important:
    - Uses GPA instead of SGPA.
    - Credits are taken from the fixed credits dictionary.
    - Supports section-wise reports.
    - Students are shown register-number-wise.
    - Rank is based on GPA.
    """

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.2 * cm,
        leftMargin=1.2 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#172554"),
        spaceAfter=8
    )

    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=11,
        leading=15,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#475569"),
        spaceAfter=12
    )

    heading_style = ParagraphStyle(
        "ReportHeading",
        parent=styles["Heading2"],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#172554"),
        spaceBefore=8,
        spaceAfter=7
    )

    normal_style = ParagraphStyle(
        "ReportNormal",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        spaceAfter=4
    )

    small_style = ParagraphStyle(
        "Small",
        parent=styles["Normal"],
        fontSize=7.5,
        leading=9
    )

    center_small = ParagraphStyle(
        "CenterSmall",
        parent=small_style,
        alignment=TA_CENTER
    )

    elements = []

    # ========================================================
    # HEADER
    # ========================================================

    institution_name = institution.get(
        "institution_name",
        "Anna University"
    )

    branch = institution.get(
        "branch",
        "CSE"
    )

    institution_code = institution.get(
        "institution_code",
        ""
    )

    section_text = (
        f" | Section {section_name}"
        if section_name
        else ""
    )

    elements.append(
        P(
            institution_name,
            title_style
        )
    )

    elements.append(
        P(
            f"Semester {sem_no} Result Analysis{section_text}",
            subtitle_style
        )
    )

    elements.append(
        P(
            f"<b>Branch:</b> {branch} "
            f"&nbsp;&nbsp; | &nbsp;&nbsp;"
            f"<b>Institution Code:</b> {institution_code}",
            normal_style
        )
    )

    elements.append(Spacer(1, 0.25 * cm))

    # ========================================================
    # SUMMARY
    # ========================================================

    elements.append(
        P("Class Performance Summary", heading_style)
    )

    total = analysis.get("total", 0)
    passed = analysis.get("passed", 0)
    arrears = analysis.get("arrear_students", 0)
    absents = analysis.get("absent_students", 0)

    summary_data = [
        ["Metric", "Value"],
        ["Total Students", str(total)],
        ["Students Passed", str(passed)],
        ["Pass Percentage", f"{analysis.get('pass_pct', 0)}%"],
        ["Students With Arrears", str(arrears)],
        ["Arrear Percentage", f"{analysis.get('arrear_pct', 0)}%"],
        ["Students With Absence", str(absents)],
        ["Absent Percentage", f"{analysis.get('absent_pct', 0)}%"],
    ]

    summary_table = Table(
        summary_data,
        colWidths=[9 * cm, 7 * cm]
    )

    summary_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#172554")
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                9
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.4,
                colors.HexColor("#CBD5E1")
            ),
            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    colors.HexColor("#F8FAFC"),
                    colors.white
                ]
            ),
            (
                "PADDING",
                (0, 0),
                (-1, -1),
                6
            ),
        ])
    )

    elements.append(summary_table)

    # ========================================================
    # OBSERVATIONS
    # ========================================================

    if observations:

        elements.append(
            P("Key Observations", heading_style)
        )

        for observation in observations:
            elements.append(
                P(
                    f"• {observation}",
                    normal_style
                )
            )

    elements.append(PageBreak())

    # ========================================================
    # GPA RANK LIST
    # ========================================================

    elements.append(
        P(
            f"Semester {sem_no} GPA Rank List",
            heading_style
        )
    )

    rank_data = [
        [
            "Rank",
            "Register Number",
            "Student Name",
            "GPA",
            "U",
            "UA",
            "Status"
        ]
    ]

    rank_map = analysis.get("rank_map", {})

    # --------------------------------------------------------
    # IMPORTANT:
    # Roll number order is preserved by sorting register no.
    # Rank itself comes from GPA.
    # --------------------------------------------------------

    rank_list = analysis.get("rank_list", [])

    for reg, name, gpa in rank_list:

        student = students.get(reg, {})

        sem_data = student.get(
            "semesters",
            {}
        ).get(str(sem_no), {})

        grades = sem_data.get(
            "grades",
            {}
        )

        u = get_arrears(grades)
        ua = get_absences(grades)

        if u:
            status = "ARREAR"
        elif ua:
            status = "ABSENT"
        else:
            status = "PASS"

        rank_data.append([
            str(rank_map.get(reg, "-")),
            str(reg),
            str(name),
            f"{gpa:.2f}",
            str(len(u)),
            str(len(ua)),
            status
        ])

    rank_table = Table(
        rank_data,
        repeatRows=1,
        colWidths=[
            1.3 * cm,
            4.0 * cm,
            6.0 * cm,
            2.0 * cm,
            1.3 * cm,
            1.3 * cm,
            2.0 * cm
        ]
    )

    rank_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#172554")
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                7.5
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.35,
                colors.HexColor("#CBD5E1")
            ),
            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    colors.HexColor("#F8FAFC"),
                    colors.white
                ]
            ),
            (
                "ALIGN",
                (0, 0),
                (0, -1),
                "CENTER"
            ),
            (
                "ALIGN",
                (3, 1),
                (5, -1),
                "CENTER"
            ),
            (
                "PADDING",
                (0, 0),
                (-1, -1),
                4
            ),
        ])
    )

    elements.append(rank_table)

    elements.append(PageBreak())

    # ========================================================
    # ROLL NUMBER-WISE STUDENT RESULTS
    # ========================================================

    elements.append(
        P(
            f"Semester {sem_no} Student-wise Results",
            heading_style
        )
    )

    # Roll number order
    sorted_students = sorted(
        students.items(),
        key=lambda x: x[0]
    )

    for reg, data in sorted_students:

        semester_data = data.get(
            "semesters",
            {}
        ).get(str(sem_no))

        if not semester_data:
            continue

        summary = student_semester_summary(
            semester_data,
            credits
        )

        rank = rank_map.get(reg, "-")

        student_name = data.get(
            "name",
            "Unknown"
        )

        elements.append(
            P(
                f"<b>{reg}</b> &nbsp; "
                f"{student_name} &nbsp; | &nbsp; "
                f"Rank: <b>{rank}</b> &nbsp; | &nbsp; "
                f"GPA: <b>{summary['gpa']:.2f}</b> &nbsp; | &nbsp; "
                f"Status: <b>{summary['status']}</b>",
                normal_style
            )
        )

        grade_rows = [
            [
                "Subject Code",
                "Subject",
                "Credits",
                "Grade",
                "Grade Point",
                "Points"
            ]
        ]

        for code, grade in semester_data.get(
            "grades",
            {}
        ).items():

            credit = credits.get(code, 0)

            grade_point = summary.get(
                "grade_points",
                {}
            ).get(code, "-")

            if grade_point == "-":
                points = "-"
            else:
                points = round(
                    float(credit) * float(grade_point),
                    2
                )

            grade_rows.append([
                code,
                subject_names.get(code, code),
                str(credit),
                grade,
                str(grade_point),
                str(points)
            ])

        grade_table = Table(
            grade_rows,
            repeatRows=1,
            colWidths=[
                3.0 * cm,
                6.0 * cm,
                2.0 * cm,
                1.8 * cm,
                2.0 * cm,
                2.0 * cm
            ]
        )

        grade_table.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#334155")
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    7
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.3,
                    colors.HexColor("#CBD5E1")
                ),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        colors.white,
                        colors.HexColor("#F8FAFC")
                    ]
                ),
                (
                    "ALIGN",
                    (2, 1),
                    (-1, -1),
                    "CENTER"
                ),
                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    3
                )
            ])
        )

        elements.append(grade_table)

        arrear_text = ", ".join(
            summary.get("arrears", [])
        ) or "None"

        absent_text = ", ".join(
            summary.get("absences", [])
        ) or "None"

        elements.append(
            P(
                f"U: {len(summary.get('arrears', []))} "
                f"({arrear_text}) &nbsp;&nbsp; "
                f"UA: {len(summary.get('absences', []))} "
                f"({absent_text})",
                small_style
            )
        )

        elements.append(
            Spacer(1, 0.25 * cm)
        )

    elements.append(PageBreak())

    # ========================================================
    # SUBJECT-WISE CLASS PERFORMANCE
    # ========================================================

    elements.append(
        P(
            f"Semester {sem_no} Subject-wise Class Performance",
            heading_style
        )
    )

    subject_data = [
        [
            "Subject Code",
            "Subject",
            "Credits",
            "Students",
            "Pass",
            "U",
            "UA",
            "Pass %"
        ]
    ]

    for code, stat in sorted(
        analysis.get(
            "subject_stats",
            {}
        ).items()
    ):

        subject_data.append([
            code,
            subject_names.get(code, code),
            str(credits.get(code, 0)),
            str(stat.get("total", 0)),
            str(stat.get("pass", 0)),
            str(stat.get("u", 0)),
            str(stat.get("ua", 0)),
            f"{stat.get('pass_pct', 0)}%"
        ])

    subject_table = Table(
        subject_data,
        repeatRows=1,
        colWidths=[
            3.0 * cm,
            6.0 * cm,
            1.8 * cm,
            2.0 * cm,
            1.7 * cm,
            1.5 * cm,
            1.5 * cm,
            2.0 * cm
        ]
    )

    subject_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#172554")
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                7.5
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.35,
                colors.HexColor("#CBD5E1")
            ),
            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    colors.HexColor("#F8FAFC"),
                    colors.white
                ]
            ),
            (
                "ALIGN",
                (2, 1),
                (-1, -1),
                "CENTER"
            ),
            (
                "PADDING",
                (0, 0),
                (-1, -1),
                4
            )
        ])
    )

    elements.append(subject_table)

    # ========================================================
    # SECTION INFORMATION
    # ========================================================

    if section_name:

        elements.append(
            Spacer(1, 0.5 * cm)
        )

        elements.append(
            P(
                f"<b>Section:</b> {section_name}",
                normal_style
            )
        )
        elements.append(
            P(
                "Students included in this report are "
                "automatically filtered according to the "
                "configured register-number section range.",
                small_style
            )
        )

    # ========================================================
    # FOOTER
    # ========================================================

    elements.append(
        Spacer(1, 0.5 * cm)
    )

    elements.append(
        P(
            "AU Result Analyzer | GPA-based Semester Result Analysis",
            center_small
        )
    )

    # ========================================================
    # BUILD PDF
    # ========================================================

    doc.build(elements)

    buffer.seek(0)

    return buffer