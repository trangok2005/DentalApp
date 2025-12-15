# index
from datetime import datetime, time
from flask import render_template, request, redirect, jsonify
from DentalApp import app, STANDARD_SLOTS, login, db
import dao
from models import UserRole, BoPhanEnum
from flask_login import login_user, logout_user, login_required, current_user


@app.route('/login', methods=['get', 'post'])
def login_index():
    err_msg = None

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        role = request.form.get("role")

        import hashlib
        password = hashlib.md5(password.encode()).hexdigest()
        print(username, password)
        # Ktra
        user = dao.auth_user(username, password, role)

        # Điều hướng theo vai trò
        if user:
            login_user(user)
            if user.VaiTro == UserRole.BenhNhan or (
                    user.VaiTro == UserRole.NhanVien and user.BoPhan == BoPhanEnum.LeTan):
                return redirect("/booking")

            elif user.VaiTro == UserRole.NhaSi:
                return redirect("/medical-record")

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
    active_tab = 'register'  # mặc định ở tab register

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
    return render_template("index.html", active_tab='login')


@login.user_loader
def get_user(user_id):
    return dao.get_user_by_id(user_id=user_id)


@app.route("/logout")
def logout_my_user():
    logout_user()
    return redirect("/")


@app.route("/booking")
@login_required
def booking():
    # STT 1: Load_Form - Tải danh sách Nha sĩ, Dịch vụ, Ngày hiện tại
    today = datetime.now().strftime('%Y-%m-%d')
    DENTISTS = dao.load_dentist_list()
    return render_template("booking.html", dentists=DENTISTS, today=today)


@app.route('/api/get-slots', methods=['POST'])
def get_slots():
    # Nhận dữ liệu từ Client
    data = request.json
    selected_dentist = data.get('dentist')
    selected_date = data.get('date')
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
    # Btn_XacNhan_Click - Lưu vào Database
    data = request.json
    new_appointment = {
        'dentist_id': data.get('dentist'),
        'date': data.get('date'),
        'time': data.get('time'),
        'name': data.get('name'),
        'phone': data.get('phone'),
        'note': data.get('note')
    }
    # import pdb; pdb.set_trace()

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


@app.route('/medical-record', methods=['get', 'post'])
@login_required
def medical_record():
    # patients = dao.load_waiting_patients(current_user.MaNguoiDung)
    services = dao.load_services_list()
    # import pdb; pdb.set_trace()
    return render_template("medical-record.html", services=services)

@app.route('/api/patient-queue')
@login_required
def api_patient_queue():
    try:
        now_time = datetime.now().time()

        lichhens = dao.load_waiting_patients(current_user.MaNguoiDung)
        print(lichhens)
        result = []
        for lh in lichhens:
            result.append({
                "maBenhNhan": lh.MaBenhNhan,
                "maLH": lh.MaLH,
                "hoTen": lh.benhnhan.HoTen,
                "gioKham": lh.GioKham.strftime('%H:%M'),
                "isLate": lh.GioKham < now_time
            })

        return jsonify(result)

    except Exception as ex:
        print("PATIENT QUEUE ERROR:", ex)
        return jsonify({"error": str(ex)}), 500

@app.route('/api/patient/<int:pid>')
def get_patient_info(pid):
    p = dao.get_patient_info(pid)

    if not p:
        return jsonify({"error": "Not found"}), 404

    return jsonify({
        "MaNguoiDung": p.MaNguoiDung,
        "HoTen": p.HoTen,
        "NgaySinh": p.NgaySinh if p.NgaySinh else None,
        "TienSuBenh": p.TienSuBenh or None
    })


@app.route('/api/medicines/search')
def search_medicines_api():
    keyword = request.args.get('q', '')
    medicines = dao.search_medicines(keyword)

    # Convert object to dict
    result = []
    for m in medicines:
        result.append({
            "id": m.MaThuoc,
            "name": m.TenThuoc,
            "unit": m.DonViTinh,
            "price": float(m.DonGia),
            "stock": m.SoLuongTonKho,
            "usage": m.LieuDung
        })
    return jsonify(result)


@app.route('/api/save-examination', methods=['POST'])
@login_required
def api_save_examination():
    try:
        data = request.json

        ma_pdt = dao.save_examination(
            ma_benh_nhan=data.get('maBenhNhan'),
            ma_nha_si=current_user.MaNguoiDung,
            chuan_doan=data.get('chuanDoan'),
            service_ids=data.get('services', []),
            medicines=data.get('medicines', []),
            ma_lich_hen=data.get('maLichHen')
        )

        return jsonify({
            "success": True,
            "maPDT": ma_pdt
        })

    except Exception as ex:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": str(ex)
        }), 500

if __name__ == "__main__":
    with app.app_context():
        print(dao.get_patient_info(1))
        app.run(debug=True)
