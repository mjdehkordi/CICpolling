from flask import Flask
import ssl

# SSL Configuration
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain('cert.pem', 'key.pem')

# Create a Flask app
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

# Run the Flask app with SSL in threaded mode (for handling multiple connections)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4433, ssl_context=context, threaded=True, debug=True)

