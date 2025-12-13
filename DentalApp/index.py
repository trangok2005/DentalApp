#index
from datetime import datetime
from flask import render_template, request, redirect, jsonify
from DentalApp import app, STANDARD_SLOTS, login, db
import dao
from models import UserRole, BoPhanEnum
from flask_login import login_user, logout_user, login_required, current_user

@app.route('/login', methods = ['get', 'post'])
def login_index():
    err_msg = None

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        role = request.form.get("role")

        # Ktra
        user = dao.auth_user(username, password, role)

        # Điều hướng theo vai trò
        if user:
            login_user(user)
            if user.VaiTro == UserRole.BenhNhan or (user.VaiTro == UserRole.NhanVien and user.BoPhan == BoPhanEnum.LeTan) :
                return redirect("/booking")

            elif user.VaiTro == UserRole.NhaSi:
                return redirect("/")

            # elif user.VaiTro == UserRole.NhanVien:
            #     # Lấy thông tin bộ phận
            #     nv = NhanVien.query.get(user.MaNguoiDung)
            #
            #     if nv.BoPhan == BoPhanEnum.LeTan:
            #         return redirect("/")
            #     elif nv.BoPhan == BoPhanEnum.ThuNgan:
            #         return redirect("/")
            #     elif nv.BoPhan == BoPhanEnum.QuanLy:
            #         return redirect("/")

        # Nếu sai bất kỳ bước nào
        err_msg = "Sai thông tin đăng nhập hoặc vai trò không đúng!"
    return render_template("index.html", error=err_msg)

@app.route('/register', methods=['get', 'post'])
def register_index():
    register_error = None
    active_tab = 'register'   # mặc định ở tab register

    if request.method == "POST":
        password = request.form.get("password")
        confirm = request.form.get("confirm")
        phone = request.form.get("phone")

        if password != confirm:
            register_error = "Mật khẩu không khớp!"
        elif dao.check_Phone(phone):
            register_error = "Số điện thoại đã được đăng ký"
        else:
            name = request.form.get("name")
            username = request.form.get("username")

            try:
                dao.add_Patient(name, username, password, phone)
                active_tab = 'login'
                return render_template(
                    "index.html",
                    success="Đăng ký thành công, vui lòng đăng nhập",
                    active_tab=active_tab
                )
            except Exception as ex:
                db.session.rollback()
                print(ex)
                register_error = "Lỗi hệ thống!"

    return render_template(
        "index.html",
        register_error=register_error,
        active_tab=active_tab
    )

@app.route("/", methods=["get", "post"])
def index():
    # thoat user
    if current_user.is_authenticated:
        return redirect("/logout")
    return render_template("medical-record.html", active_tab='login')

@login.user_loader
def get_user(user_id):
    return dao.get_user_by_id(user_id=user_id)

@app.route("/logout")
def logout_my_user():
    logout_user()
    return redirect("/")

@app.route("/booking")
def booking():
    # STT 1: Load_Form - Tải danh sách Nha sĩ, Dịch vụ, Ngày hiện tại
    today = datetime.now().strftime('%Y-%m-%d')
    DENTISTS = dao.load_dentist_list()
    return render_template("booking.html", dentists=DENTISTS, today=today)


@app.route('/api/get-slots', methods=['POST'])
def get_slots():
    # Nhận dữ liệu từ Client
    data = request.json
    selected_dentist =data.get('dentist')
    selected_date =data.get('date')
    # import pdb; pdb.set_trace()

    # Lấy danh sách lịch hẹn của nha sĩ theo ngày
    booked = dao.get_appointments_by_dentist_and_date(selected_dentist, selected_date)

    # Lấy danh sách giờ đã đặt
    booked_slots = [appt.GioKham.strftime("%H:%M") for appt in booked]
    print(booked_slots)


    total_booked = len(booked_slots)

    # STT 2: Kiểm tra điều kiện >= 5 ca
    if total_booked >= 5:
        return jsonify({
            'status': 'full',
            'message': 'Nha sĩ đã kín lịch (đã đạt 5/5 ca)',
            'booked_count': total_booked
        })

    # STT 4: Sinh_DanhSach_GioTrong
    available_slots = []
    for slot in STANDARD_SLOTS:
        if slot in booked_slots:
            state = 'Đã đặt'
        else:
            state = 'Trống'

        available_slots.append({
            'time': slot,
            'status': state
        })

    return jsonify({
        'status': 'success',
        'booked_count': total_booked,
        'slots': available_slots
    })


@app.route('/api/book', methods=['POST'])
def book_appointment():
    # STT 8: Btn_XacNhan_Click - Lưu vào Database
    data = request.json
    new_appointment = {
        'dentist_id': data.get('dentist'),
        'date': data.get('date'),
        'time': data.get('time'),
        'name': data.get('name'),
        'phone': data.get('phone'),
        'note': data.get('note')
    }
    #import pdb; pdb.set_trace()


    # Kiểm tra trùng lặp (Logic bảo vệ)
    # for appt in appointments_db:
    #     if (appt['dentist'] == new_appointment['dentist'] and
    #             appt['date'] == new_appointment['date'] and
    #             appt['time'] == new_appointment['time']):
    #         return jsonify({'success': False, 'message': 'Giờ này vừa bị người khác đặt!'})
    #

    try:
        dao.add_booking(new_appointment)
    except Exception as ex:
        db.session.rollback()
        print(ex)
        return jsonify({'success': False, 'message': 'Loi he thong!'})

    # Giả lập gửi SMS
    print(f">> SMS gửi đến {new_appointment['phone']}: Đặt lịch thành công lúc {new_appointment['time']}!")

    return jsonify({'success': True, 'message': 'Đặt lịch thành công!'})

@app.route('/medical-record', methods=['POST'])
def medical_record():
    patients = dao.load_waiting_patients()
    services = dao.load_services_list()



if __name__ == "__main__":
    with app.app_context():
        app.run(debug=True)
