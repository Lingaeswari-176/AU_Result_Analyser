
import re
import pdfplumber


# ============================================================
# GRADE DEFINITIONS
# ============================================================

GRADE_VALUES = {
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

VALID_GRADES = set(GRADE_VALUES.keys())


# ============================================================
# REGEX
# ============================================================

REGISTER_PATTERN = re.compile(r"\b\d{12}\b")

SUBJECT_PATTERN = re.compile(
    r"\b[A-Z]{2,4}\d{4}[A-Z]?\b",
    re.IGNORECASE
)

SEMESTER_PATTERN = re.compile(
    r"Semester\s+No\.?\s*:\s*(\d+)",
    re.IGNORECASE
)


# ============================================================
# CLEANING
# ============================================================

def clean_cell(value):
    if value is None:
        return ""

    value = str(value)

    value = value.replace("\n", " ")
    value = value.replace("\r", " ")
    value = value.replace("\t", " ")

    value = re.sub(r"\s+", " ", value)

    return value.strip()


def normalize_grade(value):

    value = clean_cell(value)

    if not value:
        return ""

    value = value.upper()
    value = value.replace(" ", "")

    return value


# ============================================================
# SEMESTER DETECTION
# ============================================================

def detect_semester(page_text):

    if not page_text:
        return None

    text = " ".join(page_text.split())

    match = SEMESTER_PATTERN.search(text)

    if match:
        return str(int(match.group(1)))

    return None


# ============================================================
# INSTITUTION
# ============================================================

def extract_institution_info(page_text):

    info = {
        "institution_code": "",
        "institution_name": "",
        "branch": ""
    }

    if not page_text:
        return info

    text = " ".join(page_text.split())

    # Institution
    match = re.search(
        r"Inst\.?\s*Code/Name\s*:\s*(\d+)\s*-\s*(.+?)(?=\s+Semester\s+No\.|\s+DATE\s+OF|\s+Branch\s*:|$)",
        text,
        re.IGNORECASE
    )

    if match:

        info["institution_code"] = match.group(1).strip()
        info["institution_name"] = match.group(2).strip()

    # Branch
    match = re.search(
        r"Branch\s*:\s*(.+?)(?=\s+Semester\s+No\.|\s+DATE\s+OF|$)",
        text,
        re.IGNORECASE
    )

    if match:
        info["branch"] = match.group(1).strip()

    return info


# ============================================================
# FIND SUBJECT COLUMNS
# ============================================================

def find_subject_columns(table):

    best_mapping = {}

    if not table:
        return best_mapping

    for row in table:

        if not row:
            continue

        current_mapping = {}

        for index, cell in enumerate(row):

            cell_text = clean_cell(cell).upper()

            if not cell_text:
                continue

            match = SUBJECT_PATTERN.search(cell_text)

            if match:

                code = match.group(0).upper()

                current_mapping[index] = code

        if len(current_mapping) > len(best_mapping):
            best_mapping = current_mapping

    return best_mapping


# ============================================================
# FIND HEADER ROW
# ============================================================

def find_subject_header_row(table):

    best_index = None
    best_count = 0

    if not table:
        return None

    for row_index, row in enumerate(table):

        if not row:
            continue

        count = 0

        for cell in row:

            text = clean_cell(cell).upper()

            if SUBJECT_PATTERN.search(text):
                count += 1

        if count > best_count:

            best_count = count
            best_index = row_index

    return best_index


# ============================================================
# PARSE STUDENT ROW
# ============================================================

def parse_student_table_row(row, subject_columns):

    if not row:
        return None

    cleaned = [clean_cell(cell) for cell in row]

    # --------------------------------------------------------
    # Find register number
    # --------------------------------------------------------

    reg_no = None
    reg_index = None

    for i, cell in enumerate(cleaned):

        match = REGISTER_PATTERN.search(cell)

        if match:

            reg_no = match.group(0)
            reg_index = i
            break

    # No register number = not a student row
    if not reg_no:
        return None

    # --------------------------------------------------------
    # Student name
    # --------------------------------------------------------

    name = ""

    if reg_index + 1 < len(cleaned):
        name = cleaned[reg_index + 1]

    # --------------------------------------------------------
    # Grades
    # IMPORTANT:
    # Use actual table column positions.
    # Blank cells remain blank.
    # --------------------------------------------------------

    grades = {}
    flag_grades = {}

    for column_index, subject_code in subject_columns.items():

        if column_index >= len(cleaned):
            continue

        grade = normalize_grade(cleaned[column_index])

        if not grade:
            continue

        if grade in VALID_GRADES:

            grades[subject_code] = grade

        else:

            flag_grades[subject_code] = grade

    return {
        "reg_no": reg_no,
        "name": name,
        "grades": grades,
        "flag_grades": flag_grades
    }


# ============================================================
# EXTRACT TABLES
# ============================================================

def extract_tables_from_page(page):

    tables = []

    # Try normal extraction
    try:

        result = page.extract_tables()

        if result:
            tables.extend(result)

    except Exception:
        pass

    # Try line-based extraction if necessary
    if not tables:

        try:

            result = page.extract_tables(
                table_settings={
                    "vertical_strategy": "lines",
                    "horizontal_strategy": "lines",
                    "intersection_tolerance": 5,
                    "snap_tolerance": 3,
                    "join_tolerance": 3
                }
            )

            if result:
                tables.extend(result)

        except Exception:
            pass

    return tables


# ============================================================
# MAIN PARSER
# ============================================================

def parse_pdf(pdf_file):

    student_results = {}

    semester_subjects = {}

    institution_info = {}

    # ========================================================
    # THIS IS THE IMPORTANT PART
    #
    # active_subject_columns stays alive across pages.
    #
    # Example:
    #
    # Page 20:
    # Semester 3
    # CS3301 | CS3351 | CS3352 | CS3391 | MA3354
    #
    # Page 21:
    # student rows only
    #
    # Page 22:
    # student rows only
    #
    # Page 23:
    # student rows only
    #
    # All of them continue using Semester 3 columns.
    # ========================================================

    current_semester = None

    active_subject_columns = {}

    with pdfplumber.open(pdf_file) as pdf:

        total_pages = len(pdf.pages)

        for page_number, page in enumerate(
            pdf.pages,
            start=1
        ):

            print(
                f"\nProcessing page {page_number}/{total_pages}"
            )

            # ====================================================
            # PAGE TEXT
            # ====================================================

            page_text = page.extract_text() or ""

            # ====================================================
            # CHECK WHETHER A NEW SEMESTER STARTS ON THIS PAGE
            # ====================================================

            detected_semester = detect_semester(page_text)

            if detected_semester is not None:

                # ------------------------------------------------
                # NEW SEMESTER
                # ------------------------------------------------

                if detected_semester != current_semester:

                    current_semester = detected_semester

                    # VERY IMPORTANT:
                    # Reset only when NEW semester starts.
                    active_subject_columns = {}

                    if current_semester not in semester_subjects:

                        semester_subjects[
                            current_semester
                        ] = []

                    print(
                        f"➡️ NEW SEMESTER DETECTED: "
                        f"{current_semester}"
                    )

            # ====================================================
            # INSTITUTION INFO
            # ====================================================

            if not institution_info:

                institution_info = extract_institution_info(
                    page_text
                )

            # ====================================================
            # No semester yet
            # ====================================================

            if current_semester is None:

                continue

            # ====================================================
            # EXTRACT TABLES
            # ====================================================

            tables = extract_tables_from_page(page)

            if not tables:

                print(
                    f"   No tables found on page {page_number}"
                )

                continue

            page_students = 0

            # ====================================================
            # PROCESS EVERY TABLE
            # ====================================================

            for table in tables:

                if not table:
                    continue

                # =================================================
                # TRY TO FIND SUBJECT HEADER
                # =================================================

                new_subject_columns = find_subject_columns(
                    table
                )

                # -------------------------------------------------
                # If subject header exists
                # SAVE IT
                # -------------------------------------------------

                if new_subject_columns:

                    active_subject_columns = (
                        new_subject_columns
                    )

                    semester_subjects[
                        current_semester
                    ] = list(
                        active_subject_columns.values()
                    )

                    print(
                        f"   Subjects for Sem "
                        f"{current_semester}: "
                        f"{', '.join(active_subject_columns.values())}"
                    )

                # -------------------------------------------------
                # If NO subject header:
                #
                # DO NOT SKIP!
                #
                # Use previous subject columns.
                # -------------------------------------------------

                elif active_subject_columns:

                    print(
                        f"   Continuing Sem "
                        f"{current_semester} table "
                        f"on page {page_number}"
                    )

                else:

                    # We genuinely don't know which columns
                    # correspond to which subjects.
                    continue

                # =================================================
                # DETERMINE WHERE STUDENT ROWS BEGIN
                # =================================================

                header_index = find_subject_header_row(
                    table
                )

                if header_index is not None:

                    rows_to_process = table[
                        header_index + 1:
                    ]

                else:

                    # Continuation page.
                    # Entire table contains student rows.
                    rows_to_process = table

                # =================================================
                # PARSE EVERY STUDENT
                # =================================================

                for row in rows_to_process:

                    student = parse_student_table_row(
                        row,
                        active_subject_columns
                    )

                    if not student:
                        continue

                    reg_no = student["reg_no"]

                    # ------------------------------------------------
                    # Create student
                    # ------------------------------------------------

                    if reg_no not in student_results:

                        student_results[reg_no] = {
                            "name": student["name"],
                            "reg_no": reg_no,
                            "semesters": {}
                        }

                    # ------------------------------------------------
                    # Update name
                    # ------------------------------------------------

                    if (
                        student["name"]
                        and
                        not student_results[
                            reg_no
                        ]["name"]
                    ):

                        student_results[
                            reg_no
                        ]["name"] = student["name"]

                    # ------------------------------------------------
                    # Save semester
                    # ------------------------------------------------

                    student_results[
                        reg_no
                    ]["semesters"][
                        current_semester
                    ] = {

                        "subject_codes": list(
                            active_subject_columns.values()
                        ),

                        "grades": student["grades"],

                        "flag_grades": student[
                            "flag_grades"
                        ]
                    }

                    page_students += 1

            # ====================================================
            # PAGE DEBUG
            # ====================================================

            print(
                f"   Students found on this page: "
                f"{page_students}"
            )

    # ============================================================
    # SORT SEMESTERS
    # ============================================================

    semesters = sorted(
        semester_subjects.keys(),
        key=lambda x: int(x)
    )

    # ============================================================
    # DEBUG SUMMARY
    # ============================================================

    print("\n")
    print("=" * 60)
    print("AU RESULT PARSER SUMMARY")
    print("=" * 60)

    print(
        f"TOTAL UNIQUE STUDENTS: "
        f"{len(student_results)}"
    )

    print("\nSUBJECTS PER SEMESTER:")

    for sem in semesters:

        subjects = semester_subjects.get(
            sem,
            []
        )

        print(
            f"Semester {sem}: "
            f"{len(subjects)} subjects"
        )

        print(
            "   "
            + ", ".join(subjects)
        )

    print("=" * 60)

    # ============================================================
    # RETURN
    # ============================================================

    return {

        "institution": institution_info,

        "students": student_results,

        "semesters": semesters,

        "semester_subjects": semester_subjects
    }
