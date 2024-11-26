from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from docxtpl import DocxTemplate
from flask_pymongo import PyMongo
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
import os

# Initialize Flask application
app = Flask(__name__)
# Configure MongoDB connection
app.config["MONGO_URI"] = "mongodb://localhost:27017/myDataBase"
# Set a secret key for session management and security
app.secret_key = "your_secret_key"  # Replace with a strong, unique secret key

# Initialize PyMongo for database interactions
mongo = PyMongo(app)

# Set up Flask-Login for user authentication
login_manager = LoginManager()
login_manager.init_app(app)
# Specify the login view for unauthorized access
login_manager.login_view = "login"  # Redirect to login if not logged in

# Custom User class to work with Flask-Login and MongoDB
class User(UserMixin):
    def __init__(self, user_id, username, password):
        # Initialize user with ID, username, and hashed password
        self.id = str(user_id)
        self.username = username
        self.password = password

    @staticmethod
    def get(user_id):
        # Retrieve user from MongoDB by ID
        user_data = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        if user_data:
            return User(user_data["_id"], user_data["username"], user_data["password"])
        return None

# User loader callback for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# Home route - main landing page
@app.route('/')
def home():
    return render_template('home.html')

# Route for displaying leave request form
@app.route('/form')
@login_required
def leave_form():
    # Validate template selection
    selected_template = request.args.get('template')
    if selected_template not in ['template1', 'template2', 'template3']:
        flash("Invalid template selected.")
        return redirect(url_for('home'))
    return render_template('form.html', template=selected_template)

# Routes for different document generation pages
@app.route('/letter')
@login_required
def letter():
    return render_template('letter_templates.html')

@app.route('/resume')
@login_required
def resume():
    return render_template('resume.html')

# Route for generating leave request document
@app.route('/generate', methods=['POST'])
@login_required
def generate_leave_request():
    # Retrieve current user's data from database
    user_data = mongo.db.users.find_one({"_id": ObjectId(current_user.id)})
    if not user_data:
        flash("User data not found.")
        return redirect(url_for("home"))

    # Prepare context for document template
    context = {
        'your_name': user_data.get('your_name'),
        'your_roll_number': request.form.get('your_roll_number'),
        'your_course_and_year': request.form.get('your_course_and_year'),
        'date': request.form.get('date'),
        'name_of_the_teacher': request.form.get('name_of_the_teacher'),
        'designation_teacher_dept': request.form.get('designation_teacher_dept'),
        'college_name_address': request.form.get('college_name_address'),
        'gender': request.form.get('gender'),
        'start_date': request.form.get('start_date'),
        'end_date': request.form.get('end_date'),
        'reason': request.form.get('reason')
    }

    # Load and render Word document template
    doc = DocxTemplate("Letter.docx")
    doc.render(context)

    # Save generated document
    output_path = "generated_leave_request.docx"
    doc.save(output_path)

    # Redirect to download route
    return redirect(url_for("download"))

# Route for downloading generated documents
@app.route('/download')
@login_required
def download():
    output_path = os.path.join("generated_files", "generated_leave_request.docx")
    return send_file(output_path, as_attachment=True)

# Route to change form
@app.route('/change', methods=['POST'])
@login_required
def change():
    return render_template('form.html')

# User registration route
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Collect registration information
        username = request.form.get("username")
        password = request.form.get("password")
        
        # Collect additional user details
        your_name = request.form.get("your_name")
        phonenumber = request.form.get("phonenumber")
        email = request.form.get("email")
        dob = request.form.get("dob")
        linkedin = request.form.get("linkedin")

        # Check if username already exists
        if mongo.db.users.find_one({"username": username}):
            mess = "Username already exists."
            return redirect(url_for("register", mess=mess))

        # Hash the password for secure storage
        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")

        # Insert new user into database
        user_id = mongo.db.users.insert_one({
            "username": username,
            "password": hashed_password,
            "your_name": your_name,
            "phonenumber": phonenumber,
            "dob": dob,
            "email": email,
            "linkedin": linkedin,
        }).inserted_id

        flash("Registration successful! Please log in.")
        return redirect(url_for("login"))

    return render_template("register.html")

# Route for editing user profile
@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    # Retrieve current user's data
    user_data = mongo.db.users.find_one({"_id": ObjectId(current_user.id)})
    
    if request.method == 'POST':
        # Update user profile information
        mongo.db.users.update_one(
            {"_id": ObjectId(current_user.id)},
            {"$set": {
                "your_name": request.form.get('your_name'),
                "dob": request.form.get('dob'),
                "your_roll_number": request.form.get('your_roll_number'),
                "your_course_and_year": request.form.get('your_course_and_year'),
                "college_name_address": request.form.get('college_name_address')
            }}
        )

        flash("Profile updated successfully!")
        return redirect(url_for('home'))

    return render_template('edit_profile.html', user=user_data)

# User login route
@app.route("/login", methods=["GET", "POST"])
def login():
    message = None  # Initialize message variable
    if request.method == "POST":
        # Collect login credentials
        username = request.form.get("username")
        password = request.form.get("password")

        # Find user in database
        user_data = mongo.db.users.find_one({"username": username})

        # Verify credentials
        if user_data and check_password_hash(user_data["password"], password):
            user = User(user_data["_id"], user_data["username"], user_data["password"])
            login_user(user)
            return redirect(url_for("home"))
        else:
            message = "Invalid username or password. Please try again."

    return render_template("login.html", message=message)

# User logout route
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for("home"))

# Homepage route (after login)
@app.route("/homepage")
@login_required
def homepage():
    return render_template("home.html", username=current_user.username)

# Resume generation route
@app.route('/resumegen', methods=['POST'])
@login_required
def resumegen():
    if request.method == 'POST':
        # Retrieve user data
        user_data = mongo.db.users.find_one({"_id": ObjectId(current_user.id)})
        if not user_data:
            flash("User data not found.")
            return redirect(url_for("home"))
        
        # Collect resume data from form
        data = {
            "name": user_data.get("your_name"),
            "title": request.form.get("title"),
            "contact": {
                "phone": user_data.get("phone"),
                "email": user_data.get("email"),
                "linkedin": user_data.get("linkedin")
            },
            "education": {
                "degree": request.form.get("degree"),
                "institution": request.form.get("institution"),
                "honors": request.form.get("honors"),
                "gpa": request.form.get("gpa"),
                "date": request.form.get("graduation_date")
            },
            "skills": request.form.getlist("skills[]"),
            "objective": request.form.get("objective"),
            "experience": []
        }

        # Collect work experience details
        experience_titles = request.form.getlist("experience[][title]")
        experience_companies = request.form.getlist("experience[][company]")
        experience_start_date = request.form.getlist("experience[][start_date]")
        experience_end_date = request.form.getlist("experience[][end_date]")
        experience_duties = request.form.getlist("experience[][duties]")

        # Populate experience data
        for i in range(len(experience_titles)):
            duties_list = experience_duties[i].split(",") if experience_duties[i] else []
            data["experience"].append({
                "title": experience_titles[i],
                "company": experience_companies[i],
                "start_date": experience_start_date[i],
                "end_date": experience_end_date[i],
                "duties": duties_list
            })

        # Load and render resume template
        doc = DocxTemplate("resume_templates/resume1.docx")
        doc.render(data)

        # Save generated resume
        output_path = "generated_resume.docx"
        doc.save(output_path)

        # Send resume for download
        return send_file(output_path, as_attachment=True)

    return render_template("resume_input.html")

# Bonafide certificate route
@app.route("/bonafide")
@login_required
def bonafide():
    return render_template("bonafide.html")

# Generate bonafide certificate route
@app.route("/bona", methods=["POST"])
def bona():
    # Collect bonafide certificate data
    data = {
        "reason": request.form.get("reason"),
        "academic_year": request.form.get("academic_year"),
        "gender": request.form.get("gender"),
        "name": request.form.get("name"),
        "parent_name": request.form.get("parent_name"),
        "your_roll_number": request.form.get("your_roll_number"),
        "course_name": request.form.get("course_name"),
        "year": request.form.get("year"),
        "college": request.form.get("college"),
        "aishe_no": request.form.get("aishe_no"),
        "third_person": request.form.get("third_person"),
        "child": request.form.get("child"),
        "parent": request.form.get("parent"),
    }
    
    # Load bonafide certificate template
    template = DocxTemplate("BONAFIDE CERTIFICATE.docx")

    # Render the document with form data
    template.render(data)

    # Save generated certificate
    output_filename = "bonafide_certificate.docx"
    template.save(output_filename)

    # Send certificate for download
    return send_file(output_filename, as_attachment=True)

# Main application entry point
if __name__ == '__main__':
    # Run the Flask application in debug mode
    app.run(debug=True)