"""Student Marksheet Automation (High Volume) - Python, standard library only."""
import csv, os, random, time

SUBJECTS = ["Maths", "Physics", "Chemistry", "English", "Computer"]
MAX_MARKS = 100          # per subject
PASS_MARKS = 40          # minimum in every subject

def get_grade(pct):
    """Return grade letter for a percentage."""
    for limit, grade in [(90, "A+"), (80, "A"), (70, "B"), (60, "C"), (50, "D"), (40, "E")]:
        if pct >= limit:
            return grade
    return "F"

def process_student(roll, name, marks):
    """Validate marks and calculate total, percentage, grade and result."""
    if len(marks) != len(SUBJECTS):
        raise ValueError("Need marks for all subjects")
    for m in marks:
        if not 0 <= m <= MAX_MARKS:
            raise ValueError(f"Marks must be between 0 and {MAX_MARKS}")
    total = sum(marks)
    pct = round(total / (MAX_MARKS * len(SUBJECTS)) * 100, 2)
    passed = all(m >= PASS_MARKS for m in marks)
    return {"roll": roll, "name": name, "marks": marks, "total": total, "pct": pct,
            "grade": get_grade(pct) if passed else "F",
            "result": "PASS" if passed else "FAIL", "rank": 0}

def assign_ranks(students):
    """Rank by total (highest first). Equal totals share a rank (1,2,2,4)."""
    ordered = sorted(students, key=lambda s: -s["total"])
    for i, s in enumerate(ordered):
        s["rank"] = ordered[i - 1]["rank"] if i and s["total"] == ordered[i - 1]["total"] else i + 1
    return ordered

def load_csv(path):
    """Read roll,name,<subject marks...>. Bad rows are skipped and reported."""
    good, bad = [], []
    with open(path, newline="") as f:
        for n, row in enumerate(csv.reader(f), start=2):
            if n == 2 and row[0].lower() == "roll":
                continue
            try:
                good.append(process_student(row[0], row[1], [float(x) for x in row[2:]]))
            except (ValueError, IndexError) as e:
                bad.append((n, str(e)))
    return good, bad

def marksheet_text(s, total_students):
    line = "=" * 46
    out = [line, "         STUDENT MARKSHEET", line,
           f"Roll No : {s['roll']}", f"Name    : {s['name']}", "-" * 46,
           f"{'Subject':<16}{'Marks':>8}{'Out of':>8}"]
    out += [f"{sub:<16}{m:>8g}{MAX_MARKS:>8}" for sub, m in zip(SUBJECTS, s["marks"])]
    out += ["-" * 46, f"Total      : {s['total']:g} / {MAX_MARKS * len(SUBJECTS)}",
            f"Percentage : {s['pct']}%", f"Grade      : {s['grade']}",
            f"Result     : {s['result']}", f"Rank       : {s['rank']} of {total_students}", line]
    return "\n".join(out)

def save_all(students, folder="marksheets"):
    """Write one printable marksheet per student plus a combined results.csv."""
    os.makedirs(folder, exist_ok=True)
    for s in students:
        with open(os.path.join(folder, f"{s['roll']}.txt"), "w") as f:
            f.write(marksheet_text(s, len(students)))
    with open(os.path.join(folder, "results.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Rank", "Roll", "Name"] + SUBJECTS + ["Total", "Percentage", "Grade", "Result"])
        for s in students:
            w.writerow([s["rank"], s["roll"], s["name"]] + s["marks"] +
                       [s["total"], s["pct"], s["grade"], s["result"]])

def class_summary(students):
    n = len(students)
    passed = sum(s["result"] == "PASS" for s in students)
    print(f"Students: {n} | Pass: {passed} ({passed / n * 100:.1f}%) | "
          f"Class average: {sum(s['pct'] for s in students) / n:.2f}%")
    print("Grades:", {g: sum(s["grade"] == g for s in students) for g in ["A+", "A", "B", "C", "D", "E", "F"]})

def make_demo_csv(path, n):
    """Create a sample file with n students (to test high volume)."""
    random.seed(1)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["roll", "name"] + SUBJECTS)
        for i in range(1, n + 1):
            w.writerow([f"R{i:05d}", f"Student {i}"] + [random.randint(25, 100) for _ in SUBJECTS])

def main():
    while True:
        print("\n1. Generate demo data  2. Process CSV file  3. Exit")
        c = input("Choose: ").strip()
        if c == "1":
            n = input("How many students? ").strip()
            make_demo_csv("students.csv", int(n) if n.isdigit() else 1000)
            print("students.csv created.")
        elif c == "2":
            path = input("CSV file name [students.csv]: ").strip() or "students.csv"
            if not os.path.exists(path):
                print("File not found."); continue
            t = time.time()
            students, bad = load_csv(path)
            if not students:
                print("No valid rows."); continue
            students = assign_ranks(students)
            save_all(students)
            class_summary(students)
            print(f"Skipped {len(bad)} bad rows. Marksheets saved in 'marksheets/' in {time.time() - t:.2f}s")
            print("\nTop 3:", [(s["rank"], s["name"], s["total"]) for s in students[:3]])
        elif c == "3":
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()
