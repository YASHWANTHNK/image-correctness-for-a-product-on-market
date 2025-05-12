from flask import Flask,url_for,redirect,render_template,request,session
import mysql.connector, os
import pandas as pd
from sklearn.preprocessing import LabelEncoder
import numpy as np
import joblib
from flask import Flask, request, render_template,send_from_directory
import tensorflow as tf
from flask import Flask, render_template, request
import matplotlib.pyplot as plt
from werkzeug.utils import secure_filename
app  = Flask(__name__)
app.secret_key = 'admin'

def executionquery(query,values):
    mycursor.execute(query,values)
    mydb.commit()
    return



mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    port=3306,
    database='network'
)

mycursor = mydb.cursor()

def executionquery(query,values):
    mycursor.execute(query,values)
    mydb.commit()
    return

def retrivequery1(query,values):
    mycursor.execute(query,values)
    data = mycursor.fetchall()
    return data

def retrivequery2(query, params=None):
    mycursor.execute(query, params)  # Use params in the execute statement
    data = mycursor.fetchall()
    return data 
##########################################################

# Home Route
@app.route('/')
def home():
    return render_template('index.html', section='home', message="Welcome to the Home page!")

# Gallery Route
@app.route('/gallery')
def gallery():
    return render_template('index.html', section='gallery', message="Welcome to the Gallery!")

# About Route
@app.route('/about')
def about():
    return render_template('index.html', section='about', message="Learn more About us!")

# Contact Route
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == "POST":
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']
        password = request.form['password']
        c_password = request.form['c_password']

        # Validate passwords
        if password != c_password:
            return render_template('index.html', section='contact', message="Confirm password does not match!")

        # Check if the email already exists
        query = "SELECT email FROM users WHERE email = %s"
        email_data = retrivequery2(query, (email,))
        
        # Create a list of existing emails
        email_data_list = [i[0] for i in email_data]

        if email in email_data_list:
            return render_template('index.html', section='contact', message="Email already exists!")

        # Insert new user into the database
        query = "INSERT INTO users (name, email, password, phone) VALUES (%s, %s, %s, %s)"
        values = (name, email, password, phone)  # Include phone number here
        executionquery(query, values)

        # Redirect to the login route instead of rendering
        return redirect(url_for('login', message="Successfully Registered!"))

    return render_template('index.html', section='contact')



# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        query = "SELECT email FROM users"
        email_data = retrivequery2(query)
        email_data_list = []
        for i in email_data:
            email_data_list.append(i[0])

        if email in email_data_list:
            query = "SELECT name, password FROM users WHERE email = %s"
            values = (email, )
            password__data = retrivequery1(query, values)
            if password == password__data[0][1]:
                global user_email
                user_email = email
                name = password__data[0][0]
                session['name'] = name
                print(f"User name: {name}")
            return render_template('home.html', section='home', message=f"Welcome to Home page, {name}!")
        return render_template('index.html', section='login', message="Invalid credentials!")

    return render_template('index.html', section='login')

####################################################################
@app.route('/mainhome')
def mainhome():
    return render_template('home.html')


# @app.route('/upload', methods=["GET", "POST"])
# def upload():
#     if request.method == "POST":
#         files = request.files['files']
#         print(111111, files)
#         # file = request.files['file']
#         # df = pd.read_csv(file, encoding='latin1') 
#         # df = df.to_html()
#         # return render_template('upload.html', df=df)
#     return render_template('upload.html')

# Path to the folder containing images
dataset_1 = r'static\dataset\clear_images'
# dataset_2 = r'static\dataset\haze'


@app.route('/view_data', methods = ["GET", "POST"])
def view_data():
    if request.method == "POST":
        image_files_1 = [f for f in os.listdir(dataset_1) if f.endswith('.jpg')]
        # image_files_2 = [f for f in os.listdir(dataset_2) if f.endswith('.jpg')]
        return render_template('view_data.html', 
                            image_files_1 = image_files_1, 
                            #    image_files_2 = image_files_2
                            )
    return render_template('view_data.html')



# Image Uploads
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the uploads folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def load_and_preprocess_image(img_path):
    img = tf.io.read_file(img_path)
    img = tf.image.decode_jpeg(img, channels=3)
    img = tf.image.resize(img, size=(384, 384), antialias=True)
    img = img / 255.0
    img = tf.expand_dims(img, axis=0)
    return img

def predict_dehazed_image(model_path, img_path):
    # Load the model from the SavedModel format
    model = tf.saved_model.load(model_path)
    input_img = load_and_preprocess_image(img_path)
    dehazed_img = model(input_img)  # Assuming the model's call signature is correct
    return input_img, dehazed_img

@app.route('/prediction', methods=["GET", "POST"])
def prediction():
    result = None
    if request.method == "POST":
        myfile = request.files['image']
        filename = secure_filename(myfile.filename)
        mypath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        myfile.save(mypath)

        model_path = r'model/trained_model'  # Path to your .pb model
        input_img, dehazed_img = predict_dehazed_image(model_path, mypath)

        # Save the input and dehazed images
        tf.keras.preprocessing.image.save_img(os.path.join(app.config['UPLOAD_FOLDER'], 'input_image.jpg'), input_img[0])
        tf.keras.preprocessing.image.save_img(os.path.join(app.config['UPLOAD_FOLDER'], 'dehazed_image.jpg'), dehazed_img[0])

        result = 1
    return render_template('prediction.html', result=result)


if __name__ == '__main__':
    app.run(debug=True)
