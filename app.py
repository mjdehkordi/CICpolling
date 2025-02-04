from flask import Flask, render_template_string, request, session, redirect, url_for
import matplotlib
matplotlib.use('Agg')  # Use Agg backend for Matplotlib (no GUI)
import matplotlib.pyplot as plt
import pandas as pd
import io
import base64
import os
import numpy as np
import csv
import uuid
import threading
import logging

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for session management

# Configure logging to print to the console
logging.basicConfig(level=logging.INFO)  # Log messages at INFO level

# Flag to check if initialization has been done
initialized = False

# Function to initialize active.csv and clear session.csv
def initialize_files():
    # Set 0 in active.csv
    with open('active.csv', 'w') as active_file:
        active_file.write('0')  # Writing 0 to the active.csv file
    
    # Clear the contents of session.csv
    if os.path.exists('session.csv'):
        with open('session.csv', 'w') as session_file:
            session_file.truncate(0)  # Clearing the file content
            
    # Clear the contents of user.csv
    if os.path.exists('users.csv'):
        with open('users.csv', 'w') as session_file:
            session_file.truncate(0)  # Clearing the file content

    
    # Clear Flask session storage
    session.clear()
            
# Run this on application startup using a flag
@app.before_request
def before_request():
    global initialized
    if not initialized:
        initialize_files()
        initialized = True

csv_lock_data = threading.Lock()
csv_lock_session = threading.Lock()
csv_lock_user = threading.Lock()
csv_lock_active = threading.Lock()

def read_csv_data():
    # Read CSV while handling uneven columns 
    with open('data.csv', 'r', encoding='utf-8') as file:
        lines = [line.strip().split(',') for line in file.readlines()]
    # Find max number of columns and pad each row accordingly
    max_columns = max(len(row) for row in lines)
    normalized_data = [row + [''] * (max_columns - len(row)) for row in lines]
    
    return normalized_data

@app.route('/', methods=['GET', 'POST'])
def login():
    # Show the login page where the user can enter their name
    if request.method == 'POST':
        # Save the user's name in the session
        name = request.form['name']
        session['name'] = name
        session['last_id'] = 0  # Initialize last_id to 0 after login

        # Save the username in users.csv
        file_exists = os.path.exists('users.csv')  # Check if file exists
        with csv_lock_user:
            with open('users.csv', mode='a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([name])  # Append the new name

        return redirect(url_for('survey'))  # Redirect to the survey page after login

    # Render the login page
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                margin: 0;
                background-color: #f4f4f9;
            }
            .container {
                text-align: center;
                padding: 40px; /* Increased padding */
                background-color: white;
                box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2); /* Increased shadow */
                border-radius: 16px; /* Increased border radius */
                font-size: 2em; /* Increased font size */
            }
            h1 {
                color: #333;
                font-size: 2em; /* Increased font size */
            }
            form {
                margin-top: 40px; /* Increased margin */
            }
            input[type="text"] {
                padding: 20px; /* Increased padding */
                width: 400px; /* Increased width */
                margin: 20px 0; /* Increased margin */
                border: 2px solid #ccc; /* Increased border thickness */
                border-radius: 8px; /* Increased border radius */
                font-size: 1em; /* Increased font size */
            }
            input[type="submit"] {
                padding: 20px 40px; /* Increased padding */
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px; /* Increased border radius */
                cursor: pointer;
                font-size: 1em; /* Increased font size */
            }
            input[type="submit"]:hover {
                background-color: #45a049;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Please enter your name to continue</h1>
            <form action="/" method="POST">
                <label for="name">Name:</label><br>
                <input type="text" id="name" name="name" required><br>
                <input type="submit" value="Login">
            </form>
        </div>
    </body>
    </html>
    ''')

@app.route('/users')
def users():
    users_list = []

    # Read user names from users.csv
    if os.path.exists('users.csv'):
        with open('users.csv', mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            users_list = [row[0] for row in reader if row]

    user_count = len(users_list)
    users_text = ", ".join(users_list) if users_list else "No users logged in"

    # Render the users page
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <meta http-equiv="refresh" content="3">
        <title>Users</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                margin: 0;
                background-color: #f4f4f9;
            }
            .container {
                text-align: center;
                padding: 20px;
                background-color: white;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                border-radius: 8px;
            }
            h1 {
                color: #333;
            }
            .bold {
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Users Logged In:</h1>
            <p><span class="bold">{{ user_count }}</span></p>
            <p>{{ users_text }}</p>
        </div>
    </body>
    </html>
    ''', user_count=user_count, users_text=users_text)



@app.route('/survey', methods=['GET', 'POST'])
def survey():
    # Check if the user has logged in (i.e., the name exists in the session)
    if 'name' not in session:
        return redirect(url_for('login'))
    
    # Retrieve active ID from active.csv
    try:
        with open('active.csv', 'r') as active_file:
            active_id = int(active_file.read().strip())  # Read and parse active ID
    except FileNotFoundError:
        active_id = 0  # Default to 0 if the file is missing

    # Retrieve last ID from session (initialize if not found)
    last_id = int(session.get('last_id', 0))

    # Modify the condition to check if last_id >= active_id or active_id < 2
    if last_id > active_id or active_id < 2:
        # Display the "Please wait..." page with active and last IDs
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <meta http-equiv="refresh" content="3">
            <title>Please Wait</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    height: 100vh;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    margin: 0;
                    background-color: #f4f4f9;
                }
                .container {
                    text-align: center;
                    padding: 40px; /* Increased padding */
                    background-color: white;
                    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2); /* Increased shadow */
                    border-radius: 16px; /* Increased border radius */
                    width: 800px; /* Increased width */
                }
                h1 {
                    color: #333;
                    font-size: 48px; /* Increased font size */
                }
                p {
                    font-size: 36px; /* Increased font size */
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Please wait...</h1>
            </div>
        </body>
        </html>
        ''')

    # Process the survey as normal if last_id < active_id
    if request.method == 'POST':
        # Retrieve user name and selected opinion from form
        name = session['name']
        selected_opinion = request.form.get('answer')  # The selected radio button value

        # Retrieve the last chart ID from the session
        last_id = session.get('last_id', 'N/A')

        # If no opinion is selected, return to the survey page (though HTML form already prevents empty selection)
        if not selected_opinion:
            return redirect(url_for('survey'))

        # Check if session already has a session_id, if not, create one
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())  # Generate a unique session ID

        # Prepare the data to store in session.csv without the timestamp
        session_id = session['session_id']
        session_data = [session_id, name, last_id, selected_opinion]

        logging.info("user %s sent its upinion",name)


        # Append the data to session.csv
        with csv_lock_session:  # Acquire the lock to prevent concurrent read/write
            with open('session.csv', mode='a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(session_data)
                logging.info("new inserted data: %s",session_data)

        # Update the session's last_id after submission
        session['last_id'] = str(int(last_id) + 1)  # Increment last_id by 1

        # Redirect back to the survey page (or wherever appropriate)
        return redirect(url_for('survey'))


    # Retrieve the name from the session
    name = session['name']

    # Get the row corresponding to the last_id
    data = read_csv_data()
    row = data[int(active_id) - 1]
    chart_title = row[0]  # First column is the chart title
    raw_data = row[1:]  # Remaining columns contain key-value pairs

    # Extract keys from the row to be used as options
    options = [raw_data[i] for i in range(0, len(raw_data), 2)]  # Extract every alternate value (key)
    # Filter out empty keys
    options = [option for option in options if option.strip()]

    # Update the session's last_id after showing
    session['last_id'] = str(int(active_id))
    
    # Display the survey page
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <meta http-equiv="refresh" content="20">
        <title>Survey</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                margin: 0;
                background-color: #f4f4f9;
            }
            .container {
                text-align: center;
                padding: 40px; /* Increased padding */
                background-color: white;
                box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2); /* Increased shadow */
                border-radius: 16px; /* Increased border radius */
                width: 800px; /* Increased width */
            }
            h1 {
                color: #333;
                font-size: 48px; /* Increased font size */
            }
            form {
                margin-top: 40px; /* Increased margin */
                text-align: left;
            }
            .question {
                margin-bottom: 40px; /* Increased margin */
                font-size: 36px; /* Increased font size */
                font-weight: bold;
            }
            .options {
                margin: 20px 0; /* Increased margin */
            }
            .option-item {
                margin-bottom: 30px; /* Increased margin */
            }
            input[type="radio"] {
                margin-right: 20px; /* Increased margin */
                transform: scale(2); /* Increased radio button size */
            }
            input[type="submit"] {
                padding: 20px 40px; /* Increased padding */
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px; /* Increased border radius */
                cursor: pointer;
                font-size: 36px; /* Increased font size */
            }
            input[type="submit"]:hover {
                background-color: #45a049;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Hi, {{ name }}!</h1>
            <form action="/survey" method="POST">
                <div class="question">
                    <p>{{ chart_title }}</p>  <!-- Display chart title as the question -->
                </div>

                <div class="options">
                    {% for option in options %}
                    <div class="option-item"> <!-- Add a class to each radio button line -->
                        <input type="radio" id="{{ option }}" name="answer" value="{{ option }}" required>
                        <label for="{{ option }}" style="font-size: 36px;">{{ option }}</label> <!-- Increased font size -->
                    </div>
                    {% endfor %}
                </div>

                <input type="submit" value="Submit">
            </form>
        </div>
    </body>
    </html>
    ''', name=name, chart_title=chart_title, options=options)

def count_records_in_session(row_id):
    with csv_lock_session:  # Acquire the lock to prevent concurrent access
        with open('session.csv', mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            data = list(reader)

        # Count records where third column == row_id + 1, group by the fourth column
        active_id = row_id + 1
        grouped_data = {}
        
        for row in data:
            if len(row) >= 4 and row[2] == str(active_id):  # Check if third column matches row_id + 1
                key = row[3]  # Fourth column to group by
                if key not in grouped_data:
                    grouped_data[key] = 0
                grouped_data[key] += 1

        return grouped_data


@app.route('/chart')
def chart():
    # Retrieve the 'id' from the GET parameter and store it
    row_id = int(request.args.get('id', 1)) - 1  # Convert ID to zero-based index
    
    # Read the current active ID from the file
    try:
        with open('active.csv', 'r') as active_file:
            current_active_id = int(active_file.read().strip())
    except (FileNotFoundError, ValueError):
        current_active_id = 0  # Default to 0 if the file is missing or has invalid data

    # Update the active ID only if it is lower than row_id + 1
    new_active_id = row_id + 1
    if current_active_id < new_active_id:
        with csv_lock_active:
            with open('active.csv', 'w') as active_file:
                active_file.write(str(new_active_id))  # Store the updated ID

    
    grouped_data = count_records_in_session(row_id)
    
    # Now proceed with the rest of your logic
    data = read_csv_data()

    if row_id < 0 or row_id >= len(data):
        return "Invalid chart ID"

    row = data[row_id]
    chart_title = row[0]  # First column is the chart title
    raw_data = row[1:]  # Remaining columns contain key-value pairs

    labels, values = [], []
    updated_raw_data = []

    # Parse raw_data field by field
    i = 0
    while i < len(raw_data):
        key = raw_data[i].strip()
        value = raw_data[i + 1].strip() if i + 1 < len(raw_data) else ''

        if key in grouped_data:
            # If key is in grouped_data, update it with the grouped value
            updated_raw_data.append(key)  # Keep the key
            updated_raw_data.append(str(grouped_data[key]))  # Use grouped value for the key
        else:
            # If the key is not in grouped_data, keep the original value
            updated_raw_data.append(key)  # Keep the key
            updated_raw_data.append("0")  # Keep the original value

        i += 2  # Move to the next key-value pair
    
    # Update the data at the specific row_id with the new raw_data
    raw_data = updated_raw_data
    data[row_id] = [chart_title] + updated_raw_data

    try:
        # Save all data back to CSV file with locking mechanism
        with csv_lock_data:
            with open('data.csv', mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerows(data)
    except Exception as e:
        app.logger.error(f"Error writing to CSV: {e}")
        return "Error updating chart data."

    labels, values = [], []

    # Process the key-value pairs in updated_raw_data
    for i in range(len(raw_data) - 2, -1, -2):  # Start from the end and move backward
        key, value = raw_data[i], raw_data[i + 1]

        if pd.isna(key) or pd.isna(value) or not key.strip() or not value.strip():
            continue  # Ignore empty or NaN values

        try:
            values.append(float(value.strip()))  # Convert to float
            labels.append(key.strip())  # Store label
        except ValueError:
            continue  # Skip if value is not a valid number

    # Check if there are any valid labels and values
    if not labels or not values:
        return "No valid data for chart"

    # Ensure max_value is not zero before proceeding with chart generation
    max_value = max(values) if values else 1  # Default to 1 if values are empty to avoid division by zero
    if max_value == 0:
        max_value = 1  # Fallback value to avoid zero division
    # Set larger figure size and remove the border
    fig, ax = plt.subplots(figsize=(12, 6))  # Increased panel size

    # Generate colors dynamically
    colors = plt.cm.Paired(np.linspace(0, 1, len(labels)))
    
    # Draw horizontal bars with a fixed panel size
    bar_widths = [v / max_value * 0.8 for v in values]  # Scale bars dynamically

    y_positions = range(len(labels))
    ax.barh(y_positions, bar_widths, color=colors)

    # Remove x and y axis labels and borders
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_yticklabels([])

    # Remove the top and left spines (borders)
    ax.spines['top'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)

    #logging.info("Labels List: %s", labels) 

    # Add text labels for keys and values
    for i in range(len(labels)):
        label = labels[i]
        value = values[i]
        
        # Place the key label on the left side of the bar
        ax.text(-0.1, i, label, va='center', ha='right', fontsize=12, color='black')
        
        # Place the value label on the right side of the bar
        ax.text(bar_widths[i] + 0.02, i, str(int(value)), va='center', fontsize=24)

    # Save the chart as an image without border
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight', pad_inches=0)  # Remove border
    img.seek(0)
    img_base64 = base64.b64encode(img.getvalue()).decode('utf-8')

    # Close the figure to avoid excessive memory usage
    plt.close(fig)

    # Continue rendering the image as before
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta http-equiv="refresh" content="3">
        <title>Chart</title>
    </head>
    <body>
        <h1>{{ title }}</h1>
        <img src="data:image/png;base64,{{ img_base64 }}" alt="Chart" style="width:85%; height:auto;"/>
    </body>
    </html>
    '''
    return render_template_string(html, title=chart_title, img_base64=img_base64)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
