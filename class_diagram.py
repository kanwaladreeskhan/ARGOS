# class_diagram.py
# Mixed mapping: Functional -> methods, Non-Functional/Domain -> attributes
# Usage:
#   (venv) > python class_diagram.py
#   > plantuml class_diagram.puml

import pyodbc
import re
import traceback
from datetime import datetime

# --- EDIT these to match your environment ---
SQL_SERVER = r"DESKTOP-VEIPHS8\SQLEXPRESS"
DATABASE = "AutoRE_DB"
DRIVER = "{ODBC Driver 17 for SQL Server}"
# --------------------------------------------


def get_connection():
    conn_str = (
        f"DRIVER={DRIVER};"
        f"SERVER={SQL_SERVER};"
        f"DATABASE={DATABASE};"
        "Trusted_Connection=yes;"
    )
    return pyodbc.connect(conn_str)


def fetch_latest_requirements():
    """Return list of (Type, Description) tuples for the latest SubmissionID."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT MAX(SubmissionID) FROM dbo.Requirements")
    row = cursor.fetchone()
    last_id = row[0] if row and row[0] is not None else None

    if not last_id:
        cursor.close()
        conn.close()
        return [], None

    cursor.execute(
        "SELECT Type, Description FROM dbo.Requirements WHERE SubmissionID = ?",
        (last_id,)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows, last_id


# --- manual mappings ---
manual_mappings = {
    "within 2 seconds": ("responseTime", "sec"),
    "within 3 seconds": ("responseTime", "sec"),
    "daily backups": ("backupPolicy", "daily"),
    "daily backup": ("backupPolicy", "daily"),
    "99.9% uptime": ("uptime", "99.9%"),
    "95%": ("successRate", "95%"),
    "payment methods should be paypal": ("paymentMethods", "PayPal"),
    "payment methods should be paypal and card": ("paymentMethods", "PayPal+Card"),
    "data privacy": ("privacy", "required"),
    "unauthorized access": ("unauthorizedAccess", "disallowed"),
    "generate reports": ("generateReports", None),
}


def clean_text(txt: str) -> str:
    if not txt:
        return ""
    s = txt.strip().replace("\r", " ").replace("\n", " ")
    s = re.sub(r"\bthe\s+the\b", "the", s, flags=re.I)
    s = re.sub(r"\b(system\s+){2,}", "system ", s, flags=re.I)
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"\b(system\s+(shall|must|should)\s+)+", "the system shall ", s, flags=re.I)
    return s.strip()


def _camel_case(parts):
    if not parts:
        return ""
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def statement_to_method(sentence: str) -> str:
    s = clean_text(sentence).lower()

    for k in manual_mappings:
        if k in s:
            key, val = manual_mappings[k]
            return f"+{key}()"

    s = re.sub(r"^(the\s+)?system\s+(shall|must|should)\s+", "", s, flags=re.I).strip()
    s = re.sub(r"[^\w\s]", " ", s)
    words = s.split()
    if not words:
        return "+doAction()"

    verbs = [
        "enable", "allow", "process", "make", "create", "manage", "generate",
        "view", "track", "notify", "approve", "login", "register", "update",
        "delete", "add", "remove", "search", "filter", "download",
        "upload"
    ]

    verb_idx = None
    for i, w in enumerate(words):
        if w in verbs:
            verb_idx = i
            verb = w
            break
    if verb_idx is None:
        verb = words[0]
        verb_idx = 0

    obj = []
    for w in words[verb_idx+1:verb_idx+4]:
        if w in ("to","with","by","and","using","within","for","the","a","an","of","should","be"):
            continue
        obj.append(w)

    if not obj:
        for w in words[verb_idx+1:]:
            if len(w) > 2:
                obj.append(w)
                break

    parts = [verb] + obj
    parts = ["".join(re.findall(r"[a-z0-9]+", p)) for p in parts if p]
    camel = _camel_case(parts)
    return f"+{camel}()"


def statement_to_attribute(sentence: str) -> str:
    s = clean_text(sentence).lower()

    for k, (name, val) in manual_mappings.items():
        if k in s:
            if val is None:
                return f"+{name} : String"
            return f"+{name} : {val}"

    m = re.search(r"within\s+(\d+(?:\.\d+)?)\s*seconds?", s)
    if m:
        return f"+responseTime : {m.group(1)}s"

    m = re.search(r"(\d+(?:\.\d+)?%)\s*(uptime|availability|success|reliability)?", s)
    if m:
        val = m.group(1)
        key = m.group(2) or "uptime"
        return f"+{key} : {val}"

    if "daily backup" in s or "daily backups" in s:
        return "+backupPolicy : daily"
    if "weekly backup" in s or "weekly backups" in s:
        return "+backupPolicy : weekly"

    nouns = {
        "privacy": "privacy",
        "encryption": "encryption",
        "scalable": "scalability",
        "scalability": "scalability",
        "security": "security",
        "latency": "latency",
        "timeout": "timeout",
        "reports": "reports",
        "notifications": "notifications",
    }

    for token, key in nouns.items():
        if token in s:
            val_match = re.search(r'(\d+(?:\.\d+)?%?)|daily|weekly|monthly|hourly', s)
            if val_match:
                return f"+{key} : {val_match.group(0)}"
            return f"+{key} : String"

    s = re.sub(r"[^\w\s]", " ", s)
    parts = s.split()
    if not parts:
        return "+property : String"

    key_words = parts[-2:] if len(parts) >= 2 else parts[-1:]
    key = "".join(re.findall(r"[a-z0-9]+", " ".join(key_words)))
    key = re.sub(r"^\d+", "", key)
    if not key:
        key = "property"

    return f"+{key} : String"


# ---------------------------------------
# CLASS DIAGRAM GENERATOR
# ---------------------------------------
def generate_class_diagram(requirements):
    uml_lines = ["@startuml", "skinparam classAttributeIconSize 0"]
    uml_lines.append("class Donor { }")
    uml_lines.append("class Admin extends Donor { }")
    uml_lines.append("class CampaignManager extends Donor { }")
    uml_lines.append("class System { }")

    # containers
    donor_attrs, donor_methods = set(), set()
    admin_attrs, admin_methods = set(), set()
    manager_attrs, manager_methods = set(), set()
    system_attrs, system_methods = set(), set()

    # AUTO DEFAULT ATTRIBUTES
    DEFAULT_AUTO_ATTRIBUTES = {
        "Donor": {
            "+donorID : int",
            "+name : String",
            "+email : String",
            "+phone : String",
        },
        "Admin": {
            "+adminID : int",
            "+name : String",
            "+email : String",
            "+role : String",
        },
        "CampaignManager": {
            "+managerID : int",
            "+name : String",
            "+email : String",
            "+assignedCampaigns : int",
        },
        "System": {
            "+systemVersion : String",
            "+lastBackup : String",
            "+uptime : String",
        },
    }

    donor_attrs.update(DEFAULT_AUTO_ATTRIBUTES["Donor"])
    admin_attrs.update(DEFAULT_AUTO_ATTRIBUTES["Admin"])
    manager_attrs.update(DEFAULT_AUTO_ATTRIBUTES["CampaignManager"])
    system_attrs.update(DEFAULT_AUTO_ATTRIBUTES["System"])

    # ---------- AUTO DEFAULT METHODS ----------
    DEFAULT_AUTO_METHODS = {
        "Admin": {
            "+manageUsers()",
            "+viewLogs()",
            "+configureSystem()",
        },
        "CampaignManager": {
            "+createCampaign()",
            "+reviewCampaignReports()",
            "+assignCampaign()",
        },
        "Donor": {
            "+viewProfile()",
            "+donate()",
        },
        "System": {
            "+performBackup()",
            "+generateHealthReport()",
        }
    }

    # Add default methods into method sets so they appear even if DB has none
    admin_methods.update(DEFAULT_AUTO_METHODS.get("Admin", set()))
    manager_methods.update(DEFAULT_AUTO_METHODS.get("CampaignManager", set()))
    donor_methods.update(DEFAULT_AUTO_METHODS.get("Donor", set()))
    system_methods.update(DEFAULT_AUTO_METHODS.get("System", set()))
    # ------------------------------------------

    # PROCESS REQUIREMENTS
    for rtype, desc in requirements:
        if not desc:
            continue

        text = clean_text(desc)
        text_l = text.lower()

        is_functional = (
            isinstance(rtype, str)
            and rtype.lower().startswith("functional")
        )

        action_verbs = (
            "allow","enable","create","process","generate",
            "view","track","notify","approve","login",
            "register","update","delete","add","remove",
            "download","upload","manage"
        )

        if not is_functional:
            if any(v in text_l for v in action_verbs):
                is_functional = True

        if is_functional:
            method = statement_to_method(text)

            if "admin" in text_l:
                admin_methods.add(method)
            elif "manager" in text_l or "campaign" in text_l:
                manager_methods.add(method)
            elif "donor" in text_l or "user" in text_l or "client" in text_l:
                donor_methods.add(method)
            else:
                system_methods.add(method)

        else:
            attr = statement_to_attribute(text)

            if "admin" in text_l:
                admin_attrs.add(attr)
            elif "manager" in text_l or "campaign" in text_l:
                manager_attrs.add(attr)
            elif "donor" in text_l or "user" in text_l or "client" in text_l:
                donor_attrs.add(attr)
            else:
                system_attrs.add(attr)

    # Append items
    def append_items(cls, attrs, methods):
        for a in sorted(attrs):
            uml_lines.append(f"{cls} : {a}")
        for m in sorted(methods):
            uml_lines.append(f"{cls} : {m}")

    append_items("Donor", donor_attrs, donor_methods)
    append_items("Admin", admin_attrs, admin_methods)
    append_items("CampaignManager", manager_attrs, manager_methods)
    append_items("System", system_attrs, system_methods)

    # fallback placeholders (still kept if absolutely empty)
    if not admin_attrs and not admin_methods:
        uml_lines.append("Admin : manageSystemSettings()")
    if not manager_attrs and not manager_methods:
        uml_lines.append("CampaignManager : reviewCampaignReports()")

    uml_lines.append("@enduml")
    return "\n".join(uml_lines)


def save_to_file(content, filename="class_diagram.puml"):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ UML code saved to {filename}")


# MAIN
if __name__ == "__main__":
    print("⏳ UML generator start:", datetime.now().isoformat())

    try:
        rows, sid = fetch_latest_requirements()

        if not rows:
            print("⚠️ No requirements found for latest submission.")
        else:
            print(f"📋 Generating UML for SubmissionID = {sid} (items: {len(rows)})")

            uml_text = generate_class_diagram(rows)
            save_to_file(uml_text)

            print("🎨 Run: plantuml class_diagram.puml")

    except Exception:
        print("❌ Unexpected error:")
        traceback.print_exc()
