from flask import Flask
from flask import render_template

# creates a Flask application, named app
app = Flask(__name__, template_folder='static')

commandDict = {}

# a route where we will display a welcome message via an HTML template
@app.route("/")
def index():
    return render_template('index.html')

# run the application
def start():
    app.run(port=80, host='0.0.0.0', debug=False, use_reloader=False)

@app.route('/up')
def up():
    commandDict.get("up", None)(None)
    
@app.route('/down')
def down():
    commandDict.get("down", None)(None)
    
@app.route('/left')
def left():
    commandDict.get("left", None)(None)

@app.route('/right')
def right():
    commandDict.get("right", None)(None)

@app.route('/select')
def select():
    commandDict.get("select", None)(None)

@app.route('/back')
def back():
    commandDict.get("back", None)(None)

@app.route('/power')
def power():
    commandDict.get("power", None)(None)

@app.route('/play_pause')
def play_pause():
    commandDict.get("p", None)(None)

@app.route('/search')
def search():
    commandDict.get("search", None)(None)

def setCommandDict(newCommandDict):
    global commandDict
    commandDict = newCommandDict
