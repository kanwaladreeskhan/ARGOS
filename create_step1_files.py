import os

root = "AutoRE_Project"
os.makedirs(root, exist_ok=True)

# README.md
readme = """# Auto Requirements Engineering Project
Domain: Generic (works for any domain)

This project will:
- Collect requirements from users via a form
- Save them in SQL Server
- Apply rule-based extraction
- Generate UML class diagrams automatically

Files:
- sample_reqs.txt : contains example requirements
- form_fields.txt : contains input fields
"""

# sample requirements
sample_reqs = """Functional Requirements:
1. The system shall allow a User to create an account with username and password.
2. The system shall allow a User to log in and log out.
3. An Admin can add, update, and delete records.
4. A User can view and update their profile.
5. A Manager is a type of User.
6. The system shall generate reports based on stored data.
7. A User can request a service from the system.
8. The system shall send notifications to Users.

Non-Functional Requirements:
1. The system must support at least 1000 concurrent users.
2. Response time should not exceed 2 seconds for any query.
3. The system must ensure secure storage of user data.
4. The system should be available 99% of the time.
5. Backup of the database must be taken daily.
"""

# form fields
form_fields = """Form Fields:
1. Requirement Type (Functional / Non-Functional)
2. Description (text)
3. Priority (High / Medium / Low)
4. Stakeholder Role (User / Admin / Manager / Customer)
"""

# Write files
with open(os.path.join(root, "README.md"), "w", encoding="utf-8") as f:
    f.write(readme)

with open(os.path.join(root, "sample_reqs.txt"), "w", encoding="utf-8") as f:
    f.write(sample_reqs)

with open(os.path.join(root, "form_fields.txt"), "w", encoding="utf-8") as f:
    f.write(form_fields)

print("✅ Step 1 files created successfully in 'AutoRE_Project' folder.")

