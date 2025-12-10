from DentalApp import app, db
from models import NguoiDung, NhanVien, UserRole, BoPhanEnum

def auth_user(username, password, role_from_html):
    # 1. Tìm user theo user/pass
    user = NguoiDung.query.filter(
        NguoiDung.TaiKhoan == username,
        NguoiDung.MatKhau == password
    ).first()

    if not user:
        return None

    if role_from_html == 'khachhang':
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
