import db

def fetch_functional_requirements():
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Description FROM dbo.Requirements WHERE Type='Functional'")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [r[0] for r in rows]

def generate_uml(requirements):
    uml = "@startuml\n"
    uml += "class User {\n}\n"
    uml += "class Admin {\n}\n"
    uml += "class Manager {\n}\n"

    for req in requirements:
        r = req.lower()
        if "login" in r:
            uml += "User : +login()\n"
        if "profile" in r:
            uml += "User : +updateProfile()\n"
        if "report" in r:
            uml += "Manager : +generateReport()\n"
        if "delete" in r or "manage" in r:
            uml += "Admin : +manageRecords()\n"

    uml += "Manager --|> User\n"
    uml += "Admin --|> User\n"
    uml += "@enduml\n"
    return uml

if __name__ == "__main__":
    reqs = fetch_functional_requirements()
    uml_code = generate_uml(reqs)
    with open("class_diagram.puml", "w", encoding="utf-8") as f:
        f.write(uml_code)
    print("✅ UML description generated in class_diagram.puml")
