import streamlit as st
import pandas as pd

from src.parser import parse_pdf

from src.analytics import (
    class_analysis,
    student_semester_summary,
    generate_observations,
    get_arrears,
    get_absences,
    get_section,
    filter_students_by_section
)

from src.report import generate_pdf_report


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AU Result Analyzer",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# STYLE
# ============================================================

st.markdown("""
<style>

.main {
    background: #f8fafc;
}

.block-container {
    padding: 1.5rem 2rem;
}

h1, h2, h3 {
    color: #1a1a2e;
}

.stat-card {
    background: white;
    border-radius: 10px;
    padding: 16px;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    border-top: 4px solid;
}

.pass-card {
    border-color: #10B981;
}

.arrear-card {
    border-color: #EF4444;
}

.absent-card {
    border-color: #F59E0B;
}

.total-card {
    border-color: #3B82F6;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# CURRICULUM CREDIT MAPPING
# ============================================================
#
# IMPORTANT:
# These are course-code -> credit mappings.
# No subject name is entered by the user.
#
# The curriculum PDF gives the official credit structure.
# ============================================================

COURSE_CREDITS = {

    # --------------------------------------------------------
    # SEMESTER 1
    # --------------------------------------------------------

    "IP3151": 0,
    "HS3152": 3,
    "MA3151": 4,
    "PH3151": 3,
    "CY3151": 3,
    "GE3151": 3,
    "GE3152": 1,
    "GE3171": 2,
    "BS3171": 2,
    "GE3172": 1,


    # --------------------------------------------------------
    # SEMESTER 2
    # --------------------------------------------------------

    "HS3252": 2,
    "MA3251": 4,
    "PH3256": 3,
    "BE3251": 3,
    "CS3251": 3,
    "GE3251": 3,
    "GE3252": 1,
    "AD3271": 2,
    "AD3272": 2,
    "GE3271": 1,
    "NCC": 3,


    # --------------------------------------------------------
    # SEMESTER 3
    # --------------------------------------------------------

    "MA3354": 4,
    "CS3351": 3,
    "CS3352": 3,
    "CS3301": 3,
    "CS3391": 4,
    "CS3311": 1.5,
    "CS3381": 1.5,
    "AD3391": 2,
    "GE3361": 2,


    # --------------------------------------------------------
    # SEMESTER 4
    # --------------------------------------------------------

    "CS3452": 3,
    "CS3491": 4,
    "CS3492": 3,
    "CS3401": 4,
    "CS3451": 3,
    "GE3451": 2,
    "CS3461": 1.5,
    "CS3481": 1.5,

    # Optional NCC course
    "NCC": 3,


    # --------------------------------------------------------
    # SEMESTER 5+
    #
    # Add your exact curriculum codes here when required.
    # The analyzer does NOT assume a fixed number of subjects.
    # --------------------------------------------------------

}


# ============================================================
# SUBJECT NAMES
# ============================================================

SUBJECT_NAMES = {

    "IP3151": "Induction Programme",
    "HS3152": "Professional English - I",
    "MA3151": "Matrices and Calculus",
    "PH3151": "Engineering Physics",
    "CY3151": "Engineering Chemistry",
    "GE3151": "Problem Solving and Python Programming",
    "GE3152": "Heritage of Tamils",
    "GE3171": "Problem Solving and Python Programming Laboratory",
    "BS3171": "Physics and Chemistry Laboratory",
    "GE3172": "English Laboratory",

    "HS3252": "Professional English - II",

    "MA3251": "Statistics and Numerical Methods",

    "CS3251": "Foundations of Data Science",

    "CS3351": "Data Structures and Algorithms",

    "CS3352": "Foundations of Data Science",

    "CS3301": "Data Structures",

    "CS3391": "Object Oriented Programming",

    "CS3311": "Object Oriented Programming Laboratory",

    "CS3381": "Data Structures Laboratory",

    "CS3452": "Theory of Computation",

    "CS3491": "Artificial Intelligence and Machine Learning",

    "CS3492": "Database Management Systems",

    "CS3401": "Algorithms",

    "CS3451": "Introduction to Operating Systems",

    "GE3451": "Environmental Sciences and Sustainability",

    "CS3461": "Operating Systems Laboratory",

    "CS3481": "Database Management Systems Laboratory",

}


# ============================================================
# SESSION STATE
# ============================================================

if "data" not in st.session_state:
    st.session_state.data = None


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## 🎓 AU Result Analyzer")

    st.markdown("---")

    uploaded_pdf = st.file_uploader(
        "📄 Upload Anna University Result PDF",
        type=["pdf"]
    )

    if uploaded_pdf:

        with st.spinner(
            "Reading result PDF..."
        ):

            result = parse_pdf(
                uploaded_pdf
            )

        st.session_state.data = result

        student_count = len(
            result.get(
                "students",
                {}
            )
        )

        st.success(
            f"✅ {student_count} students found!"
        )

        semesters = result.get(
            "semesters",
            []
        )

        if semesters:

            st.info(
                "Semesters detected: "
                + ", ".join(semesters)
            )

    st.markdown("---")

    page = st.radio(
        "Navigate",
        [
            "📊 Class Analysis",
            "🔍 Student Search",
            "📋 Rank List",
            "📚 Subject-wise",
            "🚨 Arrear Analysis",
            "📥 Download Report"
        ]
    )


# ============================================================
# MAIN
# ============================================================

st.markdown(
    "# 🎓 Anna University Result Analyzer"
)


if not st.session_state.data:

    st.info(
        "👈 Upload an Anna University result PDF "
        "from the sidebar."
    )

    st.markdown("""
### What this analyzer does

- 📄 Reads student results directly from PDF
- 📚 Detects semester-wise subjects
- 📝 Reads grades automatically
- 💳 Gets credits from curriculum mapping
- 🧮 Calculates GPA
- 🏆 Generates semester-wise rank list
- 📊 Performs subject-wise analysis
- 🚨 Detects U / UA
- 📥 Generates PDF report

**No manual grade entry.**

**No manual subject-name entry.**

**No manual credit entry.**

**No CGPA calculation.**

Rank is based on the selected semester GPA.
""")

    st.stop()


# ============================================================
# DATA
# ============================================================

data = st.session_state.data

students = data.get(
    "students",
    {}
)

institution = data.get(
    "institution",
    {}
)

semesters = data.get(
    "semesters",
    []
)

if not semesters:

    st.error(
        "No semesters were detected."
    )

    st.stop()


# ============================================================
# SEMESTER SELECT
# ============================================================

semesters = sorted(
    semesters,
    key=lambda x: int(x)
)

sem_no = st.selectbox("Select Semester",semesters,key = "sem_select")
if str(sem_no) == "4":
    section = st.selectbox(
        "Select Section",
        ["A","B","C"],
        key = "selection_select"
    )
else:
    section = "All"


# ============================================================
# GET SUBJECTS ONLY FOR SELECTED SEMESTER
# ============================================================

semester_subjects = []

for student in students.values():

    sem_data = student.get(
        "semesters",
        {}
    ).get(
        sem_no
    )

    if not sem_data:
        continue

    for code in sem_data.get(
        "subject_codes",
        []
    ):

        if code not in semester_subjects:

            semester_subjects.append(
                code
            )


# ============================================================
# SHOW SUBJECTS + AUTOMATIC CREDITS
# ============================================================

st.markdown(
    f"### 📚 Semester {sem_no} Subjects"
)

subject_rows = []

for code in semester_subjects:

    subject_rows.append({

        "Subject Code": code,

        "Subject Name":
            SUBJECT_NAMES.get(
                code,
                "-"
            ),

        "Credits":
            COURSE_CREDITS.get(
                code,
                "Not mapped"
            )
    })


if subject_rows:

    st.dataframe(
        pd.DataFrame(subject_rows),
        use_container_width=True,
        hide_index=True
    )

else:

    st.warning(
        "No subjects detected for this semester."
    )


# ============================================================
# CREDIT CHECK
# ============================================================

credits = {}

missing_credits = []

for code in semester_subjects:

    credit = COURSE_CREDITS.get(
        code
    )

    if credit is None:

        missing_credits.append(
            code
        )

    else:

        credits[code] = credit


if missing_credits:

    st.warning(
        "Credits are not mapped for: "
        + ", ".join(missing_credits)
    )

    st.info(
        "These codes must be added to "
        "COURSE_CREDITS before GPA/ranking "
        "can be calculated."
    )


# ============================================================
# FILTER REGISTER PREFIX
# ============================================================

prefix_filter = st.text_input(
    "Register Number Prefix (optional)",
    placeholder="Example: 310824"
)


if str(sem_no) == "4":
    filtered_students = filter_students_by_section(
        students,
        sem_no,
        section
    )

else:

    filtered_students = students


st.markdown(
    f"**Showing {len(filtered_students)} students | "
    f"Semester {sem_no}**"
)

st.markdown("---")


# ============================================================
# CLASS ANALYSIS
# ============================================================

if "Class Analysis" in page:

    analysis = class_analysis(
        filtered_students,
        sem_no,
        credits
    )

    observations = generate_observations(
        analysis,
        SUBJECT_NAMES
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.metric(
            "Total Students",
            analysis["total"]
        )

    with c2:

        st.metric(
            "Passed",
            f"{analysis['passed']} "
            f"({analysis['pass_pct']}%)"
        )

    with c3:

        st.metric(
            "With Arrears",
            f"{analysis['arrear_students']} "
            f"({analysis['arrear_pct']}%)"
        )

    with c4:

        st.metric(
            "With Absence",
            f"{analysis['absent_students']} "
            f"({analysis['absent_pct']}%)"
        )


    st.markdown(
        "### 💡 Key Observations"
    )

    for observation in observations:

        st.markdown(
            f"• {observation}"
        )


# ============================================================
# STUDENT SEARCH
# ============================================================

elif "Student Search" in page:

    st.markdown(
        "### 🔍 Search Student"
    )

    search_reg = st.text_input(
        "Register Number"
    )

    if search_reg:

        student = students.get(
            search_reg.strip()
        )

        if not student:

            st.error(
                "Student not found."
            )

        else:

            st.markdown(
                f"## {student.get('name', 'Unknown')}"
            )

            st.write(
                f"**Register Number:** {search_reg}"
            )

            semesters_for_student = student.get(
                "semesters",
                {}
            )

            for s_no in sorted(
                semesters_for_student.keys(),
                key=lambda x: int(x)
            ):

                sem_data = semesters_for_student[
                    s_no
                ]

                # Only use credits for this semester
                student_credits = {

                    code:
                    COURSE_CREDITS.get(
                        code
                    )

                    for code in sem_data.get(
                        "subject_codes",
                        []
                    )

                    if COURSE_CREDITS.get(
                        code
                    ) is not None
                }

                summary = student_semester_summary(
                    sem_data,
                    student_credits
                )

                st.markdown(
                    f"### Semester {s_no}"
                )

                st.write(
                    f"**GPA:** {summary['gpa']}"
                )

                st.write(
                    f"**Status:** {summary['status']}"
                )

                rows = []

                for code, grade in summary[
                    "grades"
                ].items():

                    rows.append({

                        "Subject Code":
                            code,

                        "Subject Name":
                            SUBJECT_NAMES.get(
                                code,
                                "-"
                            ),

                        "Credit":
                            student_credits.get(
                                code,
                                "-"
                            ),

                        "Grade":
                            grade,

                        "Grade Point":
                            {
                                "O": 10,
                                "A+": 9,
                                "A": 8,
                                "B+": 7,
                                "B": 6,
                                "C": 5,
                                "U": 0,
                                "UA": 0
                            }.get(
                                grade,
                                "-"
                            )
                    })

                if rows:

                    st.dataframe(
                        pd.DataFrame(rows),
                        use_container_width=True,
                        hide_index=True
                    )

                if summary["arrears"]:

                    st.error(
                        "Arrears: "
                        + ", ".join(
                            summary["arrears"]
                        )
                    )

                if summary["absences"]:

                    st.warning(
                        "Absences: "
                        + ", ".join(
                            summary["absences"]
                        )
                    )


# ============================================================
# RANK LIST
# ============================================================

elif "Rank List" in page:

    st.markdown(
        f"### 🏆 Semester {sem_no} GPA Rank List"
    )

    analysis = class_analysis(
        filtered_students,
        sem_no,
        credits
    )

    rows = []

    for rank, item in enumerate(
        analysis["rank_list"],
        start=1
    ):

        reg_no = item[0]

        name = item[1]

        gpa = item[2]

        sem_data = filtered_students[
            reg_no
        ]["semesters"][sem_no]

        grades = sem_data.get(
            "grades",
            {}
        )

        arrears = get_arrears(
            grades
        )

        absences = get_absences(
            grades
        )

        rows.append({

            "Rank": rank,

            "Register No":
                reg_no,

            "Name":
                name,

            "GPA":
                gpa,

            "U Count":
                len(arrears),

            "UA Count":
                len(absences),

            "Status":
                "PASS"
                if not arrears and not absences
                else "ARREAR"
                if arrears
                else "ABSENT"
        })


    if rows:

        df = pd.DataFrame(rows)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        csv = df.to_csv(
            index=False
        ).encode()

        st.download_button(
            "📥 Download Rank List CSV",
            csv,
            f"Sem_{sem_no}_GPA_Rank_List.csv",
            "text/csv"
        )


# ============================================================
# SUBJECT ANALYSIS
# ============================================================

elif "Subject-wise" in page:

    st.markdown(
        f"### 📚 Semester {sem_no} Subject Analysis"
    )

    analysis = class_analysis(
        filtered_students,
        sem_no,
        credits
    )

    rows = []

    for code, stat in analysis[
        "subject_stats"
    ].items():

        rows.append({

            "Subject Code":
                code,

            "Subject Name":
                SUBJECT_NAMES.get(
                    code,
                    "-"
                ),

            "Credit":
                credits.get(
                    code,
                    "-"
                ),

            "Total":
                stat["total"],

            "Pass":
                stat["pass"],

            "U":
                stat["u"],

            "UA":
                stat["ua"],

            "Pass %":
                f"{stat['pass_pct']}%",

            "Arrear %":
                f"{stat['u_pct']}%",

            "Absent %":
                f"{stat['ua_pct']}%"
        })


    if rows:

        df = pd.DataFrame(rows)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# ARREAR ANALYSIS
# ============================================================

elif "Arrear" in page:

    st.markdown(
        f"### 🚨 Semester {sem_no} Arrear Analysis"
    )

    arrear_rows = []

    for reg_no, student in filtered_students.items():

        sem_data = student.get(
            "semesters",
            {}
        ).get(
            sem_no
        )

        if not sem_data:
            continue

        grades = sem_data.get(
            "grades",
            {}
        )

        arrears = get_arrears(
            grades
        )

        absences = get_absences(
            grades
        )

        if arrears or absences:

            arrear_rows.append({

                "Register No":
                    reg_no,

                "Name":
                    student.get(
                        "name",
                        ""
                    ),

                "Arrear Subjects":
                    ", ".join(
                        arrears
                    )
                    if arrears
                    else "-",

                "U Count":
                    len(arrears),

                "Absent Subjects":
                    ", ".join(
                        absences
                    )
                    if absences
                    else "-",

                "UA Count":
                    len(absences)
            })


    if arrear_rows:

        df = pd.DataFrame(
            arrear_rows
        )

        df = df.sort_values(
            "U Count",
            ascending=False
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.success(
            "🎉 No students with arrears "
            "or absences in this semester!"
        )


# ============================================================
# DOWNLOAD REPORT
# ============================================================

elif "Download" in page:

    st.markdown(
        "### 📥 Generate PDF Report"
    )

    report_type = st.radio(
        "Report Type",
        [
            "Complete Report",
            "Semester-wise",
            "Individual Student"
        ]
    )

    reg = None

    if report_type == "Individual Student":

        reg = st.text_input(
            "Register Number"
        )


    if st.button(
        "📄 Generate PDF Report"
    ):

        with st.spinner(
            "Generating PDF..."
        ):

            analysis = class_analysis(
                filtered_students,
                sem_no,
                credits
            )

            observations = generate_observations(
                analysis,
                SUBJECT_NAMES
            )

            target_students = filtered_students

            if reg:

                if reg in students:

                    target_students = {
                        reg:
                        students[reg]
                    }

                else:

                    st.error(
                        "Register number not found."
                    )

                    st.stop()


            buf = generate_pdf_report(

                target_students,

                analysis,

                sem_no,

                SUBJECT_NAMES,

                credits,

                institution,

                observations
            )


        filename = (
            f"AU_Result_Sem{sem_no}_"
            f"{prefix_filter or 'All'}.pdf"
        )

        st.download_button(

            "📥 Download PDF",

            buf,

            filename,

            "application/pdf"
        )

        st.success(
            "PDF ready!"
        )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.markdown(
    "<center style='color:#888;font-size:12px'>"
    "AU Result Analyzer"
    "</center>",
    unsafe_allow_html=True
)
