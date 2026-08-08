import sqlite3
import re
import json

from google import genai


# =========================================================
# GEMINI AI SETUP
# =========================================================

# The API key is taken automatically from the
# GEMINI_API_KEY environment variable.

client = genai.Client()


# =========================================================
# DATABASE CONNECTION
# =========================================================

conn = sqlite3.connect("hostel.db")

cursor = conn.cursor()


# =========================================================
# CREATE DATABASE TABLE
# =========================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS complaints (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    student TEXT,

    block TEXT,

    room TEXT,

    problem TEXT,

    category TEXT,

    priority TEXT,

    team TEXT,

    safety TEXT,

    severity TEXT,

    status TEXT
)
""")

conn.commit()


# =========================================================
# CHECK BLOCK
# =========================================================

def valid_block(block):

    return block.upper() in ["A", "B", "C", "D"]


# =========================================================
# CHECK ROOM NUMBER
# Example:
# 3B-74
# 2A-21
# 4C-105
# =========================================================

def valid_room(room):

    pattern = r"^[1-9][A-Da-d]-[0-9]{2,3}$"

    return re.match(pattern, room) is not None


# =========================================================
# GEMINI AI - UNDERSTAND COMPLAINT
# =========================================================

def understand_complaint(problem):

    prompt = f"""
You are a hostel maintenance complaint classifier.

Read the student's complaint and identify:

1. category
2. safety
3. severity

Allowed categories:

electrical
water
internet
ac
furniture
security
cleaning
other

Safety must be:

yes
or
no

Severity must be:

critical
high
medium
low

Return ONLY valid JSON.

Do not add explanations.

Example:

{{
    "category": "electrical",
    "safety": "yes",
    "severity": "critical"
}}

Student complaint:

{problem}
"""

    try:

        response = client.models.generate_content(

            model="gemini-3.5-flash-lite",

            contents=prompt
        )

        result = response.text.strip()


        # Remove markdown if Gemini adds it

        result = result.replace(
            "```json",
            ""
        )

        result = result.replace(
            "```",
            ""
        )

        result = result.strip()


        # Convert JSON text into Python dictionary

        data = json.loads(result)


        # Get values safely

        category = data.get(
            "category",
            "other"
        ).lower()

        safety = data.get(
            "safety",
            "no"
        ).lower()

        severity = data.get(
            "severity",
            "low"
        ).lower()


        # Make sure category is valid

        valid_categories = [

            "electrical",
            "water",
            "internet",
            "ac",
            "furniture",
            "security",
            "cleaning",
            "other"
        ]


        if category not in valid_categories:

            category = "other"


        # Make sure safety is valid

        if safety not in ["yes", "no"]:

            safety = "no"


        # Make sure severity is valid

        valid_severity = [

            "critical",
            "high",
            "medium",
            "low"
        ]


        if severity not in valid_severity:

            severity = "low"


        return {

            "category": category,

            "safety": safety,

            "severity": severity
        }


    except Exception as e:

        print("\nGemini Error:")
        print(e)

        print(
            "\nUsing default values."
        )


        return {

            "category": "other",

            "safety": "no",

            "severity": "low"
        }


# =========================================================
# CALCULATE FINAL PRIORITY
# =========================================================

def get_priority(
        category,
        problem,
        safety,
        severity
):

    category = category.lower()

    problem = problem.lower()

    safety = safety.lower()

    severity = severity.lower()


    # -----------------------------------------------------
    # CRITICAL
    # -----------------------------------------------------

    if safety == "yes":

        return "CRITICAL"


    if severity == "critical":

        return "CRITICAL"


    if "spark" in problem:

        return "CRITICAL"


    if "fire" in problem:

        return "CRITICAL"


    if "flood" in problem:

        return "CRITICAL"


    # -----------------------------------------------------
    # HIGH
    # -----------------------------------------------------

    if severity == "high":

        return "HIGH"


    if category == "water":

        return "HIGH"


    if category == "security":

        return "HIGH"


    if "lock" in problem:

        return "HIGH"


    # -----------------------------------------------------
    # MEDIUM
    # -----------------------------------------------------

    if severity == "medium":

        return "MEDIUM"


    if category == "electrical":

        return "MEDIUM"


    if category == "ac":

        return "MEDIUM"


    if category == "internet":

        return "MEDIUM"


    # -----------------------------------------------------
    # LOW
    # -----------------------------------------------------

    return "LOW"


# =========================================================
# ASSIGN MAINTENANCE TEAM
# =========================================================

def get_team(category):

    category = category.lower()


    if category == "electrical":

        return "Electrical Team"


    elif category == "water":

        return "Plumbing Team"


    elif category == "internet":

        return "Network Team"


    elif category == "ac":

        return "AC Team"


    elif category == "furniture":

        return "Furniture Team"


    elif category == "security":

        return "Security Team"


    elif category == "cleaning":

        return "Cleaning Team"


    else:

        return "General Maintenance Team"


# =========================================================
# SUBMIT COMPLAINT
# =========================================================

def add_complaint():

    print("\n")
    print("========================================")
    print("          SUBMIT COMPLAINT")
    print("========================================")


    # -----------------------------------------------------
    # STUDENT NAME
    # -----------------------------------------------------

    name = input(
        "Student name: "
    )


    # -----------------------------------------------------
    # BLOCK
    # -----------------------------------------------------

    while True:

        block = input(
            "Block (A/B/C/D): "
        ).upper()


        if valid_block(block):

            break


        print(
            "\nInvalid block!"
        )

        print(
            "Please enter A, B, C or D."
        )


    # -----------------------------------------------------
    # ROOM
    # -----------------------------------------------------

    while True:

        room = input(
            "Room number (example: 3B-74): "
        ).upper()


        if valid_room(room):

            break


        print(
            "\nInvalid room format!"
        )

        print(
            "Use format like 3B-74."
        )


    # -----------------------------------------------------
    # COMPLAINT
    # -----------------------------------------------------

    problem = input(
        "\nDescribe your problem:\n"
    )


    # -----------------------------------------------------
    # AI ANALYSIS
    # -----------------------------------------------------

    print(
        "\nGemini is analyzing your complaint..."
    )


    ai_data = understand_complaint(
        problem
    )


    category = ai_data[
        "category"
    ]


    safety = ai_data[
        "safety"
    ]


    severity = ai_data[
        "severity"
    ]


    # -----------------------------------------------------
    # DISPLAY AI RESULT
    # -----------------------------------------------------

    print("\n")
    print("========================================")
    print("            AI ANALYSIS")
    print("========================================")

    print(
        "Category :",
        category
    )

    print(
        "Safety   :",
        safety
    )

    print(
        "Severity :",
        severity
    )


    # -----------------------------------------------------
    # CALCULATE PRIORITY
    # -----------------------------------------------------

    priority = get_priority(

        category,

        problem,

        safety,

        severity
    )


    # -----------------------------------------------------
    # ASSIGN TEAM
    # -----------------------------------------------------

    team = get_team(
        category
    )


    # -----------------------------------------------------
    # SAVE COMPLAINT
    # -----------------------------------------------------

    cursor.execute("""
    INSERT INTO complaints
    (
        student,
        block,
        room,
        problem,
        category,
        priority,
        team,
        safety,
        severity,
        status
    )

    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

    """, (

        name,

        block,

        room,

        problem,

        category,

        priority,

        team,

        safety,

        severity,

        "Pending"
    ))


    conn.commit()


    # -----------------------------------------------------
    # DISPLAY FINAL RESULT
    # -----------------------------------------------------

    print("\n")
    print("========================================")
    print("       COMPLAINT SUBMITTED")
    print("========================================")

    print(
        "Complaint ID :",
        cursor.lastrowid
    )

    print(
        "Student      :",
        name
    )

    print(
        "Block        :",
        block
    )

    print(
        "Room         :",
        room
    )

    print(
        "Category     :",
        category
    )

    print(
        "Safety Risk  :",
        safety
    )

    print(
        "Severity     :",
        severity
    )

    print(
        "Priority     :",
        priority
    )

    print(
        "Team         :",
        team
    )

    print(
        "Status       : Pending"
    )


# =========================================================
# VIEW ALL COMPLAINTS
# =========================================================

def show_complaints():

    print("\n")
    print("========================================")
    print("          ALL COMPLAINTS")
    print("========================================")


    # Critical complaints first

    cursor.execute("""
    SELECT *

    FROM complaints

    ORDER BY

    CASE priority

        WHEN 'CRITICAL' THEN 1

        WHEN 'HIGH' THEN 2

        WHEN 'MEDIUM' THEN 3

        WHEN 'LOW' THEN 4

    END
    """)


    rows = cursor.fetchall()


    # No complaints

    if len(rows) == 0:

        print(
            "\nNo complaints found."
        )

        return


    # Display complaints

    for row in rows:

        print("\n")
        print("----------------------------------------")

        print(
            "Complaint ID :",
            row[0]
        )

        print(
            "Student      :",
            row[1]
        )

        print(
            "Block        :",
            row[2]
        )

        print(
            "Room         :",
            row[3]
        )

        print(
            "Problem      :",
            row[4]
        )

        print(
            "Category     :",
            row[5]
        )

        print(
            "Priority     :",
            row[6]
        )

        print(
            "Team         :",
            row[7]
        )

        print(
            "Safety       :",
            row[8]
        )

        print(
            "Severity     :",
            row[9]
        )

        print(
            "Status       :",
            row[10]
        )


# =========================================================
# UPDATE COMPLAINT STATUS
# =========================================================

def update_status():

    print("\n")
    print("========================================")
    print("         UPDATE COMPLAINT")
    print("========================================")


    # -----------------------------------------------------
    # GET COMPLAINT ID
    # -----------------------------------------------------

    try:

        complaint_id = int(
            input(
                "Enter complaint ID: "
            )
        )


    except ValueError:

        print(
            "\nPlease enter a valid number."
        )

        return


    # -----------------------------------------------------
    # FIND COMPLAINT
    # -----------------------------------------------------

    cursor.execute("""

    SELECT *

    FROM complaints

    WHERE id = ?

    """, (

        complaint_id,

    ))


    complaint = cursor.fetchone()


    if complaint is None:

        print(
            "\nComplaint not found."
        )

        return


    # -----------------------------------------------------
    # CURRENT STATUS
    # -----------------------------------------------------

    print(
        "\nCurrent status:",
        complaint[10]
    )


    print("\n1. Pending")

    print("2. In Progress")

    print("3. Completed")


    choice = input(
        "\nChoose new status: "
    )


    # -----------------------------------------------------
    # SELECT STATUS
    # -----------------------------------------------------

    if choice == "1":

        status = "Pending"


    elif choice == "2":

        status = "In Progress"


    elif choice == "3":

        status = "Completed"


    else:

        print(
            "\nInvalid choice."
        )

        return


    # -----------------------------------------------------
    # UPDATE DATABASE
    # -----------------------------------------------------

    cursor.execute("""

    UPDATE complaints

    SET status = ?

    WHERE id = ?

    """, (

        status,

        complaint_id
    ))


    conn.commit()


    print(
        "\nStatus updated successfully!"
    )

    print(
        "New status:",
        status
    )


# =========================================================
# MAIN MENU
# =========================================================
if __name__ == "__main__":
 while True:

    print("\n")
    print("============================================")
    print("        HOSTEL MAINTENANCE SYSTEM")
    print("============================================")

    print("\n1. Submit Complaint")

    print("2. View Complaints")

    print("3. Update Complaint Status")

    print("4. Exit")


    choice = input(
        "\nEnter your choice: "
    )


    # -----------------------------------------------------
    # SUBMIT
    # -----------------------------------------------------

    if choice == "1":

        add_complaint()


    # -----------------------------------------------------
    # VIEW
    # -----------------------------------------------------

    elif choice == "2":

        show_complaints()


    # -----------------------------------------------------
    # UPDATE
    # -----------------------------------------------------

    elif choice == "3":

        update_status()


    # -----------------------------------------------------
    # EXIT
    # -----------------------------------------------------

    elif choice == "4":

        print("\n")
        print(
            "Thank you for using"
        )

        print(
            "Hostel Maintenance System!"
        )

        break


    # -----------------------------------------------------
    # INVALID
    # -----------------------------------------------------

    else:

        print(
            "\nInvalid choice!"
        )

        print(
            "Please select 1, 2, 3 or 4."
        )


# =========================================================
# CLOSE DATABASE
# =========================================================

conn.close()