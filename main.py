from flask import Flask, render_template, request, jsonify, send_from_directory,url_for
from datetime import datetime
import os
import base64
from picture_api import replicate_api_function

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super_secret_key'

# Set the upload folder path
UPLOAD_FOLDER = 'uploaded_images'

# total credits, to be used globally
#total_credits = 5
#used_credits = 0

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





    
if __name__ == '__main__':
  app.run(port=5000)
