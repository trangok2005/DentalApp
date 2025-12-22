# index
import re
from datetime import datetime, time, date
from flask import render_template, request, redirect, jsonify, url_for, flash, abort, session
from DentalApp import app, STANDARD_SLOTS, login, db
import dao
from models import UserRole, LichHen, NhaSi, BenhNhan, NhanVien, HoaDon, PhieuDieuTri, TrangThaiThanhToan
from flask_login import login_user, logout_user, login_required, current_user
from decorators import dentist_required,booking_required, staff_required

# login -----------------------------------------------------------------
@app.route('/login', methods=['get', 'post'])
def login_index():
    err_msg = None

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        role = request.form.get("role")

        import hashlib
        password = hashlib.md5(password.encode()).hexdigest()

        user = dao.auth_user(username, password, role)

        #print(username, password)
        # Ktra vai trò
        if user:
            login_user(user)
            if user.VaiTro == UserRole.BenhNhan:
                return redirect("/booking")

            elif user.VaiTro == UserRole.NhaSi:
                return redirect("/medical-record")

            elif user.VaiTro == UserRole.NhanVien:
                return redirect("/reception/dashboard")

            elif user.VaiTro == UserRole.QuanLy:
                return redirect("/report-stats")

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

        phone_pattern = r"^(0|\+84)(3|5|7|8|9)[0-9]{8}$"

        # 3. Thực hiện kiểm tra
        if not re.fullmatch(phone_pattern, phone):
            register_error = "Số điện thoại không hợp lệ"
        elif password != confirm:
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

# Đặt lịch --------------------------------------------------------------------------
@app.route("/booking")
@login_required
@booking_required
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
    #print(booked_slots)

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


@app.route('/api/find-patient', methods=['POST'])
def find_patient_by_phone():
    data = request.json
    phone = data.get('phone')

    # Gọi DAO để tìm người dùng (bạn cần viết hàm này trong DAO)
    # Giả sử hàm dao.get_user_by_phone trả về object User hoặc None
    user = dao.check_Phone(phone)

    if user:
        return jsonify({
            'found': True,
            'name': user.HoTen,
            'id': user.MaNguoiDung  # Trả về ID để sau này dùng nếu cần
        })
    else:
        return jsonify({'found': False})


@app.route('/api/book', methods=['POST'])
def book_appointment():
    # Btn_XacNhan_Click - Lưu vào Database
    data = request.json
    new_appointment = {
        'dentist_id': data.get('dentist_id'),
        'date': data.get('date'),
        'time': data.get('time'),
        'name': data.get('name'),
        'phone': data.get('phone'),
        'note': data.get('patientNote')
    }
    # import pdb; pdb.set_trace()

    # Kiểm tra trùng lặp (Logic bảo vệ)
    # for appt in appointments_db:
    #     if (appt['dentist'] == new_appointment['dentist'] and
    #             appt['date'] == new_appointment['date'] and
    #             appt['time'] == new_appointment['time']):
    #         return jsonify({'success': False, 'message': 'Giờ này vừa bị người khác đặt!'})
    #
    #Chống spam:0

    da_co = dao.benhnhan_da_co_lich_trong_ngay(new_appointment['phone'], new_appointment['date'])

    if da_co:
        return jsonify({
            'success': False,
            'message': 'Bạn đã có lịch trong ngày này rồi!'
        })

    try:
        # Gọi hàm add_booking đã được sửa lại logic (xem bước 4)
        result = dao.add_booking(data)

        if result:
            # giả lập gửi SMS
            print(f">> SMS gửi đến {new_appointment['phone']}: Đặt lịch thành công lúc {new_appointment['time']}!")
            return jsonify({'success': True, 'message': 'Đặt lịch thành công!'})
        else:
            return jsonify({'success': False, 'message': 'Không thể tạo lịch hẹn!'})
    except Exception as ex:
        db.session.rollback()
        print(ex)
        return jsonify({'success': False, 'message': 'Loi he thong!'})



# Nha sĩ ------------------------------------------------------------------------
@app.route('/medical-record', methods=['get', 'post'])
@login_required
@dentist_required
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
        #print(lichhens)
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


# Helper để khởi tạo session nếu chưa có
def get_cart():
    if 'exam_cart' not in session:
        session['exam_cart'] = {
            'patient_id': None,
            'appointment_id': None,
            'services': [],  # List dict: {id, name, price, desc}
            'medicines': []  # List dict: {id, name, unit, price, quantity, usage}
        }
    return session['exam_cart']


# 1. API Reset Session khi bắt đầu khám bệnh nhân mới
@app.route('/api/cart/init', methods=['POST'])
@login_required
def init_cart_api():
    data = request.json
    session['exam_cart'] = {
        'patient_id': data.get('maBenhNhan'),
        'appointment_id': data.get('maLichHen'),
        'services': [],
        'medicines': []
    }
    session.modified = True
    return jsonify({"success": True})


# 2. API Thêm Dịch Vụ vào Session
@app.route('/api/cart/add-service', methods=['POST'])
@login_required
def add_service_to_cart():
    cart = get_cart()
    data = request.json  # {id, name, price, desc}

    # Kiểm tra trùng
    exists = any(s['id'] == data['id'] for s in cart['services'])
    if exists:
        return jsonify({"error": "Dịch vụ đã tồn tại"}), 400

    cart['services'].append(data)
    session.modified = True
    return jsonify(cart['services'])  # Trả về danh sách mới nhất


# 3. API Xóa Dịch Vụ khỏi Session
@app.route('/api/cart/remove-service', methods=['POST'])
@login_required
def remove_service_from_cart():
    cart = get_cart()
    service_id = str(request.json.get('id'))

    # Lọc bỏ service có id trùng
    cart['services'] = [s for s in cart['services'] if str(s['id']) != service_id]
    session.modified = True
    return jsonify(cart['services'])


# 4. API Thêm Thuốc vào Session (Xử lý cộng dồn số lượng)
@app.route('/api/cart/add-medicine', methods=['POST'])
@login_required
def add_medicine_to_cart():
    cart = get_cart()
    data = request.json  # {id, name, unit, price, quantity, usage, stock}

    # Kiểm tra thuốc đã có trong giỏ chưa
    found = False
    for item in cart['medicines']:
        if str(item['id']) == str(data['id']):
            # Nếu có rồi thì cộng dồn số lượng và cập nhật liều dùng
            new_qty = item['quantity'] + int(data['quantity'])
            if new_qty > data['stock']:  # Kiểm tra tồn kho lần nữa phía server
                return jsonify({"error": f"Vượt quá tồn kho (Tối đa: {data['stock']})"}), 400

            item['quantity'] = new_qty
            item['usage'] = data['usage']  # Cập nhật liều dùng mới nhất
            found = True
            break

    if not found:
        cart['medicines'].append(data)

    session.modified = True
    return jsonify(cart['medicines'])


# 5. API Xóa Thuốc khỏi Session
@app.route('/api/cart/remove-medicine', methods=['POST'])
@login_required
def remove_medicine_from_cart():
    cart = get_cart()
    med_id = str(request.json.get('id'))
    cart['medicines'] = [m for m in cart['medicines'] if str(m['id']) != med_id]
    session.modified = True
    return jsonify(cart['medicines'])

# 7. API Xóa toàn bộ thuốc trong Session (Dùng cho nút Hủy Bỏ)
@app.route('/api/cart/clear-medicines', methods=['POST'])
@login_required
def clear_medicines_cart():
    cart = get_cart()
    cart['medicines'] = []  # Reset list thuốc về rỗng
    session.modified = True # Bắt buộc có để Flask lưu thay đổi
    return jsonify({"success": True})

# 6. SỬA LẠI API LƯU PHIẾU (Đọc từ Session)
@app.route('/api/save-examination', methods=['POST'])
@login_required
def api_save_examination():
    try:
        data = request.json  # Chỉ chứa chuanDoan, còn lại lấy trong session
        cart = get_cart()

        # Validate cơ bản
        if not cart['patient_id']:
            return jsonify({"success": False, "message": "Phiên làm việc hết hạn hoặc chưa chọn bệnh nhân"}), 400

        if not cart['services']:
            return jsonify({"success": False, "message": "Chưa chọn dịch vụ nào"}), 400

        # Lấy list ID dịch vụ
        service_ids = [s['id'] for s in cart['services']]

        # Map lại cấu trúc thuốc cho hàm DAO
        medicines_payload = [{
            "maThuoc": m['id'],
            "soLuong": m['quantity'],
            "lieuDung": m['lieuDung'] if 'lieuDung' in m else m.get('usage')  # handle naming diff
        } for m in cart['medicines']]

        ma_pdt = dao.save_examination(
            ma_benh_nhan=cart['patient_id'],
            ma_nha_si=current_user.MaNguoiDung,
            chuan_doan=data.get('chuanDoan'),
            service_ids=service_ids,
            medicines=medicines_payload,
            ma_lich_hen=cart['appointment_id']
        )

        # Lưu xong thì clear session
        session.pop('exam_cart', None)

        return jsonify({
            "success": True,
            "maPDT": ma_pdt
        })

    except Exception as ex:
        db.session.rollback()
        print(ex)
        return jsonify({
            "success": False,
            "message": str(ex)
        }), 500


# nhân viên -------------------------------------------------------------
# --- ROUTE 1: DASHBOARD CHÍNH (Chỉ load Lịch hẹn) ---
@app.route('/reception/dashboard')
@staff_required
def reception_dashboard():
    # 1. Lấy tham số filter
    selected_date_str = request.args.get('date', str(date.today()))
    doctor_id = request.args.get('doctor_id')
    keyword = request.args.get('keyword')

    # 2. Query Lịch Hẹn (Giữ nguyên logic cũ của bạn)
    query = LichHen.query.filter(LichHen.NgayKham == selected_date_str)

    if doctor_id and doctor_id != 'all':
        query = query.filter(LichHen.MaNhaSi == doctor_id)

    if keyword:
        query = query.join(BenhNhan).filter(
            (BenhNhan.HoTen.contains(keyword)) | (BenhNhan.SDT.contains(keyword))
        )

    ds_lichhen = query.order_by(LichHen.GioKham.asc()).all()
    ds_nhasi = NhaSi.query.all()

    # KHÔNG TRUYỀN ds_hoadon VÀO ĐÂY NỮA
    return render_template('reception-dashboard.html',
                           ds_lichhen=ds_lichhen,
                           ds_nhasi=ds_nhasi,
                           selected_date=selected_date_str,
                           selected_doctor=int(doctor_id) if doctor_id else None,
                           keyword=keyword if keyword else "")


# --- ROUTE 2: API LẤY HÓA ĐƠN (Lazy Load) ---
@app.route('/api/get-invoices')
def get_invoices_api():
    # 1. Lấy lại các tham số filter từ request AJAX gửi lên
    selected_date_str = request.args.get('date', str(date.today()))
    doctor_id = request.args.get('doctor_id')
    keyword = request.args.get('keyword')

    # 2. Query Hóa Đơn (Logic tìm kiếm giống Dashboard cũ)
    query_hd = HoaDon.query.filter(db.func.date(HoaDon.NgayLap) == selected_date_str)

    if doctor_id and doctor_id != 'all':
        # Join PhieuDieuTri vì HoaDon thường nối qua PhieuDieuTri mới biết bác sĩ nào
        query_hd = query_hd.join(PhieuDieuTri).filter(PhieuDieuTri.MaNhaSi == doctor_id)

    if keyword:
        # Join BenhNhan để tìm tên/sđt
        query_hd = query_hd.join(BenhNhan).filter(
            (BenhNhan.HoTen.contains(keyword)) | (BenhNhan.SDT.contains(keyword))
        )

    # Ưu tiên hóa đơn chưa thanh toán lên đầu
    ds_hoadon = query_hd.order_by(HoaDon.TrangThai.asc()).all()

    # 3. Thay vì trả về JSON, ta trả về file HTML con chứa các thẻ <tr>
    return render_template('includes/_invoice_rows.html', ds_hoadon=ds_hoadon)

#Hóa Đơn --------------------------------------------------------------------------------

@app.route('/dental-bill/<int:ma_hd>')
def dental_bill(ma_hd):
    # 1. Truy vấn trực tiếp Hóa Đơn theo ID
    invoice = HoaDon.query.get(ma_hd)

    if not invoice:
        flash('Không tìm thấy hóa đơn này.', 'danger')
        return redirect(url_for('reception_dashboard'))

    # # 2. Kiểm tra nếu đã thanh toán rồi thì cảnh báo (tùy chọn)
    # if invoice.TrangThaiThanhToan = TrangThaiThanhToan.  # Hoặc check theo Enum của bạn
    #     flash('Hóa đơn này đã được thanh toán.', 'warning')

    return render_template('dental-bill.html', invoice=invoice)



# @app.route('/api/get-dental-bill-info/<int:ma_pdt>', methods=['GET'])
# def get_dental_bill_info(ma_pdt):
#     try:
#         # Gọi hàm xử lý dưới DAO
#         data = dao.get_dental_bill_details(ma_pdt)
#
#         if not data:
#             return jsonify({'success': False, 'message': 'Không tìm thấy phiếu điều trị'}), 404
#
#         # Lấy data
#         tien_kham = data['tien_kham']
#         tien_thuoc = data['tien_thuoc']
#         vat = data['vat']
#         tong_tien = data['tong_tien']
#
#         return jsonify({
#             'success': True,
#             'ho_ten': data['ho_ten'],
#             'tien_kham': tien_kham,
#             'tien_thuoc': tien_thuoc,
#             'vat': vat,
#             'tong_tien': tong_tien
#         })
#
#     except Exception as e:
#         print(f"Lỗi tính hóa đơn: {str(e)}")
#         return jsonify({'success': False, 'message': 'Lỗi hệ thống'}), 500


@app.route('/api-pay', methods=["POST"])
@login_required  # Bắt buộc đăng nhập mới được thanh toán
def pay():
    # 1. Lấy dữ liệu từ Form HTML gửi lên
    ma_hd = request.form.get('ma_hd')
    pttt = request.form.get('payment_method')
    ma_lh = request.form.get('ma_lh')

    # Validate cơ bản
    if not ma_hd or not pttt:
        flash('Lỗi: Thiếu thông tin thanh toán.', 'danger')
        return redirect(url_for('reception_dashboard'))

    # 2. Tạo object dữ liệu
    payment_info = {
        'MaHD': ma_hd,
        'PTTT': pttt,
        'MaNhanVien': current_user.MaNguoiDung if current_user.is_authenticated else None
    }

    try:
        # 3. Gọi DAO để xử lý database
        is_success = dao.complete_payment(payment_info)

        if is_success:
            # Gửi thông báo thành công
            flash('Đã thanh toán hóa đơn thành công!', 'success')
        else:
            # Gửi thông báo thất bại
            flash('Thanh toán thất bại! Hóa đơn có thể đã đóng hoặc lỗi hệ thống.', 'danger')

    except Exception as e:
        print(f"Lỗi thanh toán: {e}")
        flash('Lỗi hệ thống khi xử lý thanh toán.', 'danger')

    # 4. Quay về Dashboard
    return redirect(url_for('reception_dashboard'))


@app.route("/report-stats")
@login_required
def report_stats():
    # Bảo vệ: Chỉ Quản lý mới được vào
    # if current_user.VaiTro != UserRole.QuanLy or \
    #         (isinstance(current_user, NhanVien) and current_user.BoPhan != UserRole.QuanLy):
    if current_user.VaiTro != UserRole.QuanLy:
        return render_template("index.html", error="Bạn không có quyền truy cập trang này!")

    return render_template("report.html")


@app.route("/api/revenue-stats", methods=['POST'])
@login_required
def api_revenue_stats():
    data = request.json
    criteria = data.get('criteria')  # 'month' hoặc 'dentist'
    year = data.get('year', datetime.now().year)
    month = data.get('month')  # Có thể null

    chart_data = {
        'labels': [],
        'data': []
    }

    try:
        if criteria == 'month':
            # Thống kê theo 12 tháng trong năm
            stats = dao.get_revenue_by_month(year)
            print(">>> DATA THỐNG KÊ:", stats)

            # Tạo mảng 12 tháng mặc định là 0
            monthly_data = {i: 0 for i in range(1, 13)}
            for s in stats:
                monthly_data[int(s[0])] = float(s[1])  # s[0] là tháng, s[1] là tổng tiền

            chart_data['labels'] = [f"Tháng {i}" for i in range(1, 13)]
            chart_data['data'] = list(monthly_data.values())

        elif criteria == 'dentist':
            # Thống kê theo bác sĩ
            stats = dao.get_revenue_by_dentist(month, year)
            for s in stats:
                chart_data['labels'].append(s[0])  # Tên bác sĩ
                chart_data['data'].append(float(s[1]))  # Tổng tiền

        return jsonify({'success': True, 'chartData': chart_data})

    except Exception as ex:
        print(ex)
        return jsonify({'success': False, 'message': str(ex)})

if __name__ == "__main__":
    with app.app_context():
       # print(dao.get_patient_info(1))
        app.run(debug=True)
