from flask import Flask, request, redirect, url_for, session, render_template, jsonify
import requests
import json
import pandas as pd
from gemini_api import get_csv_insights
import os

app = Flask(__name__)

app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

app.secret_key = 'wow'

# Index route
@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template("index.html")


# Dummy credentials 
USERS = {
    'admin': 'admin123',
    'guest': 'guest123'
}


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if USERS.get(username) == password:
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid username or password')
    return render_template('login.html')


# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/get_flight_trends', methods=['GET'])
def get_flight_trends():
    date = request.args.get("date", "2025-04-02")
    print(date)
    url = "https://api.aviationstack.com/v1/flights?access_key=d24e5c0f4c69a6e6aab874eff9ef0adb"
    querystring = {"date":date}

    try:
        response = requests.get(url, params=querystring)
        data = response.json()

        flights = []
        for flight in data.get("data", [])[:200]:
            flights.append({
                "flight_date": flight.get("flight_date", "N/A"),
                "status": flight.get("flight_status", "N/A"),
                "airline": flight.get("airline", {}).get("name", "N/A"),
                "flight_number": flight.get("flight", {}).get("iata", "N/A"),
                "departure_airport": flight.get("departure", {}).get("airport", "N/A"),
                "departure_time": flight.get("departure", {}).get("scheduled", "N/A"),
                "arrival_airport": flight.get("arrival", {}).get("airport", "N/A"),
                "arrival_time": flight.get("arrival", {}).get("scheduled", "N/A")
            })

        return render_template("trends.html", flights=flights)

    except Exception as e:
        print("Error in API call:", e)
        return render_template("trends.html", flights=[])


@app.route("/gemini", methods=["GET", "POST"])
def gemini_insight():
    summary = None
    if request.method == "POST":
        file = request.files["csv"]
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(filepath)

        df = pd.read_csv(filepath)
        preview = df.head(10).to_csv(index=False)

        prompt = f"Please analyze the following airline booking data and give the overview of data in points summuary:\n\n{preview}"
        summary = get_csv_insights(prompt)

    return render_template("gemini.html", summary=summary)



if __name__ == '__main__':
    app.run(debug=True, port=5000)
