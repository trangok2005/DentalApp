from sqlalchemy import and_

from DentalApp import app, db
from datetime import datetime, date
import hashlib
from flask_login import login_user, logout_user, login_required, current_user


from models import (NguoiDung, NhanVien, UserRole, NhaSi, DichVu, LichHen, BenhNhan, Thuoc,
                    PhieuDieuTriDichVu, PhieuDieuTri, DonThuoc, ChiTietDonThuoc, TrangThaiLichHen)


def auth_user(username, password, role_from_html):
    # 1. Tìm user theo user/pass
    # password = hashlib.md5(password.strip().encode('utf-8')).hexdigest()
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

    elif role_from_html == 'nhanvien':
        return user if user.VaiTro == UserRole.NhanVien else None
    return None


def add_Patient(name, username, password, phone):
    password = hashlib.md5(password.strip().encode('utf-8')).hexdigest()
    user = BenhNhan(HoTen=name, SDT=phone, TaiKhoan=username, MatKhau=password)
    db.session.add(user)
    db.session.commit()


def check_Phone(phone):
    return BenhNhan.query.filter(BenhNhan.SDT == phone).first()


def add_booking(obj):
    # 1. Xác định bệnh nhân là ai
    patient = None

    # TH1: Nếu người dùng đang login là bệnh nhân
    if current_user.is_authenticated and current_user.VaiTro.value == "Patient":
        patient = current_user

    # TH2: Lễ tân đặt hộ (hoặc khách vãng lai)
    else:
        # Kiểm tra xem SĐT này đã có trong DB chưa
        existing_patient = BenhNhan.query.filter_by(SDT=obj['phone']).first()

        if existing_patient:
            # A. Đã có => Dùng lại bệnh nhân này
            patient = existing_patient
            # Có thể cập nhật lại tên nếu lễ tân sửa (tùy chọn)
            # patient.HoTen = obj['name']
        else:
            # B. Chưa có => Tạo bệnh nhân mới
            try:
                # Username lấy theo SĐT để tránh trùng, password mặc định
                patient = add_Patient(
                    name=obj['name'],
                    username=obj['phone'],
                    password=obj['phone'],  # Mật khẩu mặc định là SĐT
                    phone=obj['phone']
                )
                db.session.add(patient)
                db.session.commit()  # Commit để lấy được MaNguoiDung
            except Exception as e:
                db.session.rollback()
                print("Lỗi tạo user mới:", e)
                return False

    # 2. Tạo lịch hẹn
    if patient:
        appt = LichHen(
            NgayKham=obj['date'],
            GioKham=obj['time'],
            GhiChu=obj.get('note'),
            MaNhaSi=obj['dentist_id'],
            MaBenhNhan=patient.MaNguoiDung  # ID lấy từ patient (cũ hoặc mới)
        )
        db.session.add(appt)
        db.session.commit()
        return True

    return False


def get_user_by_id(user_id):
    return NguoiDung.query.get(user_id)


def get_patient_info(pid):
    return BenhNhan.query.get(pid)


def load_dentist_list():
    return NhaSi.query.all()


def load_waiting_patients(dentist_id):
    return LichHen.query.filter(
        LichHen.MaNhaSi == dentist_id,
        LichHen.NgayKham == "2025-12-26",
        LichHen.TrangThai == "ChoKham"
    ).order_by(LichHen.GioKham).all()


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


def save_examination(ma_benh_nhan, ma_nha_si, chuan_doan, service_ids, medicines, ma_lich_hen):
    # 1 tạo phiếu lay id trước
    pdt = PhieuDieuTri(
        NgayLap=date.today(),
        ChuanDoan=chuan_doan,
        MaBenhNhan=ma_benh_nhan,
        MaNhaSi=ma_nha_si
    )
    db.session.add(pdt)
    db.session.flush()

    # 2 thêm dv
    if service_ids:
        dichvus = DichVu.query.filter(
            DichVu.MaDV.in_(service_ids)
        ).all()
        pdt.dichvus = dichvus

    # 3 có kê đơn thì tạo đơn thuốc
    if medicines and len(medicines) > 0:
        donthuoc = DonThuoc(
            NgayKeDon=date.today(),
            MaPDT=pdt.MaPDT
        )
        db.session.add(donthuoc)
        db.session.flush()

        for item in medicines:
            ct = ChiTietDonThuoc(
                MaDT=donthuoc.MaDT,
                MaThuoc=item["maThuoc"],
                SoLuong=item["soLuong"],
                LieuDung=item.get("lieuDung", "")
            )
            db.session.add(ct)

            # Trừ tồn kho
            thuoc = Thuoc.query.get(item["maThuoc"])
            if thuoc:
                thuoc.SoLuongTonKho -= item["soLuong"]
    # 4 cập nhật lich hen đã khám
    lich_hen = LichHen.query.get(ma_lich_hen)
    if lich_hen:
        lich_hen.TrangThai = TrangThaiLichHen.DA_KHAM

    db.session.commit()
    return True, pdt.MaPDT


def get_lich_hen_by_id(ma_lh):
    """Lấy thông tin lịch hẹn theo ID"""
    return LichHen.query.get(ma_lh)


def huy_lich_hen(ma_lh, ghi_chu_huy):
    try:
        lh = LichHen.query.get(ma_lh)
        if lh:
            lh.TrangThai = TrangThaiLichHen.HUY
            # Nối thêm lý do hủy vào ghi chú cũ (nếu có)
            old_note = lh.GhiChu if lh.GhiChu else ""
            lh.GhiChu = f"{old_note} | [Đã hủy: {ghi_chu_huy}]".strip(' | ')

            db.session.commit()
            return True
        return False
    except Exception as e:
        print(f"Lỗi khi hủy lịch: {e}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    with app.app_context():
        # datetime.now().date()
        print(search_medicines("parace"))
