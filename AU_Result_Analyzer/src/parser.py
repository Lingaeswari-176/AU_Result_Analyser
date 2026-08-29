import re
import pdfplumber


# ============================================================
# SEMESTER 4 - OFFICIAL CSE SUBJECT CREDITS
# From the supplied CSE syllabus PDF
# ============================================================

SEM4_CREDITS = {
    "CS3452": 3,
    "CS3491": 4,
    "CS3492": 3,
    "CS3401": 4,
    "CS3451": 3,
    "GE3451": 2,
    "CS3461": 1.5,
    "CS3481": 1.5,
    "NM1134": 2,
}


# Order in the actual Anna University Semester-4 result PDF
SEM4_SUBJECT_ORDER = [
    "CS3401",
    "CS3451",
    "CS3452",
    "CS3461",
    "CS3481",
    "CS3491",
    "CS3492",
    "GE3451",
    "NM1134"
]


VALID_GRADES = {
    "O",
    "A+",
    "A",
    "B+",
    "B",
    "C",
    "U",
    "UA",
    "W",
    "I",
    "WH",
    "WH1",
}


# ============================================================
# SEMESTER DETECTION
# ============================================================

def get_semester_from_text(text):
    """
    Detect:
    Semester No. : 04
    Semester No. : 03
    etc.
    """

    match = re.search(
        r"Semester\s*No\.?\s*:\s*(\d+)",
        text,
        re.IGNORECASE
    )

    if match:
        return match.group(1).zfill(2)

    return None


# ============================================================
# FIND SUBJECT COLUMN POSITIONS
# ============================================================

def find_subject_columns(words):
    """
    The PDF contains blank cells.

    Therefore we MUST NOT do:
        line.split()

    because blank cells disappear and grades shift.

    Instead, detect the actual X position of every subject
    column and assign each grade according to its position.
    """

    centres = {}

    for word in words:

        text = word["text"].strip().upper()

        if text in SEM4_CREDITS:

            centre = (
                word["x0"] + word["x1"]
            ) / 2

            centres[text] = centre

    return centres


# ============================================================
# SAME PDF ROW
# ============================================================

def get_same_row(words, top, tolerance=1.8):

    return [
        word
        for word in words
        if abs(word["top"] - top) <= tolerance
    ]


# ============================================================
# PARSE ONE STUDENT
# ============================================================

def parse_student_row(
    words,
    register_word,
    subject_columns
):

    reg_no = register_word["text"].strip()

    row_words = get_same_row(
        words,
        register_word["top"]
    )

    if not subject_columns:
        return None

    first_subject_x = min(
        subject_columns.values()
    )

    # --------------------------------------------------------
    # STUDENT NAME
    # --------------------------------------------------------

    name_words = []

    for word in row_words:

        # Name is between register number and subject columns
        if (
            word["x0"] >= 85
            and word["x1"] < first_subject_x - 2
        ):
            name_words.append(word["text"])

    name = " ".join(name_words).strip()

    # --------------------------------------------------------
    # GRADES
    # --------------------------------------------------------

    grades = {}

    for word in row_words:

        token = word["text"].strip().upper()

        if token not in VALID_GRADES:
            continue

        x = (
            word["x0"] + word["x1"]
        ) / 2

        nearest_subject = min(
            subject_columns,
            key=lambda code:
            abs(subject_columns[code] - x)
        )

        distance = abs(
            subject_columns[nearest_subject] - x
        )

        # Subject columns are roughly 42 px apart.
        # 15 px is a safe matching limit.
        if distance <= 15:

            grades[nearest_subject] = token

    # --------------------------------------------------------
    # ONLY OFFICIAL GPA SUBJECTS
    # --------------------------------------------------------

    final_grades = {}

    for code in SEM4_SUBJECT_ORDER:

        if code in grades:
            final_grades[code] = grades[code]

    return {
        "reg_no": reg_no,
        "name": name,
        "grades": final_grades,
    }


# ============================================================
# SECTION
# ============================================================

def get_section(reg_no):

    suffix = int(reg_no[-3:])

    # 001 - 054
    if 1 <= suffix <= 54:
        return "A"

    # 055 - 109
    if 55 <= suffix <= 109:
        return "B"

    # 110 onwards
    # Includes 301, 303, 304, 701 etc.
    return "C"


# ============================================================
# MAIN PDF PARSER
# ============================================================

def parse_pdf(pdf_file):

    students = {}

    institution = {
        "institution_code": "",
        "institution_name": "",
        "branch": "",
    }

    current_semester = None

    semester_4_started = False

    subject_columns = {}

    with pdfplumber.open(pdf_file) as pdf:

        for page_number, page in enumerate(
            pdf.pages,
            start=1
        ):

            text = page.extract_text() or ""

            # ------------------------------------------------
            # Detect semester heading
            # ------------------------------------------------

            detected_semester = get_semester_from_text(text)

            if detected_semester:

                current_semester = detected_semester

            # ------------------------------------------------
            # Ignore everything before Semester 4
            # ------------------------------------------------

            if current_semester != "04":

                if (
                    semester_4_started
                    and detected_semester
                    and detected_semester != "04"
                ):
                    break

                continue

            semester_4_started = True

            # ------------------------------------------------
            # Extract PDF words WITH coordinates
            # ------------------------------------------------

            words = page.extract_words(
                x_tolerance=1,
                y_tolerance=2,
                keep_blank_chars=False
            )

            # ------------------------------------------------
            # Find subject columns on first Semester-4 page
            # ------------------------------------------------

            detected_columns = find_subject_columns(
                words
            )

            if len(detected_columns) >= 5:

                subject_columns = detected_columns

            # ------------------------------------------------
            # Institution information
            # ------------------------------------------------

            if not institution["institution_name"]:

                match = re.search(
                    r"Inst\.Code/Name\s*:\s*(\d+)\s*-\s*(.+)",
                    text,
                    re.IGNORECASE
                )

                if match:

                    institution["institution_code"] = (
                        match.group(1).strip()
                    )

                    institution["institution_name"] = (
                        match.group(2).strip()
                    )

                match = re.search(
                    r"Branch\s*:\s*(.+)",
                    text,
                    re.IGNORECASE
                )

                if match:

                    institution["branch"] = (
                        match.group(1).strip()
                    )

            if not subject_columns:
                continue

            # ------------------------------------------------
            # ONLY 2024 BATCH
            #
            # 310824xxxxxxxx
            # ------------------------------------------------

            register_words = [

                word
                for word in words

                if re.fullmatch(
                    r"310824104\d{3}",
                    word["text"].strip()
                )

            ]

            # ------------------------------------------------
            # Parse every student on this page
            # ------------------------------------------------

            for register_word in register_words:

                student = parse_student_row(
                    words,
                    register_word,
                    subject_columns
                )

                if not student:
                    continue

                reg_no = student["reg_no"]

                if reg_no not in students:

                    students[reg_no] = student

                else:

                    # If the same student appears again,
                    # preserve existing data and merge grades.
                    if (
                        not students[reg_no]["name"]
                        and student["name"]
                    ):
                        students[reg_no]["name"] = (
                            student["name"]
                        )

                    students[reg_no]["grades"].update(
                        student["grades"]
                    )

    # ========================================================
    # ADD SECTION
    # ========================================================

    for reg_no, student in students.items():

        student["section"] = get_section(reg_no)

    # ========================================================
    # REGISTER NUMBER ORDER
    # ========================================================

    students = dict(
        sorted(
            students.items(),
            key=lambda item: item[0]
        )
    )

    return {

        "institution": institution,

        "students": students,

        "semester": "04",

        "credits": SEM4_CREDITS.copy(),

        "subject_order": SEM4_SUBJECT_ORDER.copy(),

        "total_students": len(students),

    }