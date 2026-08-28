

GRADE_POINTS = {
    "O": 10,
    "A+": 9,
    "A": 8,
    "B+": 7,
    "B": 6,
    "C": 5,
    "U": 0,
    "UA": 0,

    # Do not include these in GPA
    "W": None,
    "I": None,
    "WH": None,
    "WH1": None
}


def calculate_gpa(grades, credits):
    """
    GPA = SUM(grade point × credit) / SUM(valid credits)

    credits is only for the selected semester.
    """

    total_points = 0.0
    total_credits = 0.0

    for code, grade in grades.items():

        grade = grade.upper().strip()

        credit = credits.get(code)

        if credit is None:
            continue

        point = GRADE_POINTS.get(grade)

        if point is None:
            continue

        try:
            credit = float(credit)
        except (ValueError, TypeError):
            continue

        if credit <= 0:
            continue

        total_points += point * credit
        total_credits += credit

    if total_credits == 0:
        return 0.0

    return round(total_points / total_credits, 2)


def get_arrears(grades):
    return [
        code
        for code, grade in grades.items()
        if grade.upper() == "U"
    ]


def get_absences(grades):
    return [
        code
        for code, grade in grades.items()
        if grade.upper() == "UA"
    ]


def student_semester_summary(sem_data, credits):

    grades = sem_data.get("grades", {})

    arrears = get_arrears(grades)

    absences = get_absences(grades)

    gpa = calculate_gpa(
        grades,
        credits
    )

    if arrears:
        status = "ARREAR"

    elif absences:
        status = "ABSENT"

    else:
        status = "PASS"

    return {

        "subject_codes":
            sem_data.get("subject_codes", []),

        "grades":
            grades,

        "arrears":
            arrears,

        "absences":
            absences,

        "gpa":
            gpa,

        "status":
            status,

        "u_count":
            len(arrears),

        "ua_count":
            len(absences)
    }


def class_analysis(
    students,
    sem_no,
    credits
):

    total = 0
    passed = 0
    arrear_students = 0
    absent_students = 0

    subject_stats = {}

    gpa_list = []

    for reg_no, student in students.items():

        semesters = student.get(
            "semesters",
            {}
        )

        if sem_no not in semesters:
            continue

        total += 1

        sem_data = semesters[sem_no]

        grades = sem_data.get(
            "grades",
            {}
        )

        arrears = get_arrears(grades)

        absences = get_absences(grades)

        if not arrears and not absences:
            passed += 1

        if arrears:
            arrear_students += 1

        if absences:
            absent_students += 1

        gpa = calculate_gpa(
            grades,
            credits
        )

        gpa_list.append(
            (
                reg_no,
                student.get("name", ""),
                gpa
            )
        )

        # Subject analysis
        for code, grade in grades.items():

            if code not in subject_stats:

                subject_stats[code] = {
                    "total": 0,
                    "pass": 0,
                    "u": 0,
                    "ua": 0,
                    "grades": []
                }

            stat = subject_stats[code]

            stat["total"] += 1

            stat["grades"].append(
                grade
            )

            if grade == "U":

                stat["u"] += 1

            elif grade == "UA":

                stat["ua"] += 1

            else:

                stat["pass"] += 1

    # Percentages
    for code, stat in subject_stats.items():

        total_subject = stat["total"]

        if total_subject:

            stat["pass_pct"] = round(
                stat["pass"]
                / total_subject
                * 100,
                1
            )

            stat["u_pct"] = round(
                stat["u"]
                / total_subject
                * 100,
                1
            )

            stat["ua_pct"] = round(
                stat["ua"]
                / total_subject
                * 100,
                1
            )

        else:

            stat["pass_pct"] = 0

            stat["u_pct"] = 0

            stat["ua_pct"] = 0

    # Highest GPA first
    gpa_list.sort(
        key=lambda x: x[2],
        reverse=True
    )

    rank_map = {}

    for position, item in enumerate(
        gpa_list,
        start=1
    ):

        rank_map[item[0]] = position

    return {

        "total": total,

        "passed": passed,

        "arrear_students":
            arrear_students,

        "absent_students":
            absent_students,

        "pass_pct":
            round(
                passed / total * 100,
                1
            ) if total else 0,

        "arrear_pct":
            round(
                arrear_students
                / total
                * 100,
                1
            ) if total else 0,

        "absent_pct":
            round(
                absent_students
                / total
                * 100,
                1
            ) if total else 0,

        "subject_stats":
            subject_stats,

        "rank_list":
            gpa_list,

        "rank_map":
            rank_map
    }


def generate_observations(
    analysis,
    subject_names=None
):

    if subject_names is None:
        subject_names = {}

    observations = []

    stats = analysis.get(
        "subject_stats",
        {}
    )

    if stats:

        worst = max(
            stats,
            key=lambda code:
            stats[code]["u"]
        )

        best = max(
            stats,
            key=lambda code:
            stats[code]["pass_pct"]
        )

        if stats[worst]["u"] > 0:

            name = subject_names.get(
                worst,
                worst
            )

            observations.append(
                f"{name} ({worst}) "
                f"has the highest number "
                f"of U grades: "
                f"{stats[worst]['u']}."
            )

        name = subject_names.get(
            best,
            best
        )

        observations.append(
            f"{name} ({best}) has the "
            f"highest pass percentage "
            f"of {stats[best]['pass_pct']}%."
        )

    total = analysis.get(
        "total",
        0
    )

    passed = analysis.get(
        "passed",
        0
    )

    arrears = analysis.get(
        "arrear_students",
        0
    )

    absences = analysis.get(
        "absent_students",
        0
    )

    if total:

        observations.append(
            f"Overall class pass "
            f"percentage is "
            f"{analysis.get('pass_pct', 0)}% "
            f"({passed}/{total} students)."
        )

    if arrears:

        observations.append(
            f"{arrears} student(s) "
            f"have at least one arrear."
        )

    if absences:

        observations.append(
            f"{absences} student(s) "
            f"were absent in at least "
            f"one subject."
        )

    rank_list = analysis.get(
        "rank_list",
        []
    )

    if rank_list:

        top = rank_list[0]

        observations.append(
            f"Top performer: "
            f"{top[1]} ({top[0]}) "
            f"with GPA {top[2]}."
        )


    return observations
def get_section(reg_no: str, sem_no: str = "4") -> str:
    """
    Automatically determine section from register number.
    Applicable to Semester 4.
    
    001-054 -> A
    055-109 -> B
    110 onwards -> C
    """

    if str(sem_no) != "4":
        return "All"

    digits = ''.join(ch for ch in str(reg_no) if ch.isdigit())

    if len(digits) < 3:
        return "Unknown"

    try:
        roll_no = int(digits[-3:])
    except ValueError:
        return "Unknown"

    if 1 <= roll_no <= 54:
        return "A"
    elif 55 <= roll_no <= 109:
        return "B"
    elif roll_no >= 110:
        return "C"

    return "Unknown"


def filter_students_by_section(students: dict, sem_no: str, section: str) -> dict:
    """
    Automatically filter students according to section.
    Only Semester 4 uses A/B/C section division.
    """

    if str(sem_no) != "4" or section == "All":
        return students

    return {
        reg: data
        for reg, data in students.items()
        if get_section(reg, sem_no) == section
        and sem_no in data.get("semesters", {})
    }


def get_section_students(students: dict, sem_no: str) -> dict:
    """
    Returns all three section groups for Semester 4.
    """

    if str(sem_no) != "4":
        return {"All": students}

    return {
        "A": filter_students_by_section(students, sem_no, "A"),
        "B": filter_students_by_section(students, sem_no, "B"),
        "C": filter_students_by_section(students, sem_no, "C")
    }
