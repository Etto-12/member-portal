# UPKO Member Portal – Project Context for Claude

## 1. Project Overview

This project is the UPKO Member Portal.

It is a Flask web application used to manage:

- UPKO members
- Member records
- Membership applications
- Admin users
- Bahagian/Cawangan application accounts
- Member reports
- Organisation hierarchy
- ID assignment for new member IDs

Production domain:

https://upko.duckdns.org

Production server project path:

/home/upko/member_portal

Systemd service name:

upko_member_portal

Production WSGI server:

Gunicorn

Gunicorn bind:

127.0.0.1:5001

Reverse proxy:

nginx

Important production commands:

```bash
cd ~/member_portal
sudo systemctl restart upko_member_portal
sudo systemctl status upko_member_portal --no-pager -l
sudo journalctl -u upko_member_portal -n 120 --no-pager

Expected local check:

curl -I http://127.0.0.1:5001

Expected domain check:

curl -I https://upko.duckdns.org

A 302 FOUND redirect to /login is normal.

2. Tech Stack

Backend:

Python
Flask
Flask-Login
SQLAlchemy
Flask-Migrate / Alembic
PostgreSQL
Gunicorn
nginx

Frontend:

Jinja2 templates
HTML
CSS
Vanilla JavaScript

Databases:

Main database: memberdb
Membership applications database: membership_app_db
ID assignment database: id_assignment_db

SQLAlchemy binds:

SQLALCHEMY_BINDS = {
    "applications": os.environ.get("APPLICATIONS_DATABASE_URL"),
    "id_assignment": os.environ.get("ID_ASSIGNMENT_DATABASE_URL"),
}
3. Security Rules

Never commit real secrets.

Never commit:

/etc/member_portal.env
.env
real PostgreSQL passwords
Flask SECRET_KEY
database dumps
.sql
.dump
.backup
real member CSV files
Members.csv
members_clean.csv
logs
uploads
files containing real IC/member data outside the database

The real production environment variables are stored only on the server:

/etc/member_portal.env

The GitHub repo should only contain:

.env.example

with placeholder values.

Safe config pattern in app/config.py:

import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")

    SQLALCHEMY_BINDS = {
        "applications": os.environ.get("APPLICATIONS_DATABASE_URL"),
        "id_assignment": os.environ.get("ID_ASSIGNMENT_DATABASE_URL"),
    }

    SQLALCHEMY_TRACK_MODIFICATIONS = False

Do not put database URLs directly into config.py.

4. GitHub Repository

Repository:

Etto-12/member-portal

Main branch:

main

The repository must remain private.

Current workflow:

Edit locally in VS Code.
Review diff.
Commit.
Push to GitHub.
Pull changes on server.
Restart Gunicorn service.
5. Important Project Files

Main app factory:

app/__init__.py

Config:

app/config.py

Extensions:

app/extensions.py

Run file:

run.py

Models:

app/models/user.py
app/models/member.py
app/models/location.py
app/models/membership_application.py
app/models/hierarchy.py
app/models/id_assignment.py

Routes:

app/routes/auth.py
app/routes/admin.py
app/routes/applications.py
app/routes/hierarchy.py
app/routes/id_assignment.py
app/routes/master.py
app/routes/public.py

Main layout:

app/templates/layout/base.html

Admin templates:

app/templates/admin/

Applications templates:

app/templates/applications/

Hierarchy templates:

app/templates/hierarchy/

Public templates:

app/templates/public/

Migrations:

migrations/
6. App Factory / Blueprint Registration

The app is created in:

app/__init__.py

Blueprints currently registered:

auth_bp
public_bp
admin_bp
master_bp
hierarchy_bp
applications_bp
id_assignment_bp

If adding a new route file, import and register the new blueprint in app/__init__.py.

7. User / Role System

The user model is in:

app/models/user.py

The app uses Flask-Login.

Important access logic:

current_user.is_admin is used for admin access.
current_user.role is used for role checks.
Bahagian and Cawangan accounts use the application portal.
Admin users use the admin portal.

Known roles include:

admin
bahagian
cawangan

For ID Assignment:

Super Admin is treated as username upko, or role super_admin, superadmin, or su.
Admin is treated as role admin or is_admin == True.
Normal users, Bahagian users, and Cawangan users must not access ID Assignment.
8. Main Features
A. Authentication

Route file:

app/routes/auth.py

Templates:

app/templates/auth/login.html
app/templates/admin_login.html

Handles admin/member portal login and logout.

B. Admin Dashboard

Route file:

app/routes/admin.py

Template:

app/templates/admin/dashboard.html

Shows member statistics and admin overview.

C. Member Management

Route file:

app/routes/admin.py

Templates:

app/templates/admin/members.html
app/templates/admin/add_member.html
app/templates/admin/edit_member.html
app/templates/admin/member_form.html

Features:

List members
Search members
Filter members
Add member
Edit member
Delete member
Export/report members

Important fields:

IC
NOID
Full name
Bahagian
DUN
Cawangan
Pusat Mengundi
SPR fields
Birthdate
Registration date

Important validation:

birthdate must be between 1900 and 2099.
registration_date must be between 1900 and 2099.
Frontend validation must not block while typing.
Date popup should only appear when pressing Save Member with an invalid date.
Backend validation should also block invalid dates.
PostgreSQL CHECK constraints exist for invalid birthdate and registration date ranges.
D. Membership Applications

Route file:

app/routes/applications.py

Model:

app/models/membership_application.py

Templates:

app/templates/applications/
app/templates/admin/applications_list.html
app/templates/admin/application_review.html
app/templates/admin/application_accounts.html

Database bind:

applications

Database:

membership_app_db

Workflow:

Bahagian/Cawangan users login to the application portal.
They submit membership applications.
Admin reviews applications.
Admin can approve or reject.
On approval, data is transferred into the main Member table.
Admin must enter approved NOID.
Duplicate NOID must be prevented.

Important:

Application users should not manually assign member IDs unless approved by admin.
Admin approval route must check for duplicate NOID.
Application data must remain separate from main member data until approved.
E. Hierarchy Management

Route file:

app/routes/hierarchy.py

Model:

app/models/hierarchy.py

Templates:

app/templates/hierarchy/view_hierarchy.html
app/templates/hierarchy/document_view.html
app/templates/hierarchy/admin_list.html
app/templates/hierarchy/admin_form.html

Supports:

Majlis Tertinggi
Bahagian
Cawangan

Features:

View hierarchy
Add hierarchy form
Edit full hierarchy document
Delete full hierarchy document
Display hierarchy cleanly
Print hierarchy view

Important:

Hierarchy has editable term/subtitle text.
Default term:
UPKO Bagi Penggal 2026 - 2029
Admin should edit the whole form, not only one row.
Empty name fields during edit mean that position is removed.
Do not break existing hierarchy layout.
F. ID Assignment

Route file:

app/routes/id_assignment.py

Model:

app/models/id_assignment.py

Template:

app/templates/admin/id_assignment.html

Database bind:

id_assignment

Database:

id_assignment_db

Purpose:

This page assigns new member IDs so Admin/Super Admin users do not reuse the same ID.

ID range:

Starts from 162687 and above

Features:

Initial generated IDs: 5000
Generate next 500 IDs button
Available IDs can be ticked
Confirm Selected IDs button
Assigned IDs change colour
Colour indicates which admin assigned the ID
Page shows all users with ID Assignment access
Page shows assigned colour legend
Auto-refresh visible ID statuses
Release button can unassign an ID

Important fields in IdAssignment:

noid
is_assigned
assigned_by_user_id
assigned_by_username
assigned_color
assigned_at
created_at

Concurrency rule:

Assigning an ID must only happen if:

IdAssignment.is_assigned.is_(False)

This prevents duplicate assignment if two admins confirm at the same time.

Critical frontend rule:

Do not rebuild available cards during auto-refresh.

Reason:

Rebuilding available cards recreates the checkbox and clears the user's tick.

Auto-refresh should only rebuild an available card if the card was previously assigned and has now been released.

Access:

Admin allowed
Super Admin allowed
Normal user blocked
Bahagian blocked
Cawangan blocked
9. Current UI / Layout Notes

Main layout file:

app/templates/layout/base.html

The sidebar contains:

Dashboard
Members
ID Assignment
Users
Member Report
Applications
Bahagian Accounts
View Hierarchy
Manage Hierarchy

ID Assignment link should only show for Admin/Super Admin.

Bahagian/Cawangan users should see the application portal menu instead.

10. Known Mistakes To Avoid

Do not reintroduce these problems:

Do not put real DB password back into app/config.py.
Do not commit .env, .sql, .dump, .backup, Members.csv, members_clean.csv, uploads, or logs.
Do not add nested <script> tags.
Do not validate date fields while typing.
Do not make date popup appear before pressing Save Member.
Do not rebuild available ID cards during auto-refresh.
Do not make ID Assignment accessible to Bahagian/Cawangan users.
Do not switch production back to Flask development server.
Production must use Gunicorn on 127.0.0.1:5001.
Do not change database schema without giving SQL/migration instructions.
11. Production Deployment

Production service:

upko_member_portal

Production uses Gunicorn.

Correct systemd status should show:

gunicorn --workers 3 --bind 127.0.0.1:5001 --access-logfile - --error-logfile - app:app

Bad sign:

WARNING: This is a development server
Running on http://127.0.0.1:8000

That means Flask development server is running and must be fixed.

Deployment after GitHub changes:

cd ~/member_portal
git pull origin main
sudo systemctl restart upko_member_portal
sudo systemctl status upko_member_portal --no-pager -l

Check logs:

sudo journalctl -u upko_member_portal -n 120 --no-pager
12. Development Workflow

Preferred workflow:

Read CLAUDE.md.
Inspect relevant files.
Tell user what files will be changed.
Make minimal targeted changes.
Show diff.
User reviews.
Commit.
Push to GitHub.
Pull on server.
Restart service.

Commands on local PC:

git status
git diff
git add .
git commit -m "Describe change"
git push origin main

Commands on server:

cd ~/member_portal
git pull origin main
sudo systemctl restart upko_member_portal
sudo systemctl status upko_member_portal --no-pager -l
13. How Claude Should Respond

When helping with code:

Give exact file paths.
Inspect relevant files first.
Keep changes minimal.
Preserve existing visual style unless asked to redesign.
If user asks for full code, provide full replacement file.
Mention database migrations or SQL if needed.
Never expose secrets.
Never commit real member data.
Use backend validation in addition to frontend validation.
Make sure Flask blueprint names and url_for() names match.
Avoid nested script tags.
Avoid duplicate Jinja block names.
Respect SQLAlchemy binds:
applications
id_assignment
Remind user to restart production service after pulling changes.
14. First Instruction For Claude

When starting a Claude session, the user will say:

Read CLAUDE.md first. Do not change anything yet. Summarize the project structure and wait for my instruction.

Claude should then summarize the project and wait.