from flask import Flask, render_template, request, redirect
from datetime import date


app = Flask(__name__)


records = []


def validate_record(form):

    errors = []

    meal_type = form.get("meal_type", "Breakfast").strip()
    food_name = form.get("food_name", "").strip()
    servings = form.get("servings", "").strip()
    calories = form.get("calories", "").strip()
    protein = form.get("protein", "").strip()
    weight = form.get("weight", "").strip()

    if not food_name:
        errors.append("Food name is required.")

    try:
        servings = float(servings)
        if servings <= 0 or servings > 10:
            errors.append("Servings must be between 1 and 10.")
    except ValueError:
        errors.append("Servings must be a valid number.")

    try:
        calories = float(calories)
        if calories <= 0 or calories > 3000:
            errors.append("Calories must be between 1 and 3000 kcal.")
    except ValueError:
        errors.append("Calories must be a valid number.")

    try:
        protein = float(protein)
        if protein < 0 or protein > 300:
            errors.append("Protein must be between 0 and 300 g.")
    except ValueError:
        errors.append("Protein must be a valid number.")

    if weight:
        try:
            weight = float(weight)
            if weight < 30 or weight > 250:
                errors.append("Weight must be between 30 and 250 kg.")
        except ValueError:
            errors.append("Weight must be a valid number.")

    return errors


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        errors = validate_record(request.form)

        if errors:
            return render_template(
                "index.html", records=records, edit_index=None, errors=errors
            )

        record = {
            "date": date.today().strftime("%d/%m/%Y"),
            "meal_type": request.form.get("meal_type", "Breakfast"),
            "food_name": request.form["food_name"],
            "servings": request.form["servings"],
            "calories": request.form["calories"],
            "protein": request.form["protein"],
            "weight": request.form.get("weight", ""),
        }

        records.append(record)
        return redirect("/")

    return render_template("index.html", records=records, edit_index=None)


@app.route("/delete/<int:index>")
def delete_record(index):
    if 0 <= index < len(records):
        records.pop(index)
    return redirect("/")


@app.route("/edit/<int:index>")
def edit_record(index):
    if index < 0 or index >= len(records):
        return redirect("/")

    record = records[index]
    return render_template(
        "index.html", records=records, record=record, edit_index=index
    )


@app.route("/update/<int:index>", methods=["POST"])
def update_record(index):
    if index < 0 or index >= len(records):
        return redirect("/")

    errors = validate_record(request.form)

    if errors:
        return render_template(
            "index.html",
            records=records,
            record=records[index],
            edit_index=index,
            errors=errors,
        )

    records[index]["food_name"] = request.form["food_name"]
    records[index]["servings"] = request.form["servings"]
    records[index]["calories"] = request.form["calories"]
    records[index]["protein"] = request.form["protein"]
    records[index]["weight"] = request.form.get("weight", "")
    records[index]["meal_type"] = request.form.get("meal_type", "Breakfast")

    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
