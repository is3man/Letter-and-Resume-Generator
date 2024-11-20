from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from docxtpl import DocxTemplate
from flask_pymongo import PyMongo
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
import os

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/myDataBase"
app.secret_key = "your_secret_key"  # Set your secret key here

mongo = PyMongo(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"  # Redirect to login if not logged in

# Define a User class for Flask-Login
class User(UserMixin):
    def __init__(self, user_id, username, password):
        self.id = str(user_id)
        self.username = username
        self.password = password

    @staticmethod
    def get(user_id):
        user_data = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        if user_data:
            return User(user_data["_id"], user_data["username"], user_data["password"])
        return None

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@app.route('/')
def home():
    return render_template('home.html')

# Route for displaying the form
@app.route('/form')
@login_required
def leave_form():
    selected_template = request.args.get('template')
    if selected_template not in ['template1', 'template2', 'template3']:
        flash("Invalid template selected.")
        return redirect(url_for('home'))
    return render_template('form.html', template=selected_template)

@app.route('/letter')
@login_required
def letter():
    return render_template('letter_templates.html')
    

@app.route('/resume')
@login_required
def resume():
    return render_template('resume.html')

# Route for generating the leave request document
@app.route('/generate', methods=['POST'])
@login_required
def generate_leave_request():
    # Retrieve user details from the database
    user_data = mongo.db.users.find_one({"_id": ObjectId(current_user.id)})
    if not user_data:
        flash("User data not found.")
        return redirect(url_for("home"))

    # Prepare the context using the user's saved information
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

    # Load the template and render the context
    doc = DocxTemplate("Letter.docx")
    doc.render(context)

    # Save the generated document to a temporary file
    output_path = "generated_leave_request.docx"
    doc.save(output_path)

    # Redirect to the download route after generating the document
    return redirect(url_for("download"))

@app.route('/download')
@login_required
def download():
    output_path = os.path.join("generated_files", "generated_leave_request.docx")
    return send_file(output_path, as_attachment=True)

@app.route('/change', methods=['POST'])
@login_required
def change():
    return render_template('form.html')

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Basic registration info
        username = request.form.get("username")
        password = request.form.get("password")
        
        # Additional fields for leave request
        your_name = request.form.get("your_name")
        phonenumber = request.form.get("phonenumber")
        email = request.form.get("email")
        dob = request.form.get("dob")
        linkedin = request.form.get("linkedin")

        # Check if user already exists
        if mongo.db.users.find_one({"username": username}):
            mess = "Username already exists."
            return redirect(url_for("register",mess=mess))

        # Hash the password
        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")

        # Insert the new user with additional info into MongoDB
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

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user_data = mongo.db.users.find_one({"_id": ObjectId(current_user.id)})
    
    if request.method == 'POST':
        # Update user data
        your_name = request.form.get('your_name')
        dob = request.form.get('dob')
        your_roll_number = request.form.get('your_roll_number')
        your_course_and_year = request.form.get('your_course_and_year')
        college_name_address = request.form.get('college_name_address')

        mongo.db.users.update_one(
            {"_id": ObjectId(current_user.id)},
            {"$set": {
                "your_name": your_name,
                "dob": dob,
                "your_roll_number": your_roll_number,
                "your_course_and_year": your_course_and_year,
                "college_name_address": college_name_address
            }}
        )

        flash("Profile updated successfully!")
        return redirect(url_for('home'))

    return render_template('edit_profile.html', user=user_data)


@app.route("/login", methods=["GET", "POST"])
def login():
    message = None  # Initialize message as None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user_data = mongo.db.users.find_one({"username": username})

        if user_data and check_password_hash(user_data["password"], password):
            user = User(user_data["_id"], user_data["username"], user_data["password"])
            login_user(user)
            return redirect(url_for("home"))
        else:
            message = "Invalid username or password. Please try again."

    return render_template("login.html", message=message)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for("home"))

@app.route("/homepage")
@login_required
def homepage():
    return render_template("home.html", username=current_user.username)

@app.route('/resumegen',methods=['POST'])
@login_required
def resumegen():
    if request.method == 'POST':
        user_data = mongo.db.users.find_one({"_id": ObjectId(current_user.id)})
        if not user_data:
            flash("User data not found.")
            return redirect(url_for("home"))
        # Collect data from the form
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
            "skills": request.form.getlist("skills[]"),  # Collect skills as a list
            "objective": request.form.get("objective"),
            "experience": []
        }

        # Collect experience as a list of dictionaries
        experience_titles = request.form.getlist("experience[][title]")
        experience_companies = request.form.getlist("experience[][company]")
        experience_start_date= request.form.getlist("experience[][start_date]")
        experience_end_date= request.form.getlist("experience[][end_date]")
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

        # Load the .docx template
        doc = DocxTemplate("resume_templates/resume1.docx")
        doc.render(data)  # Render the template with the collected data

        # Save the generated document
        output_path = "generated_resume.docx"
        doc.save(output_path)

        # Send the file as a response
        return send_file(output_path, as_attachment=True)

    # GET request: show the form
    return render_template("resume_input.html")

@app.route("/bonafide")
@login_required
def bonafide():
    return render_template("bonafide.html")

@app.route("/bona", methods=["POST"])
def bona():
    # Collect form data
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
        "parent" : request.form.get("parent"),
    }
    template = DocxTemplate("BONAFIDE CERTIFICATE.docx")

    # Render the document with the form data
    template.render(data)

    # Save the generated document
    output_filename = "bonafide_certificate.docx"
    template.save(output_filename)

    # Send the generated file as a response to download
    return send_file(output_filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
