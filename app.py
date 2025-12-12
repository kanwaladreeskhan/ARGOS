from flask import Flask, render_template, request, redirect, url_for, session, flash
import db

app = Flask(__name__)
app.secret_key = "any_strong_secret_key_here_123"

# ==================== LOGIN / SIGNUP ====================

@app.route("/", methods=["GET", "POST"])
def index():
    if "user" in session:
        return redirect("/form")
    
    # Agar POST request hai (matlab form submit kiya) toh login logic chalao
    if request.method == "POST":
        return login()  # wohi login function jo neeche hai
    
    # Agar GET request hai toh sirf signin page dikhao
    return render_template("signin.html")         # tumhara original signin.html

@app.route("/signup")
def signup():
    return render_template("signup.html")          # tumhara original signup.html
@app.route("/logout_first_then_signin")
def logout_first_then_signin():
    session.pop("user", None)   # pehle logout kar do
    return redirect("/")        # phir signin page pe bhejo

@app.route("/register", methods=["POST"])
def register():
    email = request.form["email"].strip().lower()
    password = request.form["password"]

    if not email or not password:
        flash("Email and password required!", "error")
        return redirect("/signup")

    conn = db.get_connection()
    cursor = conn.cursor()

    # Check if already exists
    cursor.execute("SELECT Email FROM Users WHERE Email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        flash("Email already registered!", "error")
        return redirect("/signup")

    # Create new user
    cursor.execute("INSERT INTO Users (Email, Password) VALUES (?, ?)", (email, password))
    conn.commit()
    conn.close()

    flash("Account created successfully! Now login.", "success")
    return redirect("/")

@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"].strip().lower()
    password = request.form["password"]

    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Email FROM Users WHERE Email = ? AND Password = ?", (email, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        session["user"] = email
        return redirect("/form")
    else:
        flash("Invalid email or password!", "error")
        return redirect("/")

@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Logged out successfully", "success")
    return redirect("/")

# ==================== PROTECTED PAGES ====================

@app.route("/form", methods=["GET"])
def form():
    if "user" not in session:
        flash("Please login first!", "error")
        return redirect("/")
    return render_template("form.html")   # tumhara original form

@app.route("/submit", methods=["POST"])
def submit():
    if "user" not in session:
        return redirect("/")

    # ←←← Tumhara pura original submit code yahan exactly same rahega →→→
    responses = request.form.to_dict()
    conn = db.get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT ISNULL(MAX(SubmissionID), 0) + 1 FROM dbo.Requirements")
    new_id = cursor.fetchone()[0]

    functional_mapping = {
        "functional_2": {"yes": "allow admin to approve donation campaigns", "no": "not allow admin to approve donation campaigns"},
        "functional_4": {"email": "allow users to register using email", "social": "allow users to register using social media accounts"},
        "functional_7": {"yes": "support recurring donations", "no": "not support recurring donations"}
    }

    for key, value in responses.items():
        value = value.strip()
        if not value:
            continue

        if key in functional_mapping and value in functional_mapping[key]:
            sentence = f"The system shall {functional_mapping[key][value]}"
            req_type = "Functional"
        elif key.startswith("functional"):
            req_type = "Functional"
            sentence = f"The system shall {value}"
        elif key.startswith("nonfunc"):
            req_type = "Non-Functional"
            sentence = f"The system must {value}"
        elif key.startswith("domain"):
            req_type = "Domain"
            sentence = f"The system shall support {value}"
        elif key.startswith("inverse"):
            req_type = "Inverse"
            sentence = f"The system shall not {value}"
        else:
            req_type = "General"
            sentence = value

        cursor.execute("""
            INSERT INTO dbo.Requirements (Type, Description, Priority, Stakeholder, SubmissionID)
            VALUES (?, ?, ?, ?, ?)
        """, (req_type, sentence, "Medium", "Client", new_id))

    conn.commit()
    conn.close()
    return redirect(url_for("show_requirements", sid=new_id))

@app.route("/templaterequirements")
def show_requirements():
    if "user" not in session:
        return redirect("/")
    sid = request.args.get("sid", type=int)
    conn = db.get_connection()
    cursor = conn.cursor()
    query = "SELECT Type, Description FROM dbo.Requirements"
    params = ()
    if sid:
        query += " WHERE SubmissionID = ?"
        params = (sid,)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    categorized = {"Functional": [], "Non-Functional": [], "Domain": [], "Inverse": []}
    for rtype, desc in rows:
        if rtype in categorized:
            categorized[rtype].append(desc)

    return render_template("templaterequirements.html", categorized=categorized)

if __name__ == "__main__":
    app.run(debug=True)