from sqlalchemy import and_, func

from DentalApp import app, db
from datetime import datetime, date
import hashlib
from flask_login import login_user, logout_user, login_required, current_user


from models import (NguoiDung, NhanVien, UserRole, NhaSi, DichVu, LichHen, BenhNhan, Thuoc,
                    PhieuDieuTriDichVu, PhieuDieuTri, DonThuoc, ChiTietDonThuoc, TrangThaiLichHen, HoaDon, TrangThaiThanhToan)


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

def benhnhan_da_co_lich_trong_ngay(phone, ngay_kham):
    bn = BenhNhan.query.filter(BenhNhan.SDT == phone).first()
    return db.session.query(LichHen).filter(
        LichHen.MaBenhNhan == bn.MaNguoiDung,
        LichHen.NgayKham == ngay_kham,
        LichHen.TrangThai != 'Huy'
    ).first()

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
        LichHen.NgayKham == date.today(),
        LichHen.TrangThai == TrangThaiLichHen.CHO_KHAM
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

    # Biến để cộng dồn tiền
    tong_tien_dv = 0
    tong_tien_thuoc = 0

    # 2 thêm dv
    if service_ids:
        dichvus = DichVu.query.filter(
            DichVu.MaDV.in_(service_ids)
        ).all()
        pdt.dichvus = dichvus

        # Cộng tiền dịch vụ
        for dv in dichvus:
            tong_tien_dv += dv.DonGia

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

            thuoc_db = Thuoc.query.get(ct.MaThuoc)
            if thuoc_db:
                # Trừ kho
                thuoc_db.SoLuongTonKho -= ct.SoLuong

                # Tính tiền: Giá bán * Số lượng
                tong_tien_thuoc += (thuoc_db.DonGia * ct.SoLuong)


    # 4 cập nhật lich hen đã khám
    lich_hen = LichHen.query.get(ma_lich_hen)
    if lich_hen:
        lich_hen.TrangThai = TrangThaiLichHen.DA_KHAM

        # 5. TẠO HÓA ĐƠN (Mới thêm)
        hoa_don = HoaDon(
            MaBenhNhan=ma_benh_nhan,
            MaPDT=pdt.MaPDT,
            TongTienDV=tong_tien_dv,
            TongTienThuoc=tong_tien_thuoc
        )
        db.session.add(hoa_don)

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

#Hoa don ------------------------------------------------------------------
def load_invoice(ma_lh: int):
    lh = LichHen.query.get(ma_lh)

    if not lh:
        return None

    pdt = PhieuDieuTri.query.filter_by(
        MaBenhNhan=lh.MaBenhNhan,
        NgayLap=lh.NgayKham,
        MaNhaSi=lh.MaNhaSi
    ).first()
    print(pdt)

    if not pdt:
        return None

    return pdt.hoadon


# def search_medicines(keyword):
#     today = date.today()
#     keyword = keyword.lower()
#     return Thuoc.query.filter(
#         and_(
#             Thuoc.TenThuoc.contains(keyword),
#             Thuoc.SoLuongTonKho > 0,
#             Thuoc.HanSuDung >= today
#         )
#     ).all()
#
# def get_dental_bill_details(ma_pdt):
#     # 1. Lấy phiếu điều trị
#     pdt = PhieuDieuTri.query.get(ma_pdt)
#
#     if not pdt:
#         return None
#
#     # 2. Lấy tên bệnh nhân (BenhNhan kế thừa NguoiDung nên có HoTen)
#     ten_benh_nhan = pdt.benhnhan.HoTen if pdt.benhnhan else "Khách vãng lai"
#
#     # 3. Tính tiền dịch vụ
#     # pdt.dichvus là relationship Many-to-Many đã định nghĩa trong models
#     tong_tien_dv = 0
#     for dv in pdt.dichvus:
#         tong_tien_dv += float(dv.DonGia)  # Convert Decimal sang float
#
#     # 4. Tính tiền thuốc
#     tong_tien_thuoc = 0
#     # Kiểm tra xem phiếu có đơn thuốc không (vì quan hệ 1-1 có thể null)
#     if pdt.donthuoc:
#         for ct in pdt.donthuoc.chitiet:
#             # ct.thuoc là relationship lấy thông tin thuốc
#             # ct.SoLuong lấy từ bảng chi tiết
#             don_gia_thuoc = float(ct.thuoc.DonGia)
#             thanh_tien = don_gia_thuoc * ct.SoLuong
#             tong_tien_thuoc += thanh_tien
#
#     vat, tong_tien = 0,0
#     vat = (tong_tien_thuoc + tong_tien_dv) * 0.1
#     tong_tien = tong_tien_dv + tong_tien_thuoc + vat
#
#     return {
#         "success": True,
#         "ho_ten": ten_benh_nhan,
#         "tien_kham": tong_tien_dv,
#         "tien_thuoc": tong_tien_thuoc,
#         "vat": vat,
#         "tong_tien": tong_tien
#     }


# def add_dental_bill(ma_pdt, pttt, ma_nhan_vien, ghi_chu=None):
#     # Lấy thông tin phiếu để tính toán lại (Backend phải tự tính, không tin tưởng số liệu từ Frontend gửi về)
#     pdt = PhieuDieuTri.query.get(ma_pdt)
#     if not pdt:
#         return False
#
#     # Tính tiền dịch vụ
#     tong_tien_dv = 0
#     for dv in pdt.dichvus:
#         tong_tien_dv += float(dv.DonGia)
#
#     # Tính tiền thuốc
#     tong_tien_thuoc = 0
#     if pdt.donthuoc:
#         for ct in pdt.donthuoc.chitiet:
#             tong_tien_thuoc += float(ct.thuoc.DonGia) * ct.SoLuong
#
#     # Tính VAT (10%)
#     # Lưu ý: Trong models.py bạn khai báo VAT là Numeric(tiền), không phải %
#     vat = (tong_tien_dv + tong_tien_thuoc) * 0.1
#
#     # Tạo đối tượng Hóa Đơn
#     hd = HoaDon(
#         MaPDT=ma_pdt,
#         MaBenhNhan=pdt.MaBenhNhan,  # Lấy mã bệnh nhân từ phiếu điều trị
#         NgayLap=date.today(),
#         TongTienDV=tong_tien_dv,
#         TongTienThuoc=tong_tien_thuoc,
#         VAT=vat,
#         PTTT=pttt,  # Phương thức thanh toán (Tiền mặt/Chuyển khoản)
#         TrangThai="DaThanhToan",
#         MaNhanVien = ma_nhan_vien
#     )
#
#     try:
#         db.session.add(hd)
#         db.session.commit()
#         return True
#     except Exception as ex:
#         print(f"Lỗi lưu hóa đơn: {str(ex)}")
#         db.session.rollback()
#         return False


def complete_payment(obj):
    # 1. Tìm hóa đơn
    hd = HoaDon.query.get(obj['MaHD'])

    # 2. Kiểm tra tồn tại
    if not hd:
        print(f"Lỗi: Không tìm thấy hóa đơn có ID {obj['MaHD']}")
        return False

    # 3. (Tùy chọn) Kiểm tra xem đã thanh toán chưa để tránh trùng lặp
    # Giả sử enum TrangThaiThanhToan.Da_Thanh_Toan so sánh được
    if hd.TrangThai == TrangThaiThanhToan.Da_Thanh_Toan:
        print("Lỗi: Hóa đơn này đã được thanh toán trước đó.")
        return False

    try:
        # 4. Cập nhật thông tin
        hd.PTTT = obj['PTTT']
        hd.MaNhanVien = obj['MaNhanVien']

        # Cập nhật trạng thái
        hd.TrangThai = TrangThaiThanhToan.Da_Thanh_Toan

        # QUAN TRỌNG: Cập nhật ngày giờ thanh toán thực tế
        hd.NgayThanhToan = datetime.now()

        # 6. Lưu vào DB
        db.session.commit()
        return True

    except Exception as ex:
        # 6. Xử lý lỗi
        db.session.rollback()
        print(f"Lỗi hệ thống khi thanh toán: {ex}")
        return False


if __name__ == "__main__":

    with app.app_context():
        # datetime.now().date()

        print(load_invoice(9))
