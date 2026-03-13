from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    number = 42
    return render_template("index.html", num=number)

if __name__ == "__main__":
    app.run(debug=True)