from flask import Flask, request, render_template
from my_script import process_directories

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run_script', methods=['POST'])
def run_script():
    dir1 = request.form['directory1']
    dir2 = request.form['directory2']
    
    # Call the script function with the provided directories
    result = process_directories(dir1, dir2)
    
    return f"Script executed with directories {dir1} and {dir2}. Result: {result}"

if __name__ == "__main__":
    app.run()

# This is needed for Vercel's Serverless Functions
def handler(event, context):
    from flask import Request
    from werkzeug.wrappers import Response
    
    return Response.from_app(app)(Request(event))
