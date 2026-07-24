# Advanced Online Voting System

An advanced, secure, and modern web application built using Python, Flask, and SQLite. This system guarantees a strict one-vote-per-user policy, provides dynamic candidate management, secure password hashing, and real-time visualization of election results.

## Features Required for Final-Year Projects

1. **Authentication & Security:** 
   - Secure login and registration with validation.
   - Passwords are salt-hashed securely via `Flask-Bcrypt`.
   - Built-in fraud prevention ensuring single vote per registered `voter_id`.
2. **Role-Based Access Control (RBAC):**
   - **Admin:** Special dashboard to add/remove candidates, set voting deadlines, declare results, reset entire elections, and export CSVs.
   - **User:** Clean interface to review candidate agendas and securely place their vote.
3. **Advanced UI/UX:**
   - Responsive design utilizing Bootstrap 5 and custom CSS (glassmorphism/gradients).
   - Interactive pop-ups (SweetAlert2) to confirm user actions.
   - Real-time vote display dashboards using `Chart.js`.
4. **Election Logic Restrictions:**
   - Vote locks automatically triggered when admin disables specific bounds or when deadlines exceed the current local time.

---

## 🚀 Setup & Execution Instructions

To set up and run the system locally on your machine, follow these simple steps:

1. **Ensure Python is installed.** (Python 3.8+ recommended).
2. **Open the project folder (`Online Voting System`) in your Terminal.**
3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Initialize the Database:**
   ```bash
   python init_db.py
   ```
   *This command creates the database schemas and automatically seeds the default administrator account.*

5. **Run the Server:**
   ```bash
   python app.py
   ```
6. **Open browser** and visit `http://127.0.0.1:5000`

### Example Data

**To log in as Administrator:**
- **Voter ID:** `admin`
- **Password:** `admin123`

**Normal Voter Workflow:**
- Click "Register". Provide Name, Voter ID, and Password.
- Login using your Voter ID to access the User Dashboard.

---

## 📝 Explanation for Viva (Defense Questions & Answers)

**Q: What is the primary architecture of this application?**  
> We use a typical Model-View-Controller (MVC) approach implemented via Flask. Our `models.py` outlines the SQLite schemas (Model), our `templates/` folder contains Jinja2 HTML templates (View), and the logic mapped to routes in `app.py` acts as our Controller.

**Q: How do you guarantee a user cannot vote twice?**  
> Upon placing the vote via an AJAX request, our server checks the `has_voted` boolean column inside the `Users` table for the session's active `current_user`. Since it runs locally on a robust ORM transaction (SQLAlchemy), if `has_voted` is true, the request returns immediately with a 400 Bad Request prohibiting duplicate entries.

**Q: Why use SQLite? Wait, is it secure enough?**  
> SQLite is exceptional for zero-configuration testing and prototype scaling scenarios like a college project. In a real-world enterprise situation, moving to PostgreSQL or MySQL is simply a one-line config change inside our `app.py` due to using Flask-SQLAlchemy (which heavily abstracts SQL language syntax).

**Q: How does password security function under the hood?**  
> We utilize `Flask-Bcrypt`. Instead of saving raw text passwords into the database (which is extremely vulnerable to breach), Bcrypt salts the passwords and runs heavily computational hashing. To authenticate, we hash the provided string again upon login and compare the hashes dynamically securely.

**Q: How is real-time visualization active?**  
> We utilize Chart.js tied to a REST API Endpoint (`/api/results`) returning JSON data. The client-side dashboard uses basic JavaScript `fetch()` interval intervals to asynchronously fetch new vote aggregates every 15 seconds making it highly concurrent and "real-time" without needing Websockets!
