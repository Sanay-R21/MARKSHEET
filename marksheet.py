
"""Student Marksheet Automation - Python Standard Library"""

import csv
import os
import random
import time

SUBJECTS = ["Maths", "Physics", "Chemistry", "English", "Computer"]
MAX_MARKS = 100
PASS_MARKS = 40


def get_grade(pct):
    if pct >= 90:
        return "A+"
    elif pct >= 80:
        return "A"
    elif pct >= 70:
        return "B"
    elif pct >= 60:
        return "C"
    elif pct >= 50:
        return "D"
    elif pct >= 40:
        return "E"
    return "F"


def process_student(roll, name, marks):
    if len(marks) != len(SUBJECTS):
        raise ValueError("Marks required for all 5 subjects")

    for mark in marks:
        if not 0 <= mark <= MAX_MARKS:
            raise ValueError("Marks must be between 0 and 100")

    total = sum(marks)
    percentage = round(total / (MAX_MARKS * len(SUBJECTS)) * 100, 2)
    passed = all(mark >= PASS_MARKS for mark in marks)

    return {
        "roll": roll,
        "name": name,
        "marks": marks,
        "total": total,
        "pct": percentage,
        "grade": get_grade(percentage) if passed else "F",
        "result": "PASS" if passed else "FAIL",
        "rank": 0,
    }


def assign_ranks(students):
    ordered = sorted(students, key=lambda s: -s["total"])

    for i, student in enumerate(ordered):
        if i > 0 and student["total"] == ordered[i - 1]["total"]:
            student["rank"] = ordered[i - 1]["rank"]
        else:
            student["rank"] = i + 1

    return ordered


def load_csv(path):
    """Load CSV safely and report invalid rows."""
    good = []
    bad = []

    with open(path, "r", newline="", encoding="utf-8-sig") as file:
        reader = csv.reader(file)

        for row_number, row in enumerate(reader, start=1):
            # Ignore blank rows
            if not row or not any(cell.strip() for cell in row):
                continue

            # Ignore the header, even if it has spaces or capital letters
            if row[0].strip().lower() == "roll":
                continue

            try:
                # 1 roll + 1 name + 5 subject marks
                expected_columns = 2 + len(SUBJECTS)

                if len(row) != expected_columns:
                    raise ValueError(
                        f"Expected {expected_columns} columns, "
                        f"but found {len(row)}"
                    )

                roll = row[0].strip()
                name = row[1].strip()

                if not roll or not name:
                    raise ValueError("Roll number or name is missing")

                marks = [float(value.strip()) for value in row[2:]]

                student = process_student(roll, name, marks)
                good.append(student)

            except ValueError as error:
                bad.append((row_number, str(error)))

    return good, bad


def marksheet_text(student, total_students):
    line = "=" * 46

    output = [
        line,
        "         STUDENT MARKSHEET",
        line,
        f"Roll No : {student['roll']}",
        f"Name    : {student['name']}",
        "-" * 46,
        f"{'Subject':<16}{'Marks':>8}{'Out of':>8}",
    ]

    for subject, mark in zip(SUBJECTS, student["marks"]):
        output.append(f"{subject:<16}{mark:>8g}{MAX_MARKS:>8}")

    output.extend([
        "-" * 46,
        f"Total      : {student['total']:g} / {MAX_MARKS * len(SUBJECTS)}",
        f"Percentage : {student['pct']}%",
        f"Grade      : {student['grade']}",
        f"Result     : {student['result']}",
        f"Rank       : {student['rank']} of {total_students}",
        line,
    ])

    return "\n".join(output)


def save_all(students, folder="marksheets"):
    os.makedirs(folder, exist_ok=True)

    for student in students:
        filename = f"{student['roll']}.txt"
        filepath = os.path.join(folder, filename)

        with open(filepath, "w", encoding="utf-8") as file:
            file.write(marksheet_text(student, len(students)))

    results_path = os.path.join(folder, "results.csv")

    with open(results_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow(
            ["Rank", "Roll", "Name"]
            + SUBJECTS
            + ["Total", "Percentage", "Grade", "Result"]
        )

        for student in students:
            writer.writerow(
                [student["rank"], student["roll"], student["name"]]
                + student["marks"]
                + [
                    student["total"],
                    student["pct"],
                    student["grade"],
                    student["result"],
                ]
            )


def class_summary(students):
    count = len(students)

    if count == 0:
        print("No valid students available.")
        return

    passed = sum(student["result"] == "PASS" for student in students)
    average = sum(student["pct"] for student in students) / count

    print(f"\nStudents: {count}")
    print(f"Pass: {passed} ({passed / count * 100:.1f}%)")
    print(f"Fail: {count - passed}")
    print(f"Class average: {average:.2f}%")

    grades = ["A+", "A", "B", "C", "D", "E", "F"]
    print("Grades:", {
        grade: sum(student["grade"] == grade for student in students)
        for grade in grades
    })


def make_demo_csv(path, count):
    """Create sample student data for testing."""
    random.seed(1)

    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["roll", "name"] + SUBJECTS)

        for i in range(1, count + 1):
            marks = [random.randint(25, 100) for _ in SUBJECTS]
            writer.writerow([f"R{i:05d}", f"Student {i}"] + marks)


def main():
    path = "students.csv"

    print(f"Processing {path}...")

    if not os.path.isfile(path):
        print(f"ERROR: {path} not found.")
        print("Place students.csv in the project directory.")
        return

    start_time = time.time()

    try:
        students, bad = load_csv(path)
    except (OSError, csv.Error) as error:
        print(f"ERROR reading CSV: {error}")
        return

    if not students:
        print("ERROR: No valid student rows found.")

        for row_number, reason in bad[:10]:
            print(f"Row {row_number}: {reason}")

        return

    students = assign_ranks(students)

    try:
        save_all(students)
    except OSError as error:
        print(f"ERROR saving marksheets: {error}")
        return

    class_summary(students)

    print(f"\nInvalid rows skipped: {len(bad)}")

    for row_number, reason in bad[:10]:
        print(f"Row {row_number}: {reason}")

    print(f"\nMarksheets saved in 'marksheets/'")
    print(f"Processing time: {time.time() - start_time:.2f} seconds")

    print("\nTop 3 students:")
    for student in students[:3]:
        print(
            f"Rank {student['rank']}: "
            f"{student['name']} - {student['total']} marks"
        )


if __name__ == "__main__":
    main()
