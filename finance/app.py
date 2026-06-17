import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    user_id = session["user_id"]

    # 1. Obtener efectivo del usuario
    cash_data = db.execute("SELECT cash FROM users WHERE id = ?", user_id)
    cash = cash_data[0]["cash"]

    # 2. Obtener todas las acciones agrupadas
    stocks = db.execute(
        "SELECT symbol, SUM(shares) as total_shares FROM transactions WHERE user_id = ? GROUP BY symbol HAVING total_shares > 0",
        user_id
    )

    # 3. Calcular valores para cada acción
    portfolio = []
    grand_total = cash
    for stock in stocks:
        quote = lookup(stock["symbol"])
        stock_value = quote["price"] * stock["total_shares"]
        grand_total += stock_value

        portfolio.append({
            "symbol": stock["symbol"],
            "shares": stock["total_shares"],
            "price": quote["price"],
            "total": stock_value
        })

    return render_template("index.html", portfolio=portfolio, cash=cash, grand_total=grand_total)




@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "POST":

        symbol = request.form.get("symbol")

        if not symbol:
            return apology("must provide symbol", 400)

        quote = lookup(symbol)

        if not quote:
            return apology("invalid symbol", 400)

        shares = request.form.get("shares")

        try:
            shares = int(shares)
            if shares <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return apology("invalid number of shares", 400)

        cost = quote["price"] * shares

        user = db.execute(
            "SELECT cash FROM users WHERE id = ?",
            session["user_id"]
        )

        cash = user[0]["cash"]

        if cash < cost:
            return apology("can't afford", 400)

        db.execute(
            "UPDATE users SET cash = cash - ? WHERE id = ?",
            cost,
            session["user_id"]
        )

        db.execute(
            "INSERT INTO transactions (user_id, symbol, shares, price) VALUES (?, ?, ?, ?)",
            session["user_id"],
            quote["symbol"],
            shares,
            quote["price"]
        )

        return redirect("/")

    return render_template("buy.html")

@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    # Obtenemos todas las transacciones del usuario ordenadas por fecha
    transactions = db.execute(
        "SELECT * FROM transactions WHERE user_id = ? ORDER BY timestamp DESC",
        session["user_id"]
    )
    return render_template("history.html", transactions=transactions)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # 1. Olvidar cualquier user_id guardado en la sesión
    session.clear()

    # 2. Redirigir al usuario al login
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        # 1. Validar que el símbolo no esté vacío
        if not symbol:
            return apology("must provide symbol", 400)

        # 2. Consultar el precio usando la función lookup
        quote_data = lookup(symbol)

        # 3. Validar si el símbolo es real
        if not quote_data:
            return apology("invalid symbol", 400)

        # 4. Renderizar un template nuevo llamado 'quoted.html' con los datos
        return render_template("quoted.html", quote=quote_data)

    else:
        return render_template("quote.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username:
            return apology("must provide username", 400)

        if not password:
            return apology("must provide password", 400)

        if not confirmation:
            return apology("must provide confirmation", 400)

        if password != confirmation:
            return apology("passwords do not match", 400)

        hash_password = generate_password_hash(password)

        try:
            user_id = db.execute(
                "INSERT INTO users (username, hash) VALUES(?, ?)",
                username,
                hash_password
            )
        except ValueError:
            return apology("username already exists", 400)

        # Iniciar sesión automáticamente
        session["user_id"] = user_id

        return redirect("/")

    return render_template("register.html")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        # Validar entrada
        if not symbol or not shares:
            return apology("missing symbol or shares", 400)

        try:
            shares = int(shares)
            if shares <= 0:
                raise ValueError
        except:
            return apology("invalid number of shares", 400)

        # Verificar cuántas acciones tiene el usuario
        user_shares = db.execute(
            "SELECT SUM(shares) as total_shares FROM transactions WHERE user_id = ? AND symbol = ? GROUP BY symbol",
            session["user_id"], symbol
        )

        if not user_shares or user_shares[0]["total_shares"] < shares:
            return apology("not enough shares", 400)

        # Obtener precio actual
        quote = lookup(symbol)
        price = quote["price"]
        sale_value = price * shares

        # Actualizar base de datos
        db.execute("UPDATE users SET cash = cash + ? WHERE id = ?", sale_value, session["user_id"])
        db.execute("INSERT INTO transactions (user_id, symbol, shares, price) VALUES(?, ?, ?, ?)",
                   session["user_id"], symbol, -shares, price)

        return redirect("/")

    else:
        # Para el GET, pasamos los símbolos que el usuario posee
        stocks = db.execute(
            "SELECT symbol FROM transactions WHERE user_id = ? GROUP BY symbol HAVING SUM(shares) > 0",
            session["user_id"]
        )
        return render_template("sell.html", stocks=stocks)
