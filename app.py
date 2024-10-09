from flask import Flask,render_template,request,redirect,url_for

app = Flask(__name__,template_folder="templates")

@app.route('/')
def show_form():
    return render_template('home.html')

# Route to handle form submission
@app.route('/submit', methods=['POST'])
def submit_form():
    # Retrieve the text line inputs from the form
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')

    return render_template('home.html',name=name)

if __name__ == "__main__":
    app.run(debug=True)