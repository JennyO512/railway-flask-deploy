from flask import Flask, render_template, request, jsonify, send_from_directory,url_for
from datetime import datetime
import os
import base64
from picture_api import replicate_api_function

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super_secret_key'

@app.route("/", methods=['GET'])
def index():
    return render_template('index.html')

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
 
if __name__ == '__main__':
  app.run(port=5000)
