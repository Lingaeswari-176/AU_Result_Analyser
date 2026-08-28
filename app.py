import io
from typing import Optional
from collections import Counter

import pandas as pd
import streamlit as st

from src.parser import (
    parse_pdf,
    SEM4_CREDITS,
    SEM4_SUBJECT_ORDER,
)


# ============================================================
# SUBJECT NAMES
# ============================================================

SUBJECT_NAMES = {

    "CS3401":
        "Algorithms",

    "CS3451":
        "Introduction to Operating Systems",

    "CS3452":
        "Theory of Computation",

    "CS3461":
        "Operating Systems Laboratory",

    "CS3481":
        "Database Management Systems Laboratory",

    "CS3491":
        "Artificial Intelligence and Machine Learning",

    "CS3492":
        "Database Management Systems",

    "GE3451":
        "Environmental Sciences and Sustainability",
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

        grade = grades.get(code)

        if grade not in GRADE_POINTS:
            continue

        credit = SEM4_CREDITS[code]

        grade_point = GRADE_POINTS[grade]

        total_points += (
            credit * grade_point
        )

        total_credits += credit

    if total_credits == 0:

        return None

    return round(
        total_points / total_credits,
        2
    )


# ============================================================
# STATUS
# ============================================================

def get_status(grades):

    all_grades = [
        grades.get(code)
        for code in SEM4_SUBJECT_ORDER
    ]

    # U has priority
    if any(
        grade == "U"
        for grade in all_grades
    ):
        return "ARREAR"

    # UA
    if any(
        grade == "UA"
        for grade in all_grades
    ):
        return "ABSENT"

    # Special result
    if any(
        grade in SPECIAL_GRADES
        for grade in all_grades
    ):
        return "SPECIAL"

    # All 8 subjects have valid grades
    if all(
        grade in GRADE_POINTS
        for grade in all_grades
    ):
        return "PASS"

    return "INCOMPLETE"


# ============================================================
# ARREARS / ABSENCES
# ============================================================

def get_arrears(grades):

    return [

        code

        for code in SEM4_SUBJECT_ORDER

        if grades.get(code) == "U"

    ]


def get_absences(grades):

    return [

        code

        for code in SEM4_SUBJECT_ORDER

        if grades.get(code) == "UA"

    ]


# ============================================================
# SECTION LOGIC
# ============================================================

def get_section(reg_no):

    suffix = int(reg_no[-3:])

    if 1 <= suffix <= 54:

        return "A"

    if 55 <= suffix <= 109:

        return "B"

    return "C"


def get_section_students(
    students,
    section
):

    return {

        reg: data

        for reg, data in students.items()

        if get_section(reg) == section

    }


# ============================================================
# SECTION ANALYSIS
# ============================================================

def analyse_section(
    students,
    section
):

    selected = get_section_students(
        students,
        section
    )

    records = []

    # --------------------------------------------------------
    # Student-level GPA
    # --------------------------------------------------------

    for reg_no, data in selected.items():

        grades = data.get(
            "grades",
            {}
        )

        gpa = calculate_gpa(
            grades
        )

        status = get_status(
            grades
        )

        records.append({

            "Register No":
                reg_no,

            "Name":
                data.get(
                    "name",
                    ""
                ).strip(),

            "GPA":
                gpa,

            "Status":
                status,

            "U Count":
                len(
                    get_arrears(
                        grades
                    )
                ),

            "UA Count":
                len(
                    get_absences(
                        grades
                    )
                ),
        })

    # --------------------------------------------------------
    # GPA ranking
    #
    # Highest GPA = Rank 1
    # Equal GPA = same rank
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
    # DISPLAY ORDER = REGISTER NUMBER
    # --------------------------------------------------------

    records.sort(
        key=lambda row:
        row["Register No"]
    )

    for row in records:

        row["Rank"] = rank_map.get(
            row["Register No"],
            "-"
        )

    # --------------------------------------------------------
    # CLASS COUNTS
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

            data.get(
                "grades",
                {}
            ).get(code)

            for data in selected.values()

        ]

        grades = [

            grade

            for grade in grades

            if grade is not None

        ]

        total_subject = len(
            grades
        )

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

            "total":
                total_subject,

            "pass":
                pass_count,

            "u":
                u_count,

            "ua":
                ua_count,

            "pass_pct":
                round(
                    pass_count /
                    total_subject *
                    100,
                    1
                )
                if total_subject
                else 0,
        }

    return {

        "section":
            section,

        "records":
            records,

        "total":
            total,

        "passed":
            passed,

        "arrears":
            arrears,

        "absences":
            absences,

        "incomplete":
            incomplete,

        "pass_pct":
            round(
                passed /
                total *
                100,
                1
            )
            if total
            else 0,

        "avg_gpa":
            round(
                sum(gpas) /
                len(gpas),
                2
            )
            if gpas
            else None,

        "highest_gpa":
            max(gpas)
            if gpas
            else None,

        "subject_stats":
            subject_stats,
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

    from reportlab.lib.pagesizes import (
        A4,
        landscape
    )

    from reportlab.lib.styles import (
        getSampleStyleSheet,
        ParagraphStyle
    )

    from reportlab.lib.enums import TA_CENTER

    from reportlab.lib.units import cm

    from reportlab.platypus import (
        SimpleDocTemplate,
        Table,
        TableStyle,
        Paragraph,
        Spacer,
        PageBreak,
    )

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(

        buffer,

        pagesize=landscape(A4),

        rightMargin=0.7 * cm,

        leftMargin=0.7 * cm,

        topMargin=0.7 * cm,

        bottomMargin=0.7 * cm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(

        "ReportTitle",

        parent=styles["Title"],

        fontSize=18,

        alignment=TA_CENTER,

        textColor=colors.HexColor(
            "#12355B"
        ),

        spaceAfter=8,
    )

    heading_style = ParagraphStyle(

        "ReportHeading",

        parent=styles["Heading2"],

        fontSize=12,

        textColor=colors.HexColor(
            "#12355B"
        ),

        spaceAfter=6,
    )

    small_style = ParagraphStyle(

        "Small",

        parent=styles["Normal"],

        fontSize=7,

        leading=9,
    )

    elements = []

    college = (
        institution.get(
            "institution_name"
        )
        or
        "JEPPIAAR ENGINEERING COLLEGE"
    )

    branch = (
        institution.get(
            "branch"
        )
        or
        "104-B.E. Computer Science and Engineering"
    )

    # ========================================================
    # TITLE
    # ========================================================

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

    # ========================================================
    # SUMMARY
    # ========================================================

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

            str(
                analysis["total"]
            ),

            str(
                analysis["passed"]
            ),

            str(
                analysis["arrears"]
            ),

            str(
                analysis["absences"]
            ),

            str(
                analysis["incomplete"]
            ),

            f"{analysis['pass_pct']}%",

            (
                f"{analysis['avg_gpa']:.2f}"
                if analysis["avg_gpa"]
                is not None
                else "N/A"
            ),

            (
                f"{analysis['highest_gpa']:.2f}"
                if analysis["highest_gpa"]
                is not None
                else "N/A"
            ),
        ]
    ]

    summary_table = Table(

        summary_data,

        colWidths=[
            3 * cm
        ] * 8

    )

    summary_table.setStyle(

        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor(
                    "#12355B"
                )
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
            0.4 * cm
        )
    )

    # ========================================================
    # REGISTER-WISE GPA + RANK
    # ========================================================

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
                if row["GPA"]
                is not None
                else "N/A"
            ),

            str(
                row["Rank"]
            ),

            row["Status"],

            str(
                row["U Count"]
            ),

            str(
                row["UA Count"]
            ),
        ])

    rank_table = Table(

        rank_data,

        colWidths=[

            1.0 * cm,

            3.2 * cm,

            7.0 * cm,

            1.8 * cm,

            1.5 * cm,

            3.0 * cm,

            1.2 * cm,

            1.2 * cm,

        ],

        repeatRows=1,
    )

    rank_table.setStyle(

        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor(
                    "#12355B"
                )
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
                colors.HexColor(
                    "#B8C2CC"
                )
            ),

            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    colors.white,
                    colors.HexColor(
                        "#F4F7FA"
                    )
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

    # ========================================================
    # SUBJECT-WISE ANALYSIS
    # ========================================================

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

            SUBJECT_NAMES[code],

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
                colors.HexColor(
                    "#12355B"
                )
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
                    colors.HexColor(
                        "#F4F7FA"
                    )
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
            0.5 * cm
        )
    )

    # ========================================================
    # GRADE MATRIX
    # ========================================================

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

        reg_no = row[
            "Register No"
        ]

        student = students[
            reg_no
        ]

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

                for code
                in SEM4_SUBJECT_ORDER
            ],

            (
                f"{row['GPA']:.2f}"
                if row["GPA"]
                is not None
                else "N/A"
            ),

            str(
                row["Rank"]
            ),
        ])

    matrix_widths = [

        2.9 * cm,

        5.8 * cm,

    ] + [

        1.55 * cm
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
                colors.HexColor(
                    "#12355B"
                )
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
                6.5
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.25,
                colors.HexColor(
                    "#B8C2CC"
                )
            ),

            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    colors.white,
                    colors.HexColor(
                        "#F4F7FA"
                    )
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
            0.4 * cm
        )
    )

    elements.append(

        Paragraph(

            "GPA is calculated using only the "
            "8 official Semester-4 CSE courses "
            "and their syllabus credits. "
            "NCC/additional result columns are "
            "excluded.",

            small_style
        )
    )

    doc.build(
        elements
    )

    buffer.seek(0)

    return buffer.getvalue()


# ============================================================
# STREAMLIT PAGE
# ============================================================

st.set_page_config(

    page_title=
        "AU Result Analyzer | Semester 4",

    page_icon="🎓",

    layout="wide",

    initial_sidebar_state=
        "expanded",
)


# ============================================================
# UI STYLE
# ============================================================

st.markdown("""

<style>

.stApp {

    background:
    linear-gradient(
        135deg,
        #eef5ff 0%,
        #f8fbff 50%,
        #eefaf6 100%
    );

}

.block-container {

    padding:
    1.5rem
    2.2rem
    2rem
    2.2rem;

}


/* SIDEBAR */

[data-testid="stSidebar"] {

    background:
    linear-gradient(
        180deg,
        #102A43 0%,
        #163D5C 55%,
        #0F4C5C 100%
    );

}

[data-testid="stSidebar"] * {

    color: white !important;

}


/* FILE UPLOADER */

[data-testid="stFileUploaderDropzone"] {

    background: white !important;

    border:
    2px dashed
    #2D7DD2 !important;

    border-radius:
    14px !important;

}

[data-testid="stFileUploaderDropzone"] * {

    color:
    #111827 !important;

}

[data-testid="stFileUploaderDropzone"] button {

    color:
    #111827 !important;

    background:
    #eef5ff !important;

    border:
    1px solid
    #9bbce0 !important;

}


/* HERO */

.hero {

    padding: 25px 30px;

    border-radius: 20px;

    background:
    linear-gradient(
        135deg,
        #102A43,
        #1D5D78,
        #1D7A6D
    );

    color: white;

    box-shadow:
    0 12px 35px
    rgba(16,42,67,.18);

    margin-bottom: 20px;

}

.hero h1 {

    color: white !important;

    margin: 0;

    font-size:
    2.1rem;

}

.hero p {

    color:
    #dbeafe;

    margin:
    6px 0 0;

}


/* METRIC */

.metric-card {

    background:
    rgba(255,255,255,.96);

    border-radius:
    16px;

    padding:
    18px;

    box-shadow:
    0 8px 24px
    rgba(15,23,42,.08);

    border:
    1px solid
    #e5edf5;

}

.metric-title {

    color:
    #64748b;

    font-size:
    13px;

    font-weight:
    700;

}

.metric-value {

    color:
    #102A43;

    font-size:
    29px;

    font-weight:
    800;

    margin-top:
    4px;

}


/* SECTION CARD */

.section-card {

    background:
    white;

    border-radius:
    16px;

    padding:
    14px 18px;

    border:
    1px solid
    #e2e8f0;

    margin-bottom:
    12px;

}


/* BUTTON */

.stDownloadButton button {

    border-radius:
    10px !important;

    font-weight:
    700 !important;

}

</style>

""", unsafe_allow_html=True)


# ============================================================
# SESSION STATE
# ============================================================

if "parsed_result" not in st.session_state:

    st.session_state.parsed_result = None


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
            "Automatically extracts Semester 4 "
            "and only 310824... students."
        )
    )

    if uploaded_pdf is not None:

        if (

            st.session_state.parsed_result
            is None

            or st.session_state.get(
                "uploaded_name"
            )
            != uploaded_pdf.name

        ):

            with st.spinner(
                "Parsing Semester 4 result..."
            ):

                st.session_state.parsed_result = (
                    parse_pdf(
                        uploaded_pdf
                    )
                )

                st.session_state.uploaded_name = (
                    uploaded_pdf.name
                )

        result = (
            st.session_state.parsed_result
        )

        st.success(
            f"✅ {result['total_students']} "
            "2024-batch students detected"
        )

        st.info(
            "Only register numbers starting "
            "with 310824 are included."
        )

    st.markdown("---")

    st.markdown(
        "### 📚 Automatic Semester-4 Credits"
    )

    st.caption(
        "No credit input required."
    )

    for code in SEM4_SUBJECT_ORDER:

        st.markdown(

            f"**{code}** — "
            f"{SEM4_CREDITS[code]} credits"

        )

    st.markdown(
        "**Total: 22 credits**"
    )

    st.markdown("---")

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
        "**C:** 110 onward"
    )

    st.caption(
        "301 / 303 / 304 / 701 etc. "
        "also go to C."
    )


# ============================================================
# EMPTY SCREEN
# ============================================================

if not st.session_state.parsed_result:

    st.markdown("""

    <div class="hero">

        <h1>
            🎓 Anna University Result Analyzer
        </h1>

        <p>
            Semester 4 • 2024–2028 CSE
            • Automatic GPA
            • Section-wise Analysis
        </p>

    </div>

    """, unsafe_allow_html=True)

    st.info(
        "Upload the Anna University result PDF "
        "from the left sidebar."
    )

    st.markdown(
        "### 🚀 Automatic Processing"
    )

    st.markdown("""

    1. Detect complete **Semester 4 multi-page block**
    2. Ignore Semesters 1–3 and 5–8
    3. Keep only **310824... 2024 batch**
    4. Read grades using actual PDF column positions
    5. Automatically calculate **GPA**
    6. Automatically split **A / B / C**
    7. Show register-number-wise GPA and rank
    8. Show subject-wise class performance
    9. Download separate A / B / C reports

    """)

    st.stop()


# ============================================================
# DATA
# ============================================================

result = (
    st.session_state.parsed_result
)

students = result["students"]

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
# MAIN HERO
# ============================================================

st.markdown("""

<div class="hero">

    <h1>
        Semester 4 Result Analytics
    </h1>

    <p>
        2024–2028 CSE |
        GPA-only analysis |
        Register-wise ranking |
        Section-wise reports
    </p>

</div>

""", unsafe_allow_html=True)


# ============================================================
# TOP CARDS
# ============================================================

c1, c2, c3, c4 = st.columns(4)


cards = [

    (
        c1,
        "TOTAL 2024 BATCH",
        len(students)
    ),

    (
        c2,
        "SECTION A",
        section_counts.get(
            "A",
            0
        )
    ),

    (
        c3,
        "SECTION B",
        section_counts.get(
            "B",
            0
        )
    ),

    (
        c4,
        "SECTION C",
        section_counts.get(
            "C",
            0
        )
    ),
]


for col, title, value in cards:

    with col:

        st.markdown(

            f"""
            <div class="metric-card">

                <div class="metric-title">
                    {title}
                </div>

                <div class="metric-value">
                    {value}
                </div>

            </div>
            """,

            unsafe_allow_html=True
        )


st.markdown("---")


# ============================================================
# SECTION TABS
# ============================================================

tab_a, tab_b, tab_c = st.tabs([

    "🅰️ Section A",

    "🅱️ Section B",

    "©️ Section C",

])


for tab, section in [

    (tab_a, "A"),

    (tab_b, "B"),

    (tab_c, "C"),

]:

    with tab:

        analysis = analyse_section(
            students,
            section
        )

        # ----------------------------------------------------
        # SECTION HEADER
        # ----------------------------------------------------

        st.markdown(

            f"""
            <div class="section-card">

                <b>
                    Semester 4 — Section {section}
                </b>

                <br>

                <span
                    style="color:#64748b"
                >
                    {analysis['total']}
                    students |
                    GPA calculated automatically
                </span>

            </div>
            """,

            unsafe_allow_html=True
        )


        # ----------------------------------------------------
        # METRICS
        # ----------------------------------------------------

        m1, m2, m3, m4, m5 = (
            st.columns(5)
        )

        m1.metric(
            "Students",
            analysis["total"]
        )

        m2.metric(
            "Passed",
            analysis["passed"]
        )

        m3.metric(
            "Arrears",
            analysis["arrears"]
        )

        m4.metric(
            "Absent",
            analysis["absences"]
        )

        m5.metric(

            "Average GPA",

            (
                f"{analysis['avg_gpa']:.2f}"

                if analysis["avg_gpa"]
                is not None

                else "N/A"
            )
        )


        # ----------------------------------------------------
        # REGISTER NUMBER-WISE
        # ----------------------------------------------------

        st.markdown(
            "### 📋 Register Number-wise GPA & Rank"
        )

        student_df = pd.DataFrame(
            analysis["records"]
        )

        st.dataframe(

            student_df[
                [
                    "Register No",
                    "Name",
                    "GPA",
                    "Rank",
                    "Status",
                    "U Count",
                    "UA Count",
                ]
            ],

            use_container_width=True,

            hide_index=True,

            column_config={

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


        # ----------------------------------------------------
        # SUBJECT-WISE
        # ----------------------------------------------------

        st.markdown(
            "### 📚 Subject-wise Class Performance"
        )

        subject_rows = []

        for code in SEM4_SUBJECT_ORDER:

            stat = (
                analysis[
                    "subject_stats"
                ][code]
            )

            subject_rows.append({

                "Subject Code":
                    code,

                "Subject":
                    SUBJECT_NAMES[code],

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

                "Pass %":
                    st.column_config.NumberColumn(
                        "Pass %",
                        format="%.1f%%"
                    )
            }
        )


        # ----------------------------------------------------
        # GRADE MATRIX
        # ----------------------------------------------------

        st.markdown(
            "### 📝 Student Grade Matrix"
        )

        matrix_rows = []

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

        for reg_no in sorted(
            section_data
        ):

            data = students[
                reg_no
            ]

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

            gpa = calculate_gpa(
                grades
            )

            row["GPA"] = gpa

            row["Rank"] = (
                rank_lookup.get(
                    reg_no,
                    "-"
                )
            )

            matrix_rows.append(
                row
            )

        matrix_df = pd.DataFrame(
            matrix_rows
        )

        st.dataframe(

            matrix_df,

            use_container_width=True,

            hide_index=True,

            column_config={

                "GPA":
                    st.column_config.NumberColumn(
                        "GPA",
                        format="%.2f"
                    )
            }
        )


        # ----------------------------------------------------
        # DOWNLOAD
        # ----------------------------------------------------

        st.markdown(
            "### 📥 Download Section Report"
        )

        st.caption(

            f"This report contains "
            f"**Section {section} only**. "
            "It does not include the other sections."

        )

        try:

            pdf_bytes = create_section_pdf(

                analysis,

                students,

                institution
            )

            st.download_button(

                label=
                    f"📄 Download Section "
                    f"{section} PDF",

                data=pdf_bytes,

                file_name=
                    f"AU_Sem4_2024_Batch_"
                    f"Section_{section}_Report.pdf",

                mime=
                    "application/pdf",

                key=
                    f"download_{section}",

                use_container_width=True,
            )

        except ImportError:

            st.error(
                "ReportLab is not installed. "
                "Run: pip install reportlab"
            )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(

    "AU Result Analyzer • "
    "Semester 4 • 2024–2028 CSE • "
    "Automatic GPA • "
    "Section-wise Analysis"

)