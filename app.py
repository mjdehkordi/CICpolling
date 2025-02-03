from flask import Flask, render_template_string
import matplotlib.pyplot as plt
import io
import base64
import os

app = Flask(__name__)

@app.route('/')
def index():
    # Data for the bar chart
    labels = ['a', 'b', 'c']
    values = [20, 35, 27]

    # Create a figure
    fig, ax = plt.subplots()

    # Plotting the horizontal bar chart
    ax.barh(labels, values, color=['blue', 'green', 'orange'])

    # Customizing the chart
    ax.set_title('Bar Chart for a, b, and c')
    ax.set_xlabel('Values')
    ax.set_ylabel('Categories')

    # Save the plot to a BytesIO object
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    
    # Convert image to base64 string for embedding in HTML
    img_base64 = base64.b64encode(img.getvalue()).decode('utf-8')

    # Render the HTML template with the image
    html = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Bar Chart</title>
    </head>
    <body>
        <h1>Bar Chart for a, b, and c</h1>
        <img src="data:image/png;base64,{{ img_base64 }}" alt="Bar Chart"/>
    </body>
    </html>
    '''
    return render_template_string(html, img_base64=img_base64)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

