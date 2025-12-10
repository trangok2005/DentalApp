from flask import render_template, request, redirect

from DentalApp import app, dao


@app.route("/", methods=["get", "post"])
def index():
    err_msg = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        role = request.form.get("role")

        user = dao.auth_user(username, password, role)

        # Xử lý kết quả
        if user:
            return redirect("booking")
        else:
            err_msg = "Sai thông tin đăng nhập hoặc chọn sai vai trò!"

    return render_template("index.html", error=err_msg)


@app.route("/booking", )
def login_my_user():
    return render_template("booking.html")


if __name__ == "__main__":
    with app.app_context():
        app.run(debug=True)
