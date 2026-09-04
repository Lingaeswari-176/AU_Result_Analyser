import io
from collections import Counter
from typing import Optional

import pandas as pd
import streamlit as st

from src.parser import (
    parse_pdf,
    SEM4_CREDITS,
    SEM4_SUBJECT_ORDER,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AU Result Analyzer",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# SUBJECT NAMES
# ============================================================

SUBJECT_NAMES = {
    "CS3401": "Algorithms",
    "CS3451": "Introduction to Operating Systems",
    "CS3452": "Theory of Computation",
    "CS3461": "Operating Systems Laboratory",
    "CS3481": "Database Management Systems Laboratory",
    "CS3491": "Artificial Intelligence and Machine Learning",
    "CS3492": "Database Management Systems",
    "GE3451": "Environmental Sciences and Sustainability",
    "NM1134": "Foundation Skills For Employability",
}


# ============================================================
# GRADE POINTS
# ============================================================

GRADE_POINTS = {
    "O": 10,
    "A+": 9,
    "A": 8,
    "B+": 7,
    "B": 6,
    "C": 5,
    "U": 0,
    "UA": 0,
}

SPECIAL_GRADES = {
    "W",
    "I",
    "WH",
    "WH1",
}


# ============================================================
# GPA CALCULATION
# ============================================================

def calculate_gpa(grades: dict) -> Optional[float]:

    total_points = 0.0
    total_credits = 0.0

    for code in SEM4_SUBJECT_ORDER:

        grade = str(grades.get(code, "")).strip().upper()

        if grade not in GRADE_POINTS:
            continue

        credit = SEM4_CREDITS.get(code, 0)

        grade_point = GRADE_POINTS[grade]

        total_points += credit * grade_point
        total_credits += credit

    if total_credits == 0:
        return None

    return round(total_points / total_credits, 2)


# ============================================================
# STATUS
# ============================================================

def get_status(grades):

    all_grades = [
        str(grades.get(code, "")).strip().upper()
        for code in SEM4_SUBJECT_ORDER
    ]

    # U has highest priority
    if any(grade == "U" for grade in all_grades):
        return "ARREAR"

    # UA = absent
    if any(grade == "UA" for grade in all_grades):
        return "ABSENT"

    # Special result
    if any(grade in SPECIAL_GRADES for grade in all_grades):
        return "SPECIAL"

    # All subjects have valid grades
    if all(grade in GRADE_POINTS for grade in all_grades):
        return "PASS"

    return "INCOMPLETE"


# ============================================================
# ARREARS
# ============================================================

def get_arrears(grades):

    return [
        code
        for code in SEM4_SUBJECT_ORDER
        if str(grades.get(code, "")).strip().upper() == "U"
    ]


# ============================================================
# ABSENCES
# ============================================================

def get_absences(grades):

    return [
        code
        for code in SEM4_SUBJECT_ORDER
        if str(grades.get(code, "")).strip().upper() == "UA"
    ]


# ============================================================
# SECTION LOGIC
#
# 001 - 054 = A
# 055 - 109 = B
# 110 onwards = C
#
# Example:
# 31082401001 -> A
# 31082401054 -> A
# 31082401055 -> B
# 31082401109 -> B
# 31082401110 -> C
# ============================================================

def get_section(reg_no):

    reg_no = str(reg_no).strip()

    try:
        suffix = int(reg_no[-3:])
    except (ValueError, TypeError):
        return "C"

    if 1 <= suffix <= 54:
        return "A"

    if 55 <= suffix <= 109:
        return "B"

    return "C"


# ============================================================
# GET SECTION STUDENTS
# ============================================================

def get_section_students(students, section):

    return {
        reg: data
        for reg, data in students.items()
        if get_section(reg) == section
    }


# ============================================================
# SECTION ANALYSIS
# ============================================================

def analyse_section(students, section):

    selected = get_section_students(
        students,
        section
    )

    records = []

    # --------------------------------------------------------
    # STUDENT-WISE GPA
    # --------------------------------------------------------

    for reg_no, data in selected.items():

        grades = data.get(
            "grades",
            {}
        )

        gpa = calculate_gpa(grades)

        status = get_status(grades)

        records.append({

            "Register No": str(reg_no),

            "Name": str(
                data.get(
                    "name",
                    ""
                )
            ).strip(),

            "GPA": gpa,

            "Status": status,

            "U Count": len(
                get_arrears(grades)
            ),

            "UA Count": len(
                get_absences(grades)
            ),
        })

    # --------------------------------------------------------
    # RANKING
    # --------------------------------------------------------

    ranked = [
        row
        for row in records
        if row["GPA"] is not None
    ]

    ranked.sort(
        key=lambda row: (
            -row["GPA"],
            row["Register No"]
        )
    )

    rank_map = {}

    previous_gpa = None
    previous_rank = 0

    for position, row in enumerate(
        ranked,
        start=1
    ):

        if (
            previous_gpa is not None
            and row["GPA"] == previous_gpa
        ):
            rank = previous_rank
        else:
            rank = position

        rank_map[
            row["Register No"]
        ] = rank

        previous_gpa = row["GPA"]
        previous_rank = rank

    # --------------------------------------------------------
    # REGISTER NUMBER ORDER
    # --------------------------------------------------------

    records.sort(
        key=lambda row: row["Register No"]
    )

    for row in records:

        row["Rank"] = rank_map.get(
            row["Register No"],
            "-"
        )

    # --------------------------------------------------------
    # COUNTS
    # --------------------------------------------------------

    total = len(records)

    passed = sum(
        row["Status"] == "PASS"
        for row in records
    )

    arrears = sum(
        row["Status"] == "ARREAR"
        for row in records
    )

    absences = sum(
        row["Status"] == "ABSENT"
        for row in records
    )

    incomplete = sum(
        row["Status"] == "INCOMPLETE"
        for row in records
    )

    gpas = [
        row["GPA"]
        for row in records
        if row["GPA"] is not None
    ]

    # --------------------------------------------------------
    # SUBJECT-WISE ANALYSIS
    # --------------------------------------------------------

    subject_stats = {}

    for code in SEM4_SUBJECT_ORDER:

        grades = [
            str(
                data.get(
                    "grades",
                    {}
                ).get(code, "")
            ).strip().upper()

            for data in selected.values()
        ]

        grades = [
            grade
            for grade in grades
            if grade
        ]

        total_subject = len(grades)

        pass_count = sum(
            grade in GRADE_POINTS
            and grade not in {"U", "UA"}
            for grade in grades
        )

        u_count = sum(
            grade == "U"
            for grade in grades
        )

        ua_count = sum(
            grade == "UA"
            for grade in grades
        )

        subject_stats[code] = {

            "total": total_subject,

            "pass": pass_count,

            "u": u_count,

            "ua": ua_count,

            "pass_pct": round(
                pass_count /
                total_subject *
                100,
                1
            )
            if total_subject
            else 0,
        }

    return {

        "section": section,

        "records": records,

        "total": total,

        "passed": passed,

        "arrears": arrears,

        "absences": absences,

        "incomplete": incomplete,

        "pass_pct": round(
            passed /
            total *
            100,
            1
        )
        if total
        else 0,

        "avg_gpa": round(
            sum(gpas) /
            len(gpas),
            2
        )
        if gpas
        else None,

        "highest_gpa": max(gpas)
        if gpas
        else None,

        "subject_stats": subject_stats,
    }


# ============================================================
# PDF REPORT
# ============================================================

def create_section_pdf(
    analysis,
    students,
    institution
):

    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import (
        ParagraphStyle,
        getSampleStyleSheet,
    )
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        Paragraph,
        PageBreak,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=0.6 * cm,
        leftMargin=0.6 * cm,
        topMargin=0.6 * cm,
        bottomMargin=0.6 * cm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=17,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#12355B"),
        spaceAfter=7,
    )

    heading_style = ParagraphStyle(
        "ReportHeading",
        parent=styles["Heading2"],
        fontSize=11,
        textColor=colors.HexColor("#12355B"),
        spaceAfter=5,
    )

    small_style = ParagraphStyle(
        "Small",
        parent=styles["Normal"],
        fontSize=7,
        leading=9,
    )

    elements = []

    college = (
        institution.get("institution_name")
        or "JEPPIAAR ENGINEERING COLLEGE"
    )

    branch = (
        institution.get("branch")
        or "B.E. Computer Science and Engineering"
    )

    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    elements.append(
        Paragraph(
            college,
            title_style
        )
    )

    elements.append(
        Paragraph(
            "SEMESTER 4 — SECTION "
            f"{analysis['section']} "
            "GPA RESULT ANALYSIS",
            heading_style
        )
    )

    elements.append(
        Paragraph(
            "Batch: 2024–2028 | "
            f"Section: {analysis['section']} | "
            f"{branch}",
            small_style
        )
    )

    elements.append(
        Spacer(
            1,
            0.25 * cm
        )
    )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    summary_data = [

        [
            "Total",
            "Passed",
            "Arrears",
            "Absent",
            "Incomplete",
            "Pass %",
            "Average GPA",
            "Highest GPA",
        ],

        [

            str(analysis["total"]),

            str(analysis["passed"]),

            str(analysis["arrears"]),

            str(analysis["absences"]),

            str(analysis["incomplete"]),

            f"{analysis['pass_pct']}%",

            (
                f"{analysis['avg_gpa']:.2f}"
                if analysis["avg_gpa"] is not None
                else "N/A"
            ),

            (
                f"{analysis['highest_gpa']:.2f}"
                if analysis["highest_gpa"] is not None
                else "N/A"
            ),
        ]
    ]

    summary_table = Table(
        summary_data,
        colWidths=[
            3.2 * cm
        ] * 8
    )

    summary_table.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#12355B")
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
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER"
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.4,
                colors.grey
            ),

            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                8
            ),

            (
                "PADDING",
                (0, 0),
                (-1, -1),
                5
            ),
        ])
    )

    elements.append(
        summary_table
    )

    elements.append(
        Spacer(
            1,
            0.35 * cm
        )
    )

    # --------------------------------------------------------
    # REGISTER-WISE GPA & RANK
    # --------------------------------------------------------

    elements.append(
        Paragraph(
            "Register Number-wise GPA & Rank",
            heading_style
        )
    )

    rank_data = [[

        "S.No",
        "Register No",
        "Student Name",
        "GPA",
        "Rank",
        "Status",
        "U",
        "UA",

    ]]

    for i, row in enumerate(
        analysis["records"],
        start=1
    ):

        rank_data.append([

            str(i),

            row["Register No"],

            row["Name"],

            (
                f"{row['GPA']:.2f}"
                if row["GPA"] is not None
                else "N/A"
            ),

            str(row["Rank"]),

            row["Status"],

            str(row["U Count"]),

            str(row["UA Count"]),
        ])

    rank_table = Table(
        rank_data,
        colWidths=[

            0.9 * cm,
            3.2 * cm,
            7.0 * cm,
            1.6 * cm,
            1.4 * cm,
            2.5 * cm,
            1.1 * cm,
            1.1 * cm,

        ],
        repeatRows=1,
    )

    rank_table.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#12355B")
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
                0.25,
                colors.HexColor("#B8C2CC")
            ),

            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    colors.white,
                    colors.HexColor("#F4F7FA")
                ]
            ),

            (
                "ALIGN",
                (0, 0),
                (1, -1),
                "CENTER"
            ),

            (
                "ALIGN",
                (3, 1),
                (-1, -1),
                "CENTER"
            ),

            (
                "PADDING",
                (0, 0),
                (-1, -1),
                3
            ),
        ])
    )

    elements.append(
        rank_table
    )

    elements.append(
        PageBreak()
    )

    # --------------------------------------------------------
    # SUBJECT-WISE ANALYSIS
    # --------------------------------------------------------

    elements.append(
        Paragraph(
            "Subject-wise Class Performance",
            heading_style
        )
    )

    subject_data = [[

        "Subject Code",
        "Subject",
        "Credits",
        "Appeared",
        "Pass",
        "U",
        "UA",
        "Pass %",

    ]]

    for code in SEM4_SUBJECT_ORDER:

        stat = analysis[
            "subject_stats"
        ][code]

        subject_data.append([

            code,

            SUBJECT_NAMES.get(
                code,
                code
            ),

            str(
                SEM4_CREDITS[code]
            ),

            str(
                stat["total"]
            ),

            str(
                stat["pass"]
            ),

            str(
                stat["u"]
            ),

            str(
                stat["ua"]
            ),

            f"{stat['pass_pct']}%",
        ])

    subject_table = Table(
        subject_data,
        colWidths=[

            3 * cm,
            7 * cm,
            2 * cm,
            2 * cm,
            2 * cm,
            1.5 * cm,
            1.5 * cm,
            2 * cm,

        ],
        repeatRows=1
    )

    subject_table.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#12355B")
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
                8
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.3,
                colors.grey
            ),

            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    colors.white,
                    colors.HexColor("#F4F7FA")
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
                5
            ),
        ])
    )

    elements.append(
        subject_table
    )

    elements.append(
        Spacer(
            1,
            0.4 * cm
        )
    )

    # --------------------------------------------------------
    # GRADE MATRIX
    # --------------------------------------------------------

    elements.append(
        Paragraph(
            "Student Grade Matrix",
            heading_style
        )
    )

    matrix_data = [[

        "Register No",
        "Name",
        *SEM4_SUBJECT_ORDER,
        "GPA",
        "Rank",

    ]]

    for row in analysis["records"]:

        reg_no = row["Register No"]

        student = students.get(
            reg_no,
            {}
        )

        grades = student.get(
            "grades",
            {}
        )

        matrix_data.append([

            reg_no,

            row["Name"],

            *[
                grades.get(
                    code,
                    "-"
                )
                for code in SEM4_SUBJECT_ORDER
            ],

            (
                f"{row['GPA']:.2f}"
                if row["GPA"] is not None
                else "N/A"
            ),

            str(row["Rank"]),
        ])

    matrix_widths = [

        2.9 * cm,
        5.8 * cm,

    ] + [

        1.45 * cm
        for _ in SEM4_SUBJECT_ORDER

    ] + [

        1.7 * cm,
        1.5 * cm,
    ]

    matrix_table = Table(
        matrix_data,
        colWidths=matrix_widths,
        repeatRows=1
    )

    matrix_table.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#12355B")
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
                6.2
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.25,
                colors.HexColor("#B8C2CC")
            ),

            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    colors.white,
                    colors.HexColor("#F4F7FA")
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
            ),
        ])
    )

    elements.append(
        matrix_table
    )

    elements.append(
        Spacer(
            1,
            0.35 * cm
        )
    )

    elements.append(
        Paragraph(
            "GPA is calculated automatically using "
            "the official Semester-4 CSE courses "
            "and their predefined syllabus credits "
            "(24 total credits). NCC/additional "
            "result columns are excluded.",
            small_style
        )
    )

    doc.build(elements)

    buffer.seek(0)

    return buffer.getvalue()

# ============================================================
# RESPONSIVE UI - LAPTOP + MOBILE
# ============================================================

st.markdown("""
<style>

/* ============================================================
   GLOBAL
============================================================ */

html, body, [data-testid="stAppViewContainer"] {
    overflow-x: hidden !important;
}

[data-testid="stAppViewContainer"] {
    background: linear-gradient(
        135deg,
        #f4f8fc 0%,
        #eef6f8 100%
    ) !important;
}

/* Main content */
[data-testid="stMainBlockContainer"],
.block-container {
    color: #172033 !important;
    max-width: 100% !important;
}

/* Force normal dark text in main area */
[data-testid="stMainBlockContainer"] p,
[data-testid="stMainBlockContainer"] span,
[data-testid="stMainBlockContainer"] label,
[data-testid="stMainBlockContainer"] div {
    color: inherit;
}

/* Headings */
[data-testid="stMainBlockContainer"] h1,
[data-testid="stMainBlockContainer"] h2,
[data-testid="stMainBlockContainer"] h3,
[data-testid="stMainBlockContainer"] h4 {
    color: #102a43 !important;
    font-weight: 750 !important;
}

/* ============================================================
   SIDEBAR
============================================================ */

[data-testid="stSidebar"] {
    background: linear-gradient(
        180deg,
        #102f4d 0%,
        #12556a 100%
    ) !important;
}

[data-testid="stSidebar"] * {
    color: #ffffff !important;
}

/* Sidebar file uploader */
[data-testid="stSidebar"] [data-testid="stFileUploader"] {
    background: #ffffff !important;
    border-radius: 14px !important;
    padding: 8px !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploader"] * {
    color: #172033 !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
    background: #ffffff !important;
    border: 2px dashed #2b8ac6 !important;
    border-radius: 12px !important;
}

/* ============================================================
   FILE UPLOADER - MAIN
============================================================ */

[data-testid="stFileUploader"] {
    width: 100% !important;
}

[data-testid="stFileUploaderDropzone"] {
    background: #ffffff !important;
    border: 2px dashed #2584c6 !important;
    border-radius: 12px !important;
}

/* ============================================================
   METRIC CARDS
============================================================ */

[data-testid="stMetric"] {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 16px !important;
    padding: 16px !important;
    box-shadow: 0 5px 18px rgba(15, 40, 60, 0.08) !important;
    min-height: 100px !important;
}

/* Metric label */
[data-testid="stMetricLabel"] {
    color: #526274 !important;
    font-weight: 600 !important;
}

/* Metric number */
[data-testid="stMetricValue"] {
    color: #12355b !important;
    font-weight: 800 !important;
}

/* Metric delta */
[data-testid="stMetricDelta"] {
    color: #526274 !important;
}

/* ============================================================
   DATAFRAMES / TABLES
============================================================ */

[data-testid="stDataFrame"] {
    width: 100% !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}

/* ============================================================
   BUTTONS
============================================================ */

.stButton > button,
.stDownloadButton > button {
    width: 100% !important;
    min-height: 44px !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
}

/* ============================================================
   TABS
============================================================ */

[data-baseweb="tab-list"] {
    width: 100% !important;
    gap: 4px !important;
}

[data-baseweb="tab"] {
    font-weight: 700 !important;
    white-space: nowrap !important;
}

/* ============================================================
   INFO / SUCCESS / WARNING BOXES
============================================================ */

[data-testid="stAlert"] {
    border-radius: 12px !important;
}

/* ============================================================
   MOBILE - <= 768px
============================================================ */

@media screen and (max-width: 768px) {

    /* Main page */
    [data-testid="stMainBlockContainer"],
    .block-container {
        width: 100% !important;
        max-width: 100% !important;
        padding-left: 12px !important;
        padding-right: 12px !important;
        padding-top: 12px !important;
        padding-bottom: 40px !important;
    }

    /* Headings */
    [data-testid="stMainBlockContainer"] h1 {
        font-size: 1.55rem !important;
        line-height: 1.25 !important;
        margin-bottom: 8px !important;
    }

    [data-testid="stMainBlockContainer"] h2 {
        font-size: 1.3rem !important;
    }

    [data-testid="stMainBlockContainer"] h3 {
        font-size: 1.08rem !important;
    }

    /* --------------------------------------------------------
       ALL COLUMNS BECOME FULL WIDTH
    -------------------------------------------------------- */

    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: column !important;
        width: 100% !important;
        gap: 10px !important;
    }

    [data-testid="stHorizontalBlock"] > [data-testid="column"] {
        width: 100% !important;
        min-width: 100% !important;
        flex: 1 1 100% !important;
    }

    /* --------------------------------------------------------
       METRICS
    -------------------------------------------------------- */

    [data-testid="stMetric"] {
        width: 100% !important;
        min-height: 85px !important;
        padding: 12px !important;
        margin-bottom: 4px !important;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.78rem !important;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.45rem !important;
    }

    /* --------------------------------------------------------
       TABS
    -------------------------------------------------------- */

    [data-baseweb="tab-list"] {
        display: flex !important;
        width: 100% !important;
        overflow-x: auto !important;
        scrollbar-width: none !important;
    }

    [data-baseweb="tab-list"]::-webkit-scrollbar {
        display: none !important;
    }

    [data-baseweb="tab"] {
        flex: 1 0 auto !important;
        padding-left: 12px !important;
        padding-right: 12px !important;
        font-size: 0.85rem !important;
    }

    /* --------------------------------------------------------
       TABLES
    -------------------------------------------------------- */

    [data-testid="stDataFrame"] {
        width: 100% !important;
        max-width: 100% !important;
        overflow-x: auto !important;
    }

    /* --------------------------------------------------------
       DOWNLOAD BUTTON
    -------------------------------------------------------- */

    .stDownloadButton {
        width: 100% !important;
    }

    .stDownloadButton > button {
        width: 100% !important;
    }

    /* --------------------------------------------------------
       SIDEBAR
    -------------------------------------------------------- */

    [data-testid="stSidebar"] {
        width: 85vw !important;
        max-width: 330px !important;
    }
}


/* ============================================================
   VERY SMALL PHONES - <= 480px
============================================================ */

@media screen and (max-width: 480px) {

    [data-testid="stMainBlockContainer"],
    .block-container {
        padding-left: 8px !important;
        padding-right: 8px !important;
    }

    [data-testid="stMainBlockContainer"] h1 {
        font-size: 1.3rem !important;
    }

    [data-testid="stMainBlockContainer"] h2 {
        font-size: 1.15rem !important;
    }

    [data-testid="stMainBlockContainer"] h3 {
        font-size: 1rem !important;
    }

    [data-testid="stMetric"] {
        padding: 10px !important;
        border-radius: 12px !important;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.25rem !important;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.7rem !important;
    }

    [data-baseweb="tab"] {
        font-size: 0.78rem !important;
        padding-left: 9px !important;
        padding-right: 9px !important;
    }
}

</style>
""", unsafe_allow_html=True)

# ============================================================
# SESSION STATE
# ============================================================

if "parsed_result" not in st.session_state:
    st.session_state.parsed_result = None

if "uploaded_name" not in st.session_state:
    st.session_state.uploaded_name = None


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "## 🎓 AU Result Analyzer"
    )

    st.caption(
        "Semester 4 • CSE • Batch 2024–2028"
    )

    st.markdown("---")

    uploaded_pdf = st.file_uploader(
        "📄 Upload Anna University Result PDF",
        type=["pdf"],
        help=(
            "Upload the complete Anna University "
            "result PDF. Semester 4 and 2024 batch "
            "students are processed automatically."
        ),
    )

    if uploaded_pdf is not None:

        if (
            st.session_state.parsed_result is None
            or st.session_state.uploaded_name
            != uploaded_pdf.name
        ):

            with st.spinner(
                "⏳ Parsing Semester 4 result..."
            ):

                try:

                    st.session_state.parsed_result = (
                        parse_pdf(uploaded_pdf)
                    )

                    st.session_state.uploaded_name = (
                        uploaded_pdf.name
                    )

                except Exception as e:

                    st.error(
                        "Unable to parse the PDF."
                    )

                    st.exception(e)

                    st.stop()

        result = (
            st.session_state.parsed_result
        )

        st.success(
            f"✅ {result['total_students']} "
            "2024-batch students detected"
        )

        st.info(
            "Only register numbers beginning "
            "with 310824 are included."
        )

    st.markdown("---")

    # --------------------------------------------------------
    # CREDITS
    # --------------------------------------------------------

    st.markdown(
        "### 📚 Semester-4 Credits"
    )

    st.caption(
        "Credits are predefined. No manual input required."
    )

    for code in SEM4_SUBJECT_ORDER:

        st.markdown(
            f"**{code}** — "
            f"{SEM4_CREDITS[code]} credits"
        )

    total_credits = sum(
        SEM4_CREDITS.get(
            code,
            0
        )
        for code in SEM4_SUBJECT_ORDER
    )

    st.markdown(
        f"**Total: {total_credits} credits**"
    )

    st.markdown("---")

    # --------------------------------------------------------
    # SECTIONS
    # --------------------------------------------------------

    st.markdown(
        "### 🧩 Automatic Sections"
    )

    st.markdown(
        "**A:** 001 – 054"
    )

    st.markdown(
        "**B:** 055 – 109"
    )

    st.markdown(
        "**C:** 110 onwards"
    )

    st.caption(
        "Any suffix 110+ such as 110, 301, 303, "
        "304, 701 etc. is placed in Section C."
    )


# ============================================================
# EMPTY SCREEN
# ============================================================

if not st.session_state.parsed_result:

    st.title(
        "🎓 Anna University Result Analyzer"
    )

    st.caption(
        "Semester 4 • 2024–2028 CSE • "
        "Automatic GPA • Section-wise Analysis"
    )

    st.info(
        "📄 Upload the Anna University result "
        "PDF from the left sidebar."
    )

    st.markdown(
        "### 🚀 Automatic Processing"
    )

    st.markdown(
        """
        **1.** Detect Semester 4 result data  
        **2.** Keep only the 2024 batch  
        **3.** Keep only register numbers starting with `310824`  
        **4.** Read the subject grades  
        **5.** Apply predefined Semester-4 credits  
        **6.** Calculate GPA automatically  
        **7.** Split students into A / B / C sections  
        **8.** Calculate register-number-wise rank  
        **9.** Generate subject-wise class performance  
        **10.** Download separate A / B / C reports
        """
    )

    st.stop()


# ============================================================
# RESULT DATA
# ============================================================

result = st.session_state.parsed_result

students = result.get(
    "students",
    {}
)

institution = result.get(
    "institution",
    {}
)


# ============================================================
# SECTION COUNTS
# ============================================================

section_counts = Counter(
    get_section(reg)
    for reg in students
)


# ============================================================
# HERO
# ============================================================

st.title(
    "📊 Semester 4 Result Analytics"
)

st.caption(
    "2024–2028 CSE  •  Automatic GPA  •  "
    "Register-wise Ranking  •  Section-wise Reports"
)


# ============================================================
# TOP SUMMARY
# ============================================================
#
# IMPORTANT:
# Use 2 columns instead of 4/5.
# This makes the layout much better on mobile.
# ============================================================

c1, c2 = st.columns(2)

with c1:

    st.metric(
        "TOTAL 2024 BATCH",
        len(students)
    )

with c2:

    st.metric(
        "SECTION A",
        section_counts.get(
            "A",
            0
        )
    )


c3, c4 = st.columns(2)

with c3:

    st.metric(
        "SECTION B",
        section_counts.get(
            "B",
            0
        )
    )

with c4:

    st.metric(
        "SECTION C",
        section_counts.get(
            "C",
            0
        )
    )


st.markdown("---")


# ============================================================
# SECTION TABS
# ============================================================

tab_a, tab_b, tab_c = st.tabs(
    [
        "🅰️ A",
        "🅱️ B",
        "©️ C",
    ]
)


# ============================================================
# FUNCTION TO DISPLAY SECTION
# ============================================================

def display_section(section):

    analysis = analyse_section(
        students,
        section
    )

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    st.subheader(
        f"Semester 4 — Section {section}"
    )

    st.caption(
        f"{analysis['total']} students • "
        "GPA calculated automatically"
    )

    # --------------------------------------------------------
    # SECTION METRICS
    # --------------------------------------------------------

    m1, m2 = st.columns(2)

    with m1:

        st.metric(
            "Students",
            analysis["total"]
        )

    with m2:

        st.metric(
            "Passed",
            analysis["passed"]
        )

    m3, m4 = st.columns(2)

    with m3:

        st.metric(
            "Arrears",
            analysis["arrears"]
        )

    with m4:

        st.metric(
            "Absent",
            analysis["absences"]
        )

    m5, m6 = st.columns(2)

    with m5:

        st.metric(
            "Average GPA",
            (
                f"{analysis['avg_gpa']:.2f}"
                if analysis["avg_gpa"] is not None
                else "N/A"
            )
        )

    with m6:

        st.metric(
            "Highest GPA",
            (
                f"{analysis['highest_gpa']:.2f}"
                if analysis["highest_gpa"] is not None
                else "N/A"
            )
        )

    # --------------------------------------------------------
    # REGISTER-WISE GPA
    # --------------------------------------------------------

    st.markdown(
        "### 📋 Register Number-wise GPA & Rank"
    )

    student_df = pd.DataFrame(
        analysis["records"]
    )

    if not student_df.empty:

        display_df = student_df[
            [
                "Register No",
                "Name",
                "GPA",
                "Rank",
                "Status",
                "U Count",
                "UA Count",
            ]
        ].copy()

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            height=430,
            column_config={

                "Register No":
                    st.column_config.TextColumn(
                        "Register No"
                    ),

                "Name":
                    st.column_config.TextColumn(
                        "Name"
                    ),

                "GPA":
                    st.column_config.NumberColumn(
                        "GPA",
                        format="%.2f"
                    ),

                "Rank":
                    st.column_config.NumberColumn(
                        "Rank"
                    ),

                "Status":
                    st.column_config.TextColumn(
                        "Status"
                    ),

                "U Count":
                    st.column_config.NumberColumn(
                        "U"
                    ),

                "UA Count":
                    st.column_config.NumberColumn(
                        "UA"
                    ),
            }
        )

    else:

        st.warning(
            f"No students found in Section {section}."
        )

    # --------------------------------------------------------
    # SUBJECT-WISE PERFORMANCE
    # --------------------------------------------------------

    st.markdown(
        "### 📚 Subject-wise Class Performance"
    )

    subject_rows = []

    for code in SEM4_SUBJECT_ORDER:

        stat = analysis[
            "subject_stats"
        ][code]

        subject_rows.append({

            "Subject Code":
                code,

            "Subject":
                SUBJECT_NAMES.get(
                    code,
                    code
                ),

            "Credits":
                SEM4_CREDITS[code],

            "Appeared":
                stat["total"],

            "Pass":
                stat["pass"],

            "U":
                stat["u"],

            "UA":
                stat["ua"],

            "Pass %":
                stat["pass_pct"],
        })

    subject_df = pd.DataFrame(
        subject_rows
    )

    st.dataframe(
        subject_df,
        use_container_width=True,
        hide_index=True,
        column_config={

            "Subject Code":
                st.column_config.TextColumn(
                    "Code"
                ),

            "Subject":
                st.column_config.TextColumn(
                    "Subject"
                ),

            "Credits":
                st.column_config.NumberColumn(
                    "Credits"
                ),

            "Appeared":
                st.column_config.NumberColumn(
                    "Appeared"
                ),

            "Pass":
                st.column_config.NumberColumn(
                    "Pass"
                ),

            "U":
                st.column_config.NumberColumn(
                    "U"
                ),

            "UA":
                st.column_config.NumberColumn(
                    "UA"
                ),

            "Pass %":
                st.column_config.NumberColumn(
                    "Pass %",
                    format="%.1f%%"
                ),
        }
    )

    # --------------------------------------------------------
    # GRADE MATRIX
    # --------------------------------------------------------

    st.markdown(
        "### 📝 Student Grade Matrix"
    )

    section_data = get_section_students(
        students,
        section
    )

    rank_lookup = {
        row["Register No"]:
            row["Rank"]
        for row
        in analysis["records"]
    }

    matrix_rows = []

    for reg_no in sorted(
        section_data
    ):

        data = students.get(
            reg_no,
            {}
        )

        grades = data.get(
            "grades",
            {}
        )

        row = {

            "Register No":
                reg_no,

            "Name":
                data.get(
                    "name",
                    ""
                ),
        }

        for code in SEM4_SUBJECT_ORDER:

            row[code] = (
                grades.get(
                    code,
                    "-"
                )
            )

        row["GPA"] = calculate_gpa(
            grades
        )

        row["Rank"] = rank_lookup.get(
            reg_no,
            "-"
        )

        matrix_rows.append(
            row
        )

    matrix_df = pd.DataFrame(
        matrix_rows
    )

    if not matrix_df.empty:

        st.dataframe(
            matrix_df,
            use_container_width=True,
            hide_index=True,
            height=430,
            column_config={

                "Register No":
                    st.column_config.TextColumn(
                        "Register No"
                    ),

                "GPA":
                    st.column_config.NumberColumn(
                        "GPA",
                        format="%.2f"
                    ),

                "Rank":
                    st.column_config.NumberColumn(
                        "Rank"
                    ),
            }
        )

    # --------------------------------------------------------
    # DOWNLOAD
    # --------------------------------------------------------

    st.markdown(
        "### 📥 Download Section Report"
    )

    st.caption(
        f"Only Section {section} is included "
        "in this PDF report."
    )

    try:

        pdf_bytes = create_section_pdf(
            analysis,
            students,
            institution
        )

        st.download_button(

            label=(
                f"📄 Download Section "
                f"{section} PDF"
            ),

            data=pdf_bytes,

            file_name=(
                f"AU_Sem4_2024_Batch_"
                f"Section_{section}_Report.pdf"
            ),

            mime="application/pdf",

            key=(
                f"download_section_"
                f"{section}"
            ),

            use_container_width=True,
        )

    except Exception as e:

        st.error(
            "Could not generate the PDF report."
        )

        st.exception(e)


# ============================================================
# DISPLAY A
# ============================================================

with tab_a:

    display_section("A")


# ============================================================
# DISPLAY B
# ============================================================

with tab_b:

    display_section("B")


# ============================================================
# DISPLAY C
# ============================================================

with tab_c:

    display_section("C")


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "AU Result Analyzer • "
    "Semester 4 • 2024–2028 CSE • "
    "Automatic GPA • "
    "Section-wise Analysis • "
    "A: 001–054 • B: 055–109 • C: 110+"
)
