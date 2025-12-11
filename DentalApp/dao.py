from DentalApp import app, db
from datetime import datetime

from models import NguoiDung, NhanVien, UserRole, BoPhanEnum, NhaSi, DichVu, LichHen

def auth_user(username, password, role_from_html):
    # 1. Tìm user theo user/pass
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

def get_user_by_id(user_id):
    return NguoiDung.query.get(user_id)

def load_dentist_list():
    return NhaSi.query.all()

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

if __name__=="__main__":
    with app.app_context():
        import hashlib
        pas ='1'
        print(hashlib.md5(pas.strip().encode('utf-8')).hexdigest())