from sqlalchemy import and_

from DentalApp import app, db
from datetime import datetime, date
import hashlib
from flask_login import login_user, logout_user, login_required, current_user
from models import NguoiDung, NhanVien, UserRole, BoPhanEnum, NhaSi, DichVu, LichHen, BenhNhan, Thuoc


def auth_user(username, password, role_from_html):
    # 1. Tìm user theo user/pass
    #password = hashlib.md5(password.strip().encode('utf-8')).hexdigest()
    user = NguoiDung.query.filter(
        NguoiDung.TaiKhoan.__eq__(username),
        NguoiDung.MatKhau.__eq__(password)
    ).first()

    if not user:
        return None

    if role_from_html == 'BenhNhan':
        return user if user.VaiTro == UserRole.BenhNhan else None

    elif role_from_html == 'nhasi':
        return user if user.VaiTro == UserRole.NhaSi else None

    # 3. Nếu HTML gửi lên là nhóm nhân viên (letan, thungan, quanly)
    # Thì user phải là NhanVien VÀ có Bộ phận tương ứng
    elif role_from_html in ['letan', 'thungan', 'quanly']:

        # Trước hết phải là Nhân viên đã
        if user.VaiTro != UserRole.NhanVien:
            return None

        # Ép kiểu user về NhanVien để lấy thuộc tính BoPhan
        # (SQLAlchemy thường tự làm, nhưng an toàn thì query lại hoặc check trực tiếp nếu đã load)
        nhan_vien = NhanVien.query.get(user.MaNguoiDung)

        # Mapping string HTML -> Enum Python
        bophan_mapping = {
            'letan': BoPhanEnum.LeTan,
            'thungan': BoPhanEnum.ThuNgan,
            'quanly': BoPhanEnum.QuanLy
        }

        # Kiểm tra bộ phận
        if nhan_vien.BoPhan == bophan_mapping.get(role_from_html):
            return user
        else:
            return None  # Đúng là nhân viên nhưng sai bộ phận (VD: Thu ngân đăng nhập vào Lễ tân)

    return None


def add_Patient(name, username, password, phone):
    password = hashlib.md5(password.strip().encode('utf-8')).hexdigest()
    user = BenhNhan(HoTen=name, SDT=phone, TaiKhoan=username, MatKhau=password)
    db.session.add(user)
    db.session.commit()

def check_Phone(phone):
    return BenhNhan.query.filter(BenhNhan.SDT == phone).first()

def add_booking(obj):

    if current_user.is_authenticated and current_user.VaiTro.value.__eq__("Patient"):
        patient= current_user
    else:
        patient = add_Patient(
            name=obj['name'],
            username=obj['name'],
            password=obj['phone'],
            phone=obj['phone'])
        db.session.add(patient)
        db.session.commit()
        import pdb; pdb.set_trace()
    appt = LichHen(
        NgayKham=obj['date'],
        GioKham=obj['time'],
        TrangThai='ChoKham',
        GhiChu=obj.get('note'),
        MaNhaSi=obj['dentist_id'],
        MaBenhNhan=patient.MaNguoiDung)
    db.session.add(appt)
    db.session.commit()


def get_user_by_id(user_id):
    return NguoiDung.query.get(user_id)

def get_patient_info(pid):
    return BenhNhan.query.get(pid)

def load_dentist_list():
    return NhaSi.query.all()

def load_waiting_patients(dentist_id):
    return LichHen.query.filter(LichHen.MaNhaSi==dentist_id and LichHen.NgayKham == "2025-12-26" and LichHen.TrangThai.__eq__("ChoKham")).order_by(LichHen.GioKham).all()

def load_services_list():
    return DichVu.query.all()


def get_appointments_by_dentist_and_date(dentist_id, date):
    try:
        dentist_id = int(dentist_id)
    except:
        print("Dentist ID không hợp lệ:", dentist_id)
        return []  # Tránh crash app

        # chuyển ngày về kiểu date
    from datetime import datetime
    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
    except:
        print("Ngày không hợp lệ:", date)
        return []
    return (
        LichHen.query
        .filter(LichHen.MaNhaSi == dentist_id, LichHen.NgayKham == date)
        .all()
    )

def search_medicines(keyword):

    today = date.today()
    keyword = keyword.lower()
    return Thuoc.query.filter(
        and_(
            Thuoc.TenThuoc.contains(keyword),
            Thuoc.SoLuongTonKho > 0,
            Thuoc.HanSuDung >= today
        )
    ).all()

if __name__ == "__main__":
    with app.app_context():
        #datetime.now().date()
       print(search_medicines("parace"))
