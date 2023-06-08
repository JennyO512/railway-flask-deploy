from flask import Flask, render_template, request, jsonify, send_from_directory,url_for
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from sqlalchemy.exc import IntegrityError
import os
import base64
from picture_api import replicate_api_function

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super_secret_key'

# Create an intense of the LoginManager class
login_manager = LoginManager()
login_manager.init_app(app)

# Get the connection string from the environment variable
connection_string = os.getenv('DATABASE_URL')

# Connect to the PostgreSQL database
conn = psycopg2.connect(connection_string)

# Create a cursor object
cur = conn.cursor()

# Execute a simple query
cur.execute("SELECT * FROM users;")

# Fetch all the rows
rows = cur.fetchall()

for row in rows:
    print(row)

# Don't forget to close the connection
conn.close()


# Set up Flask-Login
#login_manager = LoginManager()
#login_manager.init_app(app)
#login_manager.login_view = 'login'

    
# Tell Flask-Login how to load the user from the ID
@login_manager.user_loader
def load_user(user_id):
    conn = psycopg2.connect(conn_string)
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE id = %s;", (user_id,))
    user_data = cur.fetchone()

    conn.close()

    if user_data is None:
        return None

    # Assuming the User class has a constructor that accepts all the fields in the same order they're in the database
    return User(*user_data)
 
 
class User:
    def __init__(self, id, email, password, total_credits, used_credits):
        self.id = id
        self.email = email
        self.password = password
        self.total_credits = total_credits
        self.used_credits = used_credits

    def get_id(self):
        return str(self.id)  # Flask-Login requires this to be a string

    # TODO Add any other methods required by Flask-Login here (is_authenticated, is_active, is_anonymous)
 

# Set the upload folder path
UPLOAD_FOLDER = 'uploaded_images'

# total credits, to be used globally
total_credits = 5
used_credits = 0

#this is my start
@app.route("/", methods=['GET'])
def index():
    return render_template('index.html')

#this is the upload to folder global variable
uploaded_filename = ""

#this is the route that takes input from the users camera
@app.route('/upload_image', methods=['POST'])
def upload_image():
    global uploaded_filename
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    image_data = request.json['imageData']
    filename = f'{timestamp}_uploaded_image.png'
    uploaded_filename = filename
    with open(f"uploaded_images/{filename}", 'wb') as f:
        f.write(base64.b64decode(image_data.split(',')[1]))
    return jsonify({'message': 'Image uploaded successfully'}), 200

#this is the dashboard route
@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        room_input = request.form['room'].title()
        style_input = request.form['room-style'].title()

        if request.form['hiddenImageInput']:
            filename = uploaded_filename
            print('Uploaded Filename:', filename)
        elif request.files['file']:
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            file = request.files['file']
            filename = file.filename
            filename = f"{timestamp}_{filename}"
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            print('Uploaded Filename:', filename)
            uploaded_image = url_for('static', filename=f"{UPLOAD_FOLDER}/{filename}")

        api_token = os.getenv('REPLICATE_API_TOKEN')
        output = replicate_api_function(room_input, style_input, f'{UPLOAD_FOLDER}/{filename}')

        if output:
            print('API OUTPUT:', output)
            return render_template('dashboard.html', api_output=True, output_image_link=output[1], original_image_name=filename, user_input=[room_input, style_input])

    return render_template('dashboard.html')
 
 #this route uploads the picture to the uploaded folder 
@app.route('/uploads/<filename>')
def display_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)    

#this is the route to get paid, it does to the plan.html file
@app.route('/subscription', methods=['GET', 'POST'])
def subscribe():
    if request.method == 'POST':
        # Get the email and payment token from the form
        email = request.form['email']
        token = request.form['stripeToken']
        plan = request.form.get('plan', 'pro')  # default to 'pro' if no plan is specified

        # Create a new customer in Stripe
        customer = stripe.Customer.create(
            email=email,
            source=token
        )

        # Depending on the plan, set the price ID and credit allocation
        if plan == 'premium':
            price_id = 'prod_Nvp3GfvoJl1LiD'
            total_credits = 50
        else:
            price_id = 'prod_Nvp2Sttg35Wp87'
            total_credits = 20

        # Create a subscription for the customer with your product
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[
                {
                    'price': price_id
                }
            ],
        )

        if subscription.status == 'active':
            flash("A total of {} credits have been updated to your account!".format(plan))

    return render_template('plan.html')

# REGISTER USER
@ app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        print(request.form)
        email = request.form['email']
        password1 = request.form['password1']
        password2 = request.form['password2']

        # hash and salt password
        hashed_password = generate_password_hash(
            password1, method='sha256', salt_length=8)

        new_user = User(email=email, password=hashed_password)

        if len(password1) < 7:
            flash('Password must be at least 7 characters.')
        elif password1 != password2:
            flash('Passwords do not match.')
        else:
            try:
                db.session.add(new_user)
                db.session.commit()
                # login new user
                login_user(new_user)
                flash('Account created successfully. 5 credits added.')
                return redirect(url_for('dashboard'))
            except IntegrityError:
                flash('User with that email already exists. Please log in instead.')
                return redirect(url_for('login'))
    return render_template('register.html')

# LOGIN USER
@ app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                login_user(user)
                flash('Logged in successfully.')
                return redirect(url_for('dashboard'))
            else:
                flash('Password is incorrect, please try again.')
        else:
            flash('User does not exist. Please register instead.')
            return redirect(url_for('register'))
    return render_template('login.html')


# LOGOUT USER
@ app.route("/logout")
#@ login_required
def logout():
    logout_user()
    flash('User logged out successfully.')
    return redirect(url_for('login'))


    
if __name__ == '__main__':
    app.run()
