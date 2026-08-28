# src/analytics.py

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
    "W": None,
    "I": None,
    "WH": None,
    "WH1": None,
}


# ============================================================
# GET GRADE POINT
# ============================================================

def get_grade_point(grade):
    if not grade:
        return None

    grade = str(grade).strip().upper()

    return GRADE_POINTS.get(grade)


# ============================================================
# CALCULATE GPA
# ============================================================

def calculate_gpa(grades: dict, credits: dict) -> float:
    """
    GPA = Sum(Credit × Grade Point) / Sum(Credits)

    Example:
        3 credit subject + O  = 3 × 10 = 30
        4 credit subject + A+ = 4 × 9  = 36
    """

    total_points = 0.0
    total_credits = 0.0

    for code, grade in grades.items():

        code = str(code).strip().upper()
        grade = str(grade).strip().upper()

        credit = credits.get(code)

        if credit is None:
            continue

        grade_point = get_grade_point(grade)

        # W/I/WH/WH1 are not included in GPA
        if grade_point is None:
            continue

        try:
            credit = float(credit)
        except (ValueError, TypeError):
            continue

        if credit <= 0:
            continue

        total_points += credit * grade_point
        total_credits += credit

    if total_credits == 0:
        return 0.0

    return round(total_points / total_credits, 2)


# ============================================================
# GET ARREARS
# ============================================================

def get_arrears(grades: dict) -> list:
    return [
        code
        for code, grade in grades.items()
        if str(grade).strip().upper() == "U"
    ]


# ============================================================
# GET ABSENCES
# ============================================================

def get_absences(grades: dict) -> list:
    return [
        code
        for code, grade in grades.items()
        if str(grade).strip().upper() == "UA"
    ]


# ============================================================
# STUDENT SEMESTER SUMMARY
# ============================================================

def student_semester_summary(
    sem_data: dict,
    credits: dict
) -> dict:

    grades = sem_data.get("grades", {})

    arrears = get_arrears(grades)
    absences = get_absences(grades)

    gpa = calculate_gpa(
        grades,
        credits
    )

    # Grade points for report
    grade_points = {}

    for code, grade in grades.items():

        gp = get_grade_point(grade)

        if gp is not None:
            grade_points[code] = gp
        else:
            grade_points[code] = "-"

    if arrears:
        status = "ARREAR"
    elif absences:
        status = "ABSENT"
    else:
        status = "PASS"

    return {
        "grades": grades,
        "arrears": arrears,
        "absences": absences,
        "gpa": gpa,
        "grade_points": grade_points,
        "status": status,
        "u_count": len(arrears),
        "ua_count": len(absences)
    }


# ============================================================
# CLASS ANALYSIS
# ============================================================

def class_analysis(
    students: dict,
    sem_no: str,
    credits: dict
) -> dict:

    total = 0
    passed = 0
    arrear_count = 0
    absent_count = 0

    subject_stats = {}
    gpa_list = []

    # --------------------------------------------------------
    # PROCESS STUDENTS
    # --------------------------------------------------------

    for reg, data in students.items():

        semesters = data.get(
            "semesters",
            {}
        )

        sem_data = semesters.get(
            str(sem_no)
        )

        if not sem_data:
            continue

        total += 1

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

        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        if not arrears and not absences:
            passed += 1

        if arrears:
            arrear_count += 1

        if absences:
            absent_count += 1

        # ----------------------------------------------------
        # GPA
        # ----------------------------------------------------

        gpa = calculate_gpa(
            grades,
            credits
        )

        gpa_list.append(
            (
                reg,
                data.get("name", ""),
                gpa
            )
        )

        # ----------------------------------------------------
        # SUBJECT ANALYSIS
        # ----------------------------------------------------

        for code, grade in grades.items():

            code = str(code).strip().upper()
            grade = str(grade).strip().upper()

            if code not in subject_stats:

                subject_stats[code] = {
                    "total": 0,
                    "pass": 0,
                    "u": 0,
                    "ua": 0,
                    "grades": []
                }

            subject_stats[code]["total"] += 1

            subject_stats[code]["grades"].append(
                grade
            )

            if grade == "U":

                subject_stats[code]["u"] += 1

            elif grade == "UA":

                subject_stats[code]["ua"] += 1

            else:

                subject_stats[code]["pass"] += 1

    # ========================================================
    # SUBJECT PERCENTAGES
    # ========================================================

    for code, stat in subject_stats.items():

        total_subject = stat["total"]

        if total_subject > 0:

            stat["pass_pct"] = round(
                stat["pass"] /
                total_subject *
                100,
                1
            )

            stat["u_pct"] = round(
                stat["u"] /
                total_subject *
                100,
                1
            )

            stat["ua_pct"] = round(
                stat["ua"] /
                total_subject *
                100,
                1
            )

        else:

            stat["pass_pct"] = 0
            stat["u_pct"] = 0
            stat["ua_pct"] = 0

    # ========================================================
    # RANKING
    # ========================================================

    # Highest GPA gets Rank 1.
    #
    # If two students have the same GPA,
    # register number is used as tie-breaker.
    #
    # This keeps the result deterministic.

    gpa_list_sorted = sorted(
        gpa_list,
        key=lambda x: (
            -x[2],
            x[0]
        )
    )

    rank_map = {}

    for index, item in enumerate(
        gpa_list_sorted,
        start=1
    ):

        reg = item[0]

        rank_map[reg] = index

    # ========================================================
    # PERCENTAGES
    # ========================================================

    if total > 0:

        pass_pct = round(
            passed / total * 100,
            1
        )

        arrear_pct = round(
            arrear_count / total * 100,
            1
        )

        absent_pct = round(
            absent_count / total * 100,
            1
        )

    else:

        pass_pct = 0
        arrear_pct = 0
        absent_pct = 0

    # ========================================================
    # RETURN
    # ========================================================

    return {
        "total": total,

        "passed": passed,

        "arrear_students": arrear_count,

        "absent_students": absent_count,

        "pass_pct": pass_pct,

        "arrear_pct": arrear_pct,

        "absent_pct": absent_pct,

        "subject_stats": subject_stats,

        "rank_list": gpa_list_sorted,

        "rank_map": rank_map
    }


# ============================================================
# OBSERVATIONS
# ============================================================

def generate_observations(
    analysis: dict,
    subject_names: dict
) -> list:

    observations = []

    stats = analysis.get(
        "subject_stats",
        {}
    )

    # --------------------------------------------------------
    # SUBJECT PERFORMANCE
    # --------------------------------------------------------

    if stats:

        # Highest arrears
        worst_subject = max(
            stats,
            key=lambda code:
            stats[code].get("u", 0)
        )

        # Highest pass percentage
        best_subject = max(
            stats,
            key=lambda code:
            stats[code].get("pass_pct", 0)
        )

        worst_u = stats[
            worst_subject
        ].get("u", 0)

        if worst_u > 0:

            name = subject_names.get(
                worst_subject,
                worst_subject
            )

            observations.append(
                f"{name} ({worst_subject}) "
                f"recorded the highest number of "
                f"U grades ({worst_u} students)."
            )

        best_name = subject_names.get(
            best_subject,
            best_subject
        )

        best_pct = stats[
            best_subject
        ].get(
            "pass_pct",
            0
        )

        observations.append(
            f"{best_name} ({best_subject}) "
            f"achieved the highest pass "
            f"percentage of {best_pct}%."
        )

    # --------------------------------------------------------
    # CLASS PERFORMANCE
    # --------------------------------------------------------

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
            f"Overall class pass percentage: "
            f"{analysis.get('pass_pct', 0)}% "
            f"({passed}/{total} students passed)."
        )

    if arrears:

        observations.append(
            f"{arrears} student(s) have "
            f"at least one arrear subject."
        )

    if absences:

        observations.append(
            f"{absences} student(s) were "
            f"absent in at least one subject."
        )

    # --------------------------------------------------------
    # TOP PERFORMER
    # --------------------------------------------------------

    rank_list = analysis.get(
        "rank_list",
        []
    )

    if rank_list:

        top = rank_list[0]

        observations.append(
            f"Top performer: "
            f"{top[1]} ({top[0]}) "
            f"with GPA {top[2]:.2f}."
        )

    return observations