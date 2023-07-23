from flask import Flask, render_template, request, jsonify, send_from_directory,url_for, redirect, session
from flask import flash
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy.exc import IntegrityError
import os
import base64
from picture_api import replicate_api_function
import psycopg2
from psycopg2 import sql 
import stripe


app = Flask(__name__)
app.config['SECRET_KEY'] = 'super_secret_key'
app.config['STRIPE_WEBHOOK_SECRET'] = 'STRIPE_WEBHOOK_SECRET'

# Create an intense of the LoginManager class
login_manager = LoginManager()
login_manager.init_app(app)

# Get the connection string from the environment variable
connection_string = os.getenv('DATABASE_URL')

# Set up Flask-Login
#login_manager = LoginManager()
#login_manager.init_app(app)
#login_manager.login_view = 'login'

# Tell Flask-Login how to load the user from the ID
@login_manager.user_loader
def load_user(user_id):
    conn = psycopg2.connect(connection_string)
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE id = id", (user_id,))
    user_data = cur.fetchone()

    conn.close()

    if user_data is None:
        return None

    # Assuming the User class has a constructor that accepts all the fields in the same order they're in the database
    return User(*user_data)
 
class User(UserMixin, db.Model):
    def __init__(self, id, email, password, total_credits, used_credits):
        self.id = id
        self.email = email
        self.password = password
        self.total_credits = total_credits
        self.used_credits = used_credits

    def get_id(self):
        return str(self.id)  # Flask-Login requires this to be a string

    def is_active(self):
        return True  # You can implement your own logic here if needed

    def is_authenticated(self):
        return True  # You can implement your own logic here if needed

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
    # Connect to the PostgreSQL database
    conn = psycopg2.connect(connection_string)
    cur = conn.cursor()

    # Fetch the user's credits from the database
    cur.execute("SELECT total_credits, used_credits FROM users WHERE id = %s", (current_user.id,))
    total_credits, used_credits = cur.fetchone()

    #print the query to see if anything comes up
    result = cur.fetchone()

    # Print the result
    print(result)

    # Assign the result to total_credits and used_credits
    if result is not None:
        total_credits, used_credits = result
    else:
        print("No user found with id:", current_user.id)                              

    conn.close()
    
    # Manage User Credits
    insufficient_credits = False
    
    # total purchased credits (default=5 when user registers)
    #total_credits = current_user.total_credits
    #used_credits = current_user.used_credits
    user_credits = total_credits - used_credits


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
            return render_template('dashboard.html', api_output=True, output_image_link=output[1], original_image_name=filename, user_input=[room_input, style_input], total_credits=total_credits, used_credits=used_credits)

    return render_template('dashboard.html', total_credits=total_credits, used_credits=used_credits)


 
 #this route uploads the picture to the uploaded folder 
@app.route('/uploads/<filename>')
def display_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)    

#this is the route to get paid, it goes to the plan.html file
"""
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

            # newly added 6-22
            # Update the user's total credits in your database
            conn = psycopg2.connect(connection_string)
            cur = conn.cursor()

            cur.execute("UPDATE users SET total_credits = total_credits + %s WHERE email = %s", (total_credits, email))

            conn.commit()
            conn.close()

            flash("A total of {} credits have been updated to your account!".format(total_credits))
            
            #flash("A total of {} credits have been updated to your account!".format(plan))

    return render_template('plan.html')
    """


@app.route('/subscription', methods=['GET', 'POST'])
@login_required
def subscribe():
    if request.method == 'POST':
        email = request.form.get('email', current_user.email)
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
            # Connect to the PostgreSQL database
            conn = psycopg2.connect(connection_string)
            cur = conn.cursor()

            # Fetch the user from the database
            cur.execute("SELECT * FROM users WHERE email = %s;", (email,))
            user_data = cur.fetchone()

            if user_data:
                user = User(*user_data)
                # Update the user's total credits in your database
                cur.execute("UPDATE users SET total_credits = total_credits + %s WHERE email = %s", (total_credits, email))

                conn.commit()
                conn.close()

                flash("Subscription for {} plan created successfully!".format(plan))
            else:
                flash("User not found in database. Please check the email address and try again.")
        return redirect(url_for('dashboard'))  # Redirect to dashboard

    return render_template('plan.html')

    

#updated register route on 7/3 added error checking
#REGISTER ROUTE
@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        print(request.form)
        email = request.form.get('email')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        if not email or not password1 or not password2:
            flash('Missing email or password.')
            return render_template('register.html')

        # Hash and salt the password
        try:
            hashed_password = generate_password_hash(password1, method='sha256', salt_length=8)
        except Exception as e:
            print(f"Error hashing password: {e}")
            flash('Error creating account. Line 312 | Please try again.')
            return render_template('register.html')

        if len(password1) < 7:
            flash('Password must be at least 7 characters.')
        elif password1 != password2:
            flash('Passwords do not match.')
        else:
            try:
                # Connect to the PostgreSQL database
                conn = psycopg2.connect(connection_string)
                cur = conn.cursor()

                # Execute the INSERT statement
                cur.execute(
                    "INSERT INTO users (email, password, total_credits, used_credits) VALUES (%s, %s, %s, %s);",
                    (email, hashed_password, 5, 0)
                )

                # Commit the transaction
                conn.commit()

                # Close the connection
                conn.close()

                # Fetch the user from the database
                cur.execute("SELECT * FROM users WHERE email = %s;", (email,))
                user_data = cur.fetchone()

                if user_data:
                    user = User(*user_data)
                    # Log in the user
                    login_user(user)

                flash('Account created successfully. 5 credits added.')
                return redirect(url_for('dashboard'))

            except IntegrityError:
                flash('User with that email already exists. Please log in instead.')
                return redirect(url_for('login'))
            except Exception as e:
                flash('User with that email already exists. Please log in instead. Line 352')
                return redirect(url_for('login'))

    return render_template('register.html')



# LOGIN USER
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Connect to the PostgreSQL database
        conn = psycopg2.connect(connection_string)
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE email = %s;", (email,))
        user_data = cur.fetchone()

        if user_data:
            user = User(*user_data)
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



@app.route('/update_credits', methods=['POST'])
@login_required
def update_credits():
    # Connect to the PostgreSQL database
    conn = psycopg2.connect(connection_string)
    cur = conn.cursor()

    # Update the user's credits
    cur.execute(
        sql.SQL(
            "UPDATE users SET total_credits = total_credits + 5 WHERE email = %s"
        ),
        [current_user.email]
    )

    # Commit the transaction
    conn.commit()

    # Close the connection
    conn.close()

    # Update the user's credits in the session
    current_user.total_credits += 5

    return jsonify({'status': 'success'})

# ADD 5 CREDITS FOR TESTING PURPOSES (REMOVE THIS AND HTML WHEN DONE TESTING)
@app.route("/credit")
@login_required
def add_credit():
    try:
        # Connect to the PostgreSQL database
        conn = psycopg2.connect(connection_string)
        cur = conn.cursor()

        # Update the user's credits
        cur.execute(
            sql.SQL(
                "UPDATE users SET total_credits = total_credits + 5 WHERE email = %s"
            ),
            [current_user.email]
        )

        # Commit the transaction
        conn.commit()

        # Close the connection
        conn.close()

        # Update the user's credits in the session
        current_user.total_credits += 5

        print("5 extra credits added.")
        return redirect(url_for('dashboard'))
    except AttributeError:
        flash('Please log in to add credits.')
        return redirect(url_for('login'))




@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, app.config['STRIPE_WEBHOOK_SECRET']
        )
    except ValueError as e:
        # Invalid payload
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return 'Invalid signature', 400

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        customer_email = session['customer_details']['email']

        # Connect to the PostgreSQL database
        conn = psycopg2.connect(connection_string)
        cur = conn.cursor()

        # Fetch the user from the database
        cur.execute("SELECT * FROM users WHERE email = %s", (customer_email,))
        user_data = cur.fetchone()

        if user_data:
            user = User(*user_data)
            # Update user's credits based on the plan they purchased
            if session['display_items'][0]['plan']['id'] == 'prod_Nvp3GfvoJl1LiD':
                user.total_credits += 50
            else:
                user.total_credits += 20

            # Update the user's credits in the database
            cur.execute("UPDATE users SET total_credits = %s WHERE email = %s", (user.total_credits, customer_email))
            conn.commit()
            print('User credits updated successfully')

        conn.close()

    return '', 200



# LOGOUT USER
@ app.route("/logout")
#@ login_required
def logout():
    logout_user()
    flash('User logged out successfully.')
    return redirect(url_for('login'))


    
if __name__ == '__main__':
    app.run()
