from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
import pymysql
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "nutritrack-secret-key")


def get_db_connection():
    return pymysql.connect(
        host="nutrack-rds.cabxutl8lakb.us-east-1.rds.amazonaws.com",
        user="admin",
        password=os.environ.get("DB_PASSWORD"),
        database="nutritrack",
        cursorclass=pymysql.cursors.DictCursor,
    )


def get_all_records():
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    DATE_FORMAT(record_date, '%d/%m/%Y') AS date,
                    meal_type,
                    food_name,
                    servings,
                    calories,
                    protein,
                    weight
                FROM nutrition_records
                ORDER BY id DESC
                """
            )

            return cursor.fetchall()

    finally:
        connection.close()


def get_record_by_id(record_id):
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    DATE_FORMAT(record_date, '%%d/%%m/%%Y') AS date,
                    meal_type,
                    food_name,
                    servings,
                    calories,
                    protein,
                    weight
                FROM nutrition_records
                WHERE id = %s
                """,
                (record_id,),
            )

            return cursor.fetchone()

    finally:
        connection.close()


def validate_record(form):
    errors = []

    food_name = form.get("food_name", "").strip()
    servings = form.get("servings", "").strip()
    calories = form.get("calories", "").strip()
    protein = form.get("protein", "").strip()
    weight = form.get("weight", "").strip()

    if not food_name:
        errors.append("Food name is required.")

    try:
        servings_value = float(servings)

        if servings_value <= 0 or servings_value > 10:
            errors.append("Servings must be between 1 and 10.")

    except ValueError:
        errors.append("Servings must be a valid number.")

    try:
        calories_value = float(calories)

        if calories_value <= 0 or calories_value > 3000:
            errors.append("Calories must be between 1 and 3000 kcal.")

    except ValueError:
        errors.append("Calories must be a valid number.")

    try:
        protein_value = float(protein)

        if protein_value < 0 or protein_value > 300:
            errors.append("Protein must be between 0 and 300 g.")

    except ValueError:
        errors.append("Protein must be a valid number.")

    if weight:
        try:
            weight_value = float(weight)

            if weight_value < 30 or weight_value > 250:
                errors.append("Weight must be between 30 and 250 kg.")

        except ValueError:
            errors.append("Weight must be a valid number.")

    return errors


@app.route("/login", methods=["GET", "POST"])
def login():
    errors = []

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username:
            errors.append("Username is required.")

        if not password:
            errors.append("Password is required.")

        if not errors:
            connection = get_db_connection()

            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT
                            id,
                            username,
                            password_hash
                        FROM users
                        WHERE username = %s
                        """,
                        (username,),
                    )

                    user = cursor.fetchone()

            finally:
                connection.close()

            if user and check_password_hash(user["password_hash"], password):
                session["user_id"] = user["id"]
                session["username"] = user["username"]

                return redirect(url_for("home"))

            errors.append("Invalid username or password.")

    return render_template("login.html", errors=errors)


@app.route("/register", methods=["GET", "POST"])
def register():
    errors = []

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not username:
            errors.append("Username is required.")

        if not email:
            errors.append("Email is required.")

        if len(password) < 8:
            errors.append("Password must be at least 8 characters.")

        if password != confirm_password:
            errors.append("Passwords do not match.")

        if not errors:
            connection = get_db_connection()

            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT id
                        FROM users
                        WHERE username = %s OR email = %s
                        """,
                        (username, email),
                    )

                    existing_user = cursor.fetchone()

                    if existing_user:
                        errors.append("Username or email is already registered.")
                    else:
                        password_hash = generate_password_hash(password)

                        cursor.execute(
                            """
                            INSERT INTO users (
                                username,
                                email,
                                password_hash
                            )
                            VALUES (%s, %s, %s)
                            """,
                            (username, email, password_hash),
                        )

                        connection.commit()

            finally:
                connection.close()

        if not errors:
            return redirect(url_for("login"))

    return render_template("register.html", errors=errors)


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        errors = validate_record(request.form)

        if errors:
            records = get_all_records()

            return render_template(
                "index.html",
                records=records,
                edit_index=None,
                errors=errors,
            )

        weight = request.form.get("weight", "").strip()
        weight = float(weight) if weight else None

        connection = get_db_connection()

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO nutrition_records (
                        meal_type,
                        food_name,
                        servings,
                        calories,
                        protein,
                        weight,
                        record_date
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        request.form.get("meal_type", "Breakfast"),
                        request.form["food_name"].strip(),
                        float(request.form["servings"]),
                        float(request.form["calories"]),
                        float(request.form["protein"]),
                        weight,
                        date.today(),
                    ),
                )

            connection.commit()

        finally:
            connection.close()

        return redirect("/")

    records = get_all_records()

    return render_template(
        "index.html",
        records=records,
        edit_index=None,
    )


@app.route("/edit/<int:record_id>")
def edit_record(record_id):
    record = get_record_by_id(record_id)

    if record is None:
        return redirect("/")

    records = get_all_records()

    return render_template(
        "index.html",
        records=records,
        record=record,
        edit_index=record_id,
    )


@app.route("/update/<int:record_id>", methods=["POST"])
def update_record(record_id):
    existing_record = get_record_by_id(record_id)

    if existing_record is None:
        return redirect("/")

    errors = validate_record(request.form)

    if errors:
        records = get_all_records()

        record = {
            "id": record_id,
            "date": existing_record["date"],
            "meal_type": request.form.get("meal_type", "Breakfast"),
            "food_name": request.form.get("food_name", ""),
            "servings": request.form.get("servings", ""),
            "calories": request.form.get("calories", ""),
            "protein": request.form.get("protein", ""),
            "weight": request.form.get("weight", ""),
        }

        return render_template(
            "index.html",
            records=records,
            record=record,
            edit_index=record_id,
            errors=errors,
        )

    weight = request.form.get("weight", "").strip()
    weight = float(weight) if weight else None

    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE nutrition_records
                SET
                    meal_type = %s,
                    food_name = %s,
                    servings = %s,
                    calories = %s,
                    protein = %s,
                    weight = %s
                WHERE id = %s
                """,
                (
                    request.form.get("meal_type", "Breakfast"),
                    request.form["food_name"].strip(),
                    float(request.form["servings"]),
                    float(request.form["calories"]),
                    float(request.form["protein"]),
                    weight,
                    record_id,
                ),
            )

        connection.commit()

    finally:
        connection.close()

    return redirect("/")


@app.route("/delete/<int:record_id>")
def delete_record(record_id):
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM nutrition_records
                WHERE id = %s
                """,
                (record_id,),
            )

        connection.commit()

    finally:
        connection.close()

    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)