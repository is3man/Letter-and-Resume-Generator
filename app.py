from flask import Flask, render_template, request, send_file, redirect, url_for, flash, make_response
from docxtpl import DocxTemplate
from flask_pymongo import PyMongo
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from verify_email import verify_email
import os
from functools import wraps

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

@app.after_request
def add_cache_control_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "-1"
    return response

# Home route - main landing page
@app.route('/')
def home():
    return render_template('home.html')

# Route for displaying leave request form
@app.route('/form')
@login_required
def leave_form():
    selected_template = request.args.get('template')
    templates = {
            'template1': 'form.html',
            'template2': 'form_template2.html',
        }
        
    if selected_template not in templates:
        flash("Invalid template selected.")
        return redirect(url_for('home'))
        
        # Render the specific template
    return render_template(templates[selected_template], template=selected_template)

@app.route('/resume')
@login_required
def resume():
    selected_template = request.args.get('template')
    templates = {
        'template1': 'resume.html',
        'template2': 'resume2.html',
        'template3': 'resume3.html'
    }

    if selected_template not in templates:
        flash("Invalid template selected.")
        return redirect(url_for('home'))

    # Render the specific template
    return render_template(templates[selected_template])
    
# Routes for different document generation pages
@app.route('/letter')
@login_required
def letter():
    return render_template('letter_templates.html')

@app.route('/resume_temp')
@login_required
def resumetemp():
    return render_template('resume_templates.html')

# Route for generating leave request document
@app.route('/generate', methods=['POST'])
@login_required
def generate_leave_request():
    user_data = mongo.db.users.find_one({"_id": ObjectId(current_user.id)})
    if not user_data:
        flash("User data not found.")
        return redirect(url_for("home"))

    context = {
        'fname': user_data.get('fname'),
        'lname': user_data.get('lname'),
        'your_roll_number': request.form.get('your_roll_number'),
        'your_course_and_year': request.form.get('your_course_and_year'),
        'date': request.form.get('date'),
        'principal': request.form.get('principal'),
        'class_guide': request.form.get('name_of_the_teacher'),
        'designation': request.form.get('designation'),
        'college': request.form.get('college'),
        'gender': request.form.get('gender'),
        'start_date': request.form.get('start_date'),
        'end_date': request.form.get('end_date'),
        'no': request.form.get('no')
    }

    template_path = "Letter.docx"
    if not os.path.exists(template_path):
        flash("Template not found.")
        return redirect(url_for("home"))

    doc = DocxTemplate(template_path)
    doc.render(context)

    output_path = os.path.join("generated_files", "generated_leave_request.docx")
    doc.save(output_path)

    return redirect(url_for("download"))

@app.route('/generate1', methods=['POST'])
@login_required
def generate_leave_request2():
    user_data = mongo.db.users.find_one({"_id": ObjectId(current_user.id)})
    if not user_data:
        flash("User data not found.")
        return redirect(url_for("home"))

    context = {
        'fname': user_data.get('fname'),
        'lname': user_data.get('lname'),
        'your_roll_number': request.form.get('your_roll_number'),
        'your_course_and_year': request.form.get('your_course_and_year'),
        'date': request.form.get('date'),
        'class_guide': request.form.get('name_of_the_teacher'),
        'designation': request.form.get('designation'),
        'college': request.form.get('college'),
        'gender': request.form.get('gender'),
        'start_date': request.form.get('start_date'),
        'end_date': request.form.get('end_date'),
    }

    template_path = "func.docx"
    if not os.path.exists(template_path):
        flash("Template not found.")
        return redirect(url_for("home"))

    doc = DocxTemplate(template_path)
    doc.render(context)

    output_path = os.path.join("generated_files", "generated_leave_request.docx")
    doc.save(output_path)

    return redirect(url_for("download"))

@app.route('/download')
@login_required
def download():
    output_path = os.path.join("generated_files", "generated_leave_request.docx")
    if not os.path.exists(output_path):
        flash("Generated file not found.")
        return redirect(url_for("home"))
    return send_file(output_path, as_attachment=True)

# Route to change form
@app.route('/change', methods=['POST'])
@login_required
def change():
    return render_template('form.html')

# User registration route
@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        fname = request.form.get("fname")
        lname = request.form.get("lname")
        phonenumber = request.form.get("phonenumber")
        email = request.form.get("email")
        dob = request.form.get("dob")
        linkedin = request.form.get("linkedin")
        address =  request.form.get("address")

        if mongo.db.users.find_one({"username": username}):
            flash("Username already exists.")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")

        mongo.db.users.insert_one({
            "username": username,
            "password": hashed_password,
            "fname": fname,
            "lname": lname,
            "phonenumber": phonenumber,
            "email": email,
            "dob": dob,
            "linkedin": linkedin,
            "address": address,
        })

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
    # Redirect already logged-in users to the homepage
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    message = None  # Initialize message variable
    if request.method == "POST":
        # Collect login credentials
        username = request.form.get("username")
        password = request.form.get("password")

        # Find user in the database
        user_data = mongo.db.users.find_one({"username": username})

        # Verify credentials
        if user_data and check_password_hash(user_data["password"], password):
            user = User(user_data["_id"], user_data["username"], user_data["password"])
            login_user(user)
            return redirect(url_for("home"))
        else:
            message = "Invalid username or password. Please try again."

    # Render the login page with cache-control headers
    response = make_response(render_template("login.html", message=message))
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "-1"
    return response

# User logout route
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    response = make_response(redirect(url_for("home")))
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "-1"
    return response

# Homepage route (after login)
@app.route("/homepage")
@login_required
def homepage():
    return render_template("home.html", username=current_user.username)

@app.route("/profile")
def profile():
        # Retrieve user data
    user_data = mongo.db.users.find_one({"_id": ObjectId(current_user.id)})
    if not user_data:
        return render_template("profile.html", error="User data not found.")
    
    data = {
        'fname': user_data.get('fname'),
        'lname': user_data.get('lname'),
        'phonenumber': user_data.get('phonenumber'),
        'email': user_data.get('email'),
        'linkedin': user_data.get('linkedin'),
        "addr": user_data.get("address")
    }
    return render_template("profile.html",data=data)

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
            "fname": user_data.get("fname"),
            "lname": user_data.get("lname"),
            "title": request.form.get("title"),
            "contact": {
                "phonenumber": user_data.get("phonenumber"),
                "email": user_data.get("email"),
                "linkedin": user_data.get("linkedin"),
                "addr": user_data.get("address")
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
        doc = DocxTemplate("resume_templates/resume-template-2.docx")
        doc.render(data)

        # Save generated resume
        output_path = "generated_resume.docx"
        doc.save(output_path)

        # Send resume for download
        return send_file(output_path, as_attachment=True)

    return render_template("resume_input.html")

@app.route('/resumegen2', methods=['POST'])
@login_required
def resumegen2():
    if request.method == 'POST':
        # Retrieve user data
        user_data = mongo.db.users.find_one({"_id": ObjectId(current_user.id)})
        if not user_data:
            flash("User data not found.")
            return redirect(url_for("home"))
        
        # Collect resume data from form
        data = {
            "fname": user_data.get("fname"),
            "lname": user_data.get("lname"),
            "title": request.form.get("title"),
            "contact": {
                "phonenumber": user_data.get("phonenumber"),
                "email": user_data.get("email"),
                "linkedin": user_data.get("linkedin"),
                "addr": user_data.get("address")
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

@app.route('/resumegen3', methods=['POST'])
@login_required
def resumegen3():
    if request.method == 'POST':
        # Retrieve user data
        user_data = mongo.db.users.find_one({"_id": ObjectId(current_user.id)})
        if not user_data:
            flash("User data not found.")
            return redirect(url_for("home"))
        
        # Collect resume data from form
        data = {
            "fname": user_data.get("fname"),
            "lname": user_data.get("lname"),
            "title": request.form.get("title"),
            "contact": {
                "phonenumber": user_data.get("phonenumber"),
                "email": user_data.get("email"),
                "linkedin": user_data.get("linkedin"),
                "addr": user_data.get("address")
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
        doc = DocxTemplate("resume_templates/resume-template-4.docx")
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