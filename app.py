from flask import Flask, render_template, request, jsonify, session
from openaiapi import ResponseData, generate_response


app = Flask(__name__)
app.secret_key = 'chatbotsenumsecretkey1234'

# Renitialiser les variables de session
@app.before_request
def clear_session():
    if request.method == 'GET' and request.referrer != request.url:
        session.clear()

@app.route('/', methods=['POST', 'GET'])
def index():
    if 'response_data' not in session:
        session['response_data'] = ResponseData().to_json()
    response_data = ResponseData.from_json(session['response_data'])

    if request.method == 'POST':
        prompt = request.form['prompt']
        res = {}
        res['answer'] = generate_response(prompt, response_data)
        session['response_data'] = response_data.to_json()
        return jsonify(res), 200
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)