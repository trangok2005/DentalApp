from datetime import date, time


from DentalApp import db, app, VAT
from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, Enum, Numeric, Time, func, DateTime
from sqlalchemy.orm import relationship, backref
import enum
from flask_login import UserMixin
import json

class UserRole(enum.Enum):
    QuanLy = "Manager"   # Tách Quản lý thành Role riêng
    NhaSi = "Dentist"
    BenhNhan = "Patient"
    NhanVien = "Staff"

class TrangThaiLichHen(enum.Enum):

    CHO_KHAM = "Chờ Khám"
    DA_KHAM = "Đã Khám" # Bác sĩ đã khám xong -> Chờ thanh toán
    HUY = "Hủy"

    def __str__(self):
        return self.value

class TrangThaiThanhToan(enum.Enum):
    Da_Thanh_Toan = "DaThanhToan"
    Chua_Thanh_Toan = "ChuaThanhToan"


# --- Bảng Người Dùng (Base) ---
class NguoiDung(db.Model, UserMixin):
    __tablename__ = 'nguoidung'

    MaNguoiDung = Column(Integer, primary_key=True, autoincrement=True)
    HoTen = Column(String(100), nullable=False)
    TaiKhoan = Column(String(50), unique=True, nullable=False)
    MatKhau = Column(String(255), nullable=False)
    VaiTro = Column(Enum(UserRole), nullable=False, default=UserRole.BenhNhan)

    # Thiết lập đa hình (Polymorphism) để SQLAlchemy tự nhận diện loại class
    __mapper_args__ = {
        'polymorphic_on': VaiTro,
    }

    def __str__(self):
        return self.HoTen
    #flask-login sài
    def get_id(self):
        return str(self.MaNguoiDung)


# --- Các Class Kế Thừa ---
class BenhNhan(NguoiDung):
    __tablename__ = 'benhnhan'
    MaNguoiDung = Column(Integer, ForeignKey('nguoidung.MaNguoiDung'), primary_key=True)
    SDT = Column(String(15), unique=True, nullable=False)
    NgaySinh = Column(Date)
    DiaChi = Column(Text)
    TienSuBenh = Column(Text)

    __mapper_args__ = {
        'polymorphic_identity': UserRole.BenhNhan,
    }

    # Relationships
    hoadons = relationship("HoaDon", backref="benhnhan", lazy=True)
    phieudieutris = relationship("PhieuDieuTri", backref="benhnhan", lazy=True)
    lichhens = relationship("LichHen", backref="benhnhan", lazy=True)


class NhaSi(NguoiDung):
    __tablename__ = 'nhasi'
    MaNguoiDung = Column(Integer, ForeignKey('nguoidung.MaNguoiDung'), primary_key=True)
    ChuyenMon = Column(Text)

    __mapper_args__ = {
        'polymorphic_identity': UserRole.NhaSi,
    }

    # Relationships
    phieudieutris = relationship("PhieuDieuTri", backref="nhasi", lazy=True)
    lichhens = relationship("LichHen", backref="nhasi", lazy=True)


class NhanVien(NguoiDung):
    __tablename__ = 'nhanvien'
    MaNguoiDung = Column(Integer, ForeignKey('nguoidung.MaNguoiDung'), primary_key=True)
    TrinhDo = Column(Text)

    hoadons = relationship("HoaDon", backref="nhanvien", lazy=True)

    __mapper_args__ = {
        'polymorphic_identity': UserRole.NhanVien,
    }

class QuanLy(NguoiDung):
    __tablename__ = 'quanly'
    MaNguoiDung = Column(Integer, ForeignKey('nguoidung.MaNguoiDung'), primary_key=True)
    SoNamKinhNghiem =Column(Integer)

    __mapper_args__ = {
        'polymorphic_identity': UserRole.QuanLy,
    }

# --- Lịch Hẹn ---
class LichHen(db.Model):
    __tablename__ = 'lichhen'
    MaLH = Column(Integer, primary_key=True, autoincrement=True)
    NgayKham = Column(Date, nullable=False)
    GioKham = Column(Time, nullable=False)  # Dùng kiểu Time thay vì Integer
    TrangThai = Column(Enum(TrangThaiLichHen), default=TrangThaiLichHen.CHO_KHAM)  # Mặc định trạng thái
    GhiChu = Column(Text)

    MaNhaSi = Column(Integer, ForeignKey('nhasi.MaNguoiDung'))
    MaBenhNhan = Column(Integer, ForeignKey('benhnhan.MaNguoiDung'))

    @property
    def thong_tin_hoa_don(self):
        """
        Hàm helper để tìm Hóa đơn tương ứng với lịch hẹn này.
        Logic: Tìm Phiếu điều trị của Bệnh nhân này vào Ngày khám này.
        """
        # Import cục bộ để tránh lỗi circular import
        from models import PhieuDieuTri, HoaDon

        # 1. Tìm phiếu điều trị khớp User và Ngày
        pdt = PhieuDieuTri.query.filter_by(
            MaBenhNhan=self.MaBenhNhan,
            NgayLap=self.NgayKham
        ).first()

        # 2. Nếu có phiếu, trả về hóa đơn (nếu có)
        if pdt and pdt.hoadon:
            return pdt.hoadon

        return None

class PhieuDieuTri(db.Model):
    __tablename__ = 'phieudieutri'

    MaPDT = Column(Integer, primary_key=True, autoincrement=True)
    NgayLap = Column(Date, default=func.now())  # Lấy ngày hiện tại phía DB
    ChuanDoan = Column(Text)

    MaBenhNhan = Column(Integer, ForeignKey('benhnhan.MaNguoiDung'), nullable=False)
    MaNhaSi = Column(Integer, ForeignKey('nhasi.MaNguoiDung'), nullable=False)

    # Quan hệ Many-to-Many với DichVu
    dichvus = relationship("DichVu", secondary="phieudieutri_dichvu", backref="phieudieutris", lazy="subquery")

    # Quan hệ 1-1
    donthuoc = relationship("DonThuoc", backref="phieudieutri", uselist=False, lazy=True)
    hoadon = relationship("HoaDon", backref="phieudieutri", uselist=False, lazy=True)

class DichVu(db.Model):
    __tablename__ = 'dichvu'
    MaDV = Column(Integer, primary_key=True, autoincrement=True)
    TenDV = Column(String(500), nullable=False)
    # Dùng Numeric cho tiền tệ để tránh sai số Float
    DonGia = Column(Numeric(10, 0), nullable=False)
    MoTa = Column(Text)

    def __str__(self):
        return self.TenDV

class PhieuDieuTriDichVu(db.Model):
    __tablename__ = 'phieudieutri_dichvu'
    MaPDT = Column(Integer, ForeignKey('phieudieutri.MaPDT'), primary_key=True)
    MaDV = Column(Integer, ForeignKey('dichvu.MaDV'), primary_key=True)

class Thuoc(db.Model):
    __tablename__ = 'thuoc'
    MaThuoc = Column(Integer, primary_key=True, autoincrement=True)
    TenThuoc = Column(String(255), nullable=False)
    DonViTinh = Column(String(50), nullable=False)
    DonGia = Column(Numeric(10, 0), nullable=False)
    SoLuongTonKho = Column(Integer, default=0)
    HanSuDung = Column(Date)
    LieuDung = Column(Text)  # Hướng dẫn chung

    def __str__(self):
        return self.TenThuoc

class DonThuoc(db.Model):
    __tablename__ = 'donthuoc'
    MaDT = Column(Integer, primary_key=True, autoincrement=True)
    NgayKeDon = Column(Date, default=func.now())
    MaPDT = Column(Integer, ForeignKey('phieudieutri.MaPDT'), unique=True, nullable=False)

    # Quan hệ tới bảng chi tiết
    chitiet = relationship("ChiTietDonThuoc", backref="donthuoc", lazy=True, cascade="all, delete-orphan")


class ChiTietDonThuoc(db.Model):
    __tablename__ = 'chitietdonthuoc'

    MaDT = Column(Integer, ForeignKey('donthuoc.MaDT'), primary_key=True)
    MaThuoc = Column(Integer, ForeignKey('thuoc.MaThuoc'), primary_key=True)
    SoLuong = Column(Integer, nullable=False)
    LieuDung = Column(Text)  # Hướng dẫn cụ thể cho bệnh nhân này

    # Relationship để truy cập ngược lại thông tin thuốc từ chi tiết
    thuoc = relationship("Thuoc")


# --- Hóa Đơn ---
class HoaDon(db.Model):
    __tablename__ = 'hoadon'

    MaHD = Column(Integer, primary_key=True, autoincrement=True)
    NgayLap = Column(Date, default=func.now())
    # Numeric tốt hơn Float cho tiền
    TongTienDV = Column(Numeric(12, 0), default=0)
    TongTienThuoc = Column(Numeric(12, 0), default=0)
    # VAT có thể là Float vì là % nhưng tiền phải là Numeric. Ở đây để đơn giản lưu tiền VAT
    VAT = Column(Numeric(12, 0), default=VAT)
    PTTT = Column(String(50))  # Phương thức thanh toán
    TrangThai = Column(String(50), default=TrangThaiThanhToan.Chua_Thanh_Toan)
    NgayThanhToan = Column(DateTime)

    MaBenhNhan = Column(Integer, ForeignKey('benhnhan.MaNguoiDung'))
    MaPDT = Column(Integer, ForeignKey('phieudieutri.MaPDT'), unique=True)
    MaNhanVien = Column(Integer, ForeignKey('nhanvien.MaNguoiDung'))
#
if __name__ == "__main__":
    with app.app_context():

        db.create_all()
        # bn1 =BenhNhan(
        #     HoTen="Nguyễn Văn A",
        #     SDT="0909123456",
        #     TaiKhoan="tvt",
        #     MatKhau="6512bd43d9caa6e02c990b0a82652dca",#123
        #     NgaySinh=date(1990, 5, 15),
        #     DiaChi="123 Lê Lợi, Q1, TP.HCM",
        #     TienSuBenh="Dị ứng thuốc tê nhẹ"
        # )
        # lt1 = NhanVien(
        #     HoTen="Lê Thị Hạnh",
        #     TaiKhoan="letan01",
        #     MatKhau="6512bd43d9caa6e02c990b0a82652dca",
        # )
        #
        #
        # db.session.add_all([bn1,lt1])
        # db.session.commit()
        #
        # with open("data/NhaSi.json", encoding="utf-8") as f:
        #     dentists = json.load(f)
        #
        #     for d in dentists:
        #         den = NhaSi(**d)
        #         db.session.add(den)
        #
        # db.session.commit()
        #
        #
        # with open("data/LichKham.json", encoding="utf-8") as f:
        #     appointments = json.load(f)
        #
        #     for item in appointments:
        #         appt = LichHen(**item)
        #         db.session.add(appt)
        #
        # db.session.commit()
        #
        # with open("data/DichVu.json", encoding="utf-8") as f:
        #     services = json.load(f)
        #
        #     for s in services:
        #         ser = DichVu(**s)
        #         db.session.add(ser)
        #
        # db.session.commit()
        #
        # with open("data/Thuoc.json", encoding="utf-8") as f:
        #     medicines = json.load(f)
        #
        #     for m in medicines:
        #         me = Thuoc(**m)
        #         db.session.add(me)
        #
        # db.session.commit()


