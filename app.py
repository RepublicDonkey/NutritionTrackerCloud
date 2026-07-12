from datetime import date, timedelta
from functools import wraps
import os
import re

import pymysql
from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

# Never keep a predictable secret key in production.
secret_key = os.environ.get("SECRET_KEY")
if not secret_key:
    raise RuntimeError("SECRET_KEY environment variable is not set.")

app.config.update(
    SECRET_KEY=secret_key,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("FLASK_ENV") == "production",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=2),
)

MEAL_TYPES = {"Breakfast", "Lunch", "Dinner", "Snack","Supper"}
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{3,30}$")
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def get_db_connection():
    """Create a new connection to the NutriTrack MySQL database."""
    return pymysql.connect(
        host=os.environ.get(
            "DB_HOST",
            "nutrack-rds.cabxutl8lakb.us-east-1.rds.amazonaws.com",
        ),
        user=os.environ.get("DB_USER", "admin"),
        password=os.environ.get("DB_PASSWORD"),
        database=os.environ.get("DB_NAME", "nutritrack"),
        cursorclass=pymysql.cursors.DictCursor,
        charset="utf8mb4",
        connect_timeout=10,
        read_timeout=10,
        write_timeout=10,
    )


def login_required(view_function):
    """Redirect unauthenticated visitors to the login page."""

    @wraps(view_function)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view_function(*args, **kwargs)

    return wrapped_view


def get_all_records(user_id):
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
                WHERE user_id = %s
                ORDER BY record_date DESC, id DESC
                """,
                (user_id,),
            )
            return cursor.fetchall()
    finally:
        connection.close()


def get_record_by_id(record_id, user_id):
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
                WHERE id = %s AND user_id = %s
                """,
                (record_id, user_id),
            )
            return cursor.fetchone()
    finally:
        connection.close()


def validate_record(form):
    errors = []

    meal_type = form.get("meal_type", "Breakfast").strip()
    food_name = form.get("food_name", "").strip()
    servings = form.get("servings", "").strip()
    calories = form.get("calories", "").strip()
    protein = form.get("protein", "").strip()
    weight = form.get("weight", "").strip()

    if meal_type not in MEAL_TYPES:
        errors.append("Please select a valid meal type.")

    if not food_name:
        errors.append("Food name is required.")
    elif len(food_name) > 100:
        errors.append("Food name must not exceed 100 characters.")

    try:
        servings_value = float(servings)
        if not 0 < servings_value <= 10:
            errors.append("Servings must be more than 0 and no more than 10.")
    except (TypeError, ValueError):
        errors.append("Servings must be a valid number.")

    try:
        calories_value = float(calories)
        if not 0 < calories_value <= 3000:
            errors.append("Calories must be more than 0 and no more than 3000 kcal.")
    except (TypeError, ValueError):
        errors.append("Calories must be a valid number.")

    try:
        protein_value = float(protein)
        if not 0 <= protein_value <= 300:
            errors.append("Protein must be between 0 and 300 g.")
    except (TypeError, ValueError):
        errors.append("Protein must be a valid number.")

    if weight:
        try:
            weight_value = float(weight)
            if not 30 <= weight_value <= 250:
                errors.append("Weight must be between 30 and 250 kg.")
        except (TypeError, ValueError):
            errors.append("Weight must be a valid number.")

    return errors


def record_form_values(form):
    """Return cleaned and converted record values after validation succeeds."""
    weight = form.get("weight", "").strip()

    return {
        "meal_type": form.get("meal_type", "Breakfast").strip(),
        "food_name": form.get("food_name", "").strip(),
        "servings": float(form.get("servings", "")),
        "calories": float(form.get("calories", "")),
        "protein": float(form.get("protein", "")),
        "weight": float(weight) if weight else None,
    }


@app.route("/")
def landing():
    if "user_id" in session:
        return redirect(url_for("home"))
    return render_template("landing.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("home"))

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
                        SELECT id, username, password_hash
                        FROM users
                        WHERE username = %s
                        """,
                        (username,),
                    )
                    user = cursor.fetchone()
            finally:
                connection.close()

            if user and check_password_hash(user["password_hash"], password):
                session.clear()
                session.permanent = True
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                return redirect(url_for("home"))

            errors.append("Invalid username or password.")

    return render_template("login.html", errors=errors)


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("home"))

    errors = []

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not USERNAME_PATTERN.fullmatch(username):
            errors.append(
                "Username must be 3–30 characters and use only letters, numbers, dots, hyphens, or underscores."
            )

        if not EMAIL_PATTERN.fullmatch(email):
            errors.append("Please enter a valid email address.")

        if len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        elif not any(character.isalpha() for character in password) or not any(
            character.isdigit() for character in password
        ):
            errors.append("Password must contain at least one letter and one number.")

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

                    if cursor.fetchone():
                        errors.append("Username or email is already registered.")
                    else:
                        cursor.execute(
                            """
                            INSERT INTO users (username, email, password_hash)
                            VALUES (%s, %s, %s)
                            """,
                            (username, email, generate_password_hash(password)),
                        )
                        connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                connection.close()

        if not errors:
            return redirect(url_for("login"))

    return render_template("register.html", errors=errors)


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/tracker", methods=["GET", "POST"])
@login_required
def home():
    if request.method == "POST":
        errors = validate_record(request.form)

        if errors:
            return render_template(
                "index.html",
                records=get_all_records(session["user_id"]),
                edit_index=None,
                errors=errors,
                form_data=request.form,
            )

        values = record_form_values(request.form)
        connection = get_db_connection()

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO nutrition_records (
                        user_id,
                        meal_type,
                        food_name,
                        servings,
                        calories,
                        protein,
                        weight,
                        record_date
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        session["user_id"],
                        values["meal_type"],
                        values["food_name"],
                        values["servings"],
                        values["calories"],
                        values["protein"],
                        values["weight"],
                        date.today(),
                    ),
                )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

        return redirect(url_for("home"))

    return render_template(
        "index.html",
        records=get_all_records(session["user_id"]),
        edit_index=None,
    )


@app.route("/edit/<int:record_id>")
@login_required
def edit_record(record_id):
    record = get_record_by_id(record_id, session["user_id"])

    if record is None:
        return redirect(url_for("home"))

    return render_template(
        "index.html",
        records=get_all_records(session["user_id"]),
        record=record,
        edit_index=record_id,
    )


@app.route("/update/<int:record_id>", methods=["POST"])
@login_required
def update_record(record_id):
    existing_record = get_record_by_id(record_id, session["user_id"])

    if existing_record is None:
        return redirect(url_for("home"))

    errors = validate_record(request.form)

    if errors:
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
            records=get_all_records(session["user_id"]),
            record=record,
            edit_index=record_id,
            errors=errors,
        )

    values = record_form_values(request.form)
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE nutrition_records
                SET meal_type = %s,
                    food_name = %s,
                    servings = %s,
                    calories = %s,
                    protein = %s,
                    weight = %s
                WHERE id = %s AND user_id = %s
                """,
                (
                    values["meal_type"],
                    values["food_name"],
                    values["servings"],
                    values["calories"],
                    values["protein"],
                    values["weight"],
                    record_id,
                    session["user_id"],
                ),
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    return redirect(url_for("home"))


@app.route("/delete/<int:record_id>", methods=["POST"])
@login_required
def delete_record(record_id):
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM nutrition_records
                WHERE id = %s AND user_id = %s
                """,
                (record_id, session["user_id"]),
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    return redirect(url_for("home"))


@app.errorhandler(404)
def page_not_found(error):
    return redirect(url_for("landing"))


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5000")),
        debug=os.environ.get("FLASK_DEBUG") == "1",
    )