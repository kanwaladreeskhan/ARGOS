import db

def fetch_requirements():
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Id, Type, Description, Priority, Stakeholder FROM dbo.Requirements")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def categorize_requirement(desc):
    desc = desc.lower()
    if "functional" in desc:
        return "Functional"
    elif "nonfunc" in desc or "time" in desc or "privacy" in desc or "security" in desc:
        return "Non-Functional"
    elif "domain" in desc:
        return "Domain-Specific"
    elif "inverse" in desc or "not" in desc or "never" in desc:
        return "Inverse"
    else:
        return "Uncategorized"

if __name__ == "__main__":
    data = fetch_requirements()
    for row in data:
        rid, rtype, desc, priority, stakeholder = row
        category = categorize_requirement(desc)
        print(f"[{category}] {desc} (Priority: {priority}, Stakeholder: {stakeholder})")
