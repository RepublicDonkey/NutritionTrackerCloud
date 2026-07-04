from flask import Flask, render_template, request , redirect
from datetime import date

app = Flask(__name__)

records = []

@app.route("/", methods=["GET", "POST"])
def home():
    
    if request.method == "POST":
        record_date = date.today().strftime("%d/%m/%Y")
        meal_type = request.form.get("meal_type", "Breakfast")
        food_name = request.form["food_name"]
        servings = request.form["servings"]
        calories = request.form["calories"]
        protein = request.form["protein"]
        weight = request.form.get("weight","")
        

        record = {
            "date": record_date,
            "meal_type": meal_type,
            "food_name": food_name,
            "calories": calories,
            "protein": protein,
            "weight": weight,
            "servings": servings,
            
        }

        records.append(record)
        return redirect("/")

    return render_template(
         "index.html",
         records=records,
         edit_index=None


     )   
    

@app.route("/delete/<int:index>")
def delete_record(index):
    records.pop(index)
    return redirect("/")

@app.route("/edit/<int:index>")
def edit_record(index):
    if index < 0 or index >= len(records):
        return redirect("/")

    record = records[index]
    return render_template("index.html", records=records, record=record, edit_index=index)
    


@app.route("/update/<int:index>", methods=["POST"])
def update_record(index):

    records[index]["food_name"] = request.form["food_name"]
    records[index]["servings"] = request.form["servings"]
    records[index]["calories"] = request.form["calories"]
    records[index]["protein"] = request.form["protein"]
    records[index]["weight"] = request.form.get("weight","")
    records[index]["meal_type"] = request.form.get("meal_type", "Breakfast")
    records[index]["servings"] = request.form["servings"]

    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)