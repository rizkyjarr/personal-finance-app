from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "<h1>HELLO FROM FLASK!</h1><p>If you see this, Flask is working!</p>"

if __name__ == '__main__':
    app.run(debug=True, port=5001)