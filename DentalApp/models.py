from datetime import date, time
from DentalApp import db, app
from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, Enum, Numeric, Time, func
from sqlalchemy.orm import relationship, backref
import enum

class UserRole(enum.Enum):
    BenhNhan = 1
    NhaSi = 2
    NhanVien = 3

class BoPhanEnum(enum.Enum):
    LeTan = 1
    ThuNgan = 2
    QuanLy = 3

# --- Bảng Người Dùng (Base) ---
class NguoiDung(db.Model):
    __tablename__ = 'nguoidung'

    MaNguoiDung = Column(Integer, primary_key=True, autoincrement=True)
    HoTen = Column(String(100), nullable=False)
    SDT = Column(String(15), unique=True, nullable=False)  # SDT nên là duy nhất
    TaiKhoan = Column(String(50), unique=True, nullable=False)
    MatKhau = Column(String(255), nullable=False)
    VaiTro = Column(Enum(UserRole), nullable=False)

    # Thiết lập đa hình (Polymorphism) để SQLAlchemy tự nhận diện loại class
    __mapper_args__ = {
        'polymorphic_on': VaiTro,
    }


# --- Các Class Kế Thừa ---
class BenhNhan(NguoiDung):
    __tablename__ = 'benhnhan'
    MaNguoiDung = Column(Integer, ForeignKey('nguoidung.MaNguoiDung'), primary_key=True)
    NgaySinh = Column(Date, nullable=False)
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
    BoPhan = Column(Enum(BoPhanEnum), nullable=False, default=BoPhanEnum.LeTan)

    __mapper_args__ = {
        'polymorphic_identity': UserRole.NhanVien,
    }


# --- Dịch Vụ & Phiếu Điều Trị ---

# Bảng trung gian cho quan hệ n-n giữa PhieuDieuTri và DichVu
# Dùng Model thay vì Table thuần để dễ mở rộng sau này (ví dụ thêm số lượng dịch vụ)
class PhieuDieuTriDichVu(db.Model):
    __tablename__ = 'phieudieutri_dichvu'
    MaPDT = Column(Integer, ForeignKey('phieudieutri.MaPDT'), primary_key=True)
    MaDV = Column(Integer, ForeignKey('dichvu.MaDV'), primary_key=True)


class DichVu(db.Model):
    __tablename__ = 'dichvu'
    MaDV = Column(Integer, primary_key=True, autoincrement=True)
    TenDV = Column(String(255), nullable=False)
    # Dùng Numeric cho tiền tệ để tránh sai số Float
    DonGia = Column(Numeric(10, 0), nullable=False)
    MoTa = Column(Text)


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


# --- Lịch Hẹn ---
class LichHen(db.Model):
    __tablename__ = 'lichhen'
    MaLH = Column(Integer, primary_key=True, autoincrement=True)
    NgayKham = Column(Date, nullable=False)
    GioKham = Column(Time, nullable=False)  # Dùng kiểu Time thay vì Integer
    TrangThai = Column(String(50), default="ChoKham")  # Mặc định trạng thái
    GhiChu = Column(Text)

    MaNhaSi = Column(Integer, ForeignKey('nhasi.MaNguoiDung'))
    MaBenhNhan = Column(Integer, ForeignKey('benhnhan.MaNguoiDung'))


# --- Thuốc & Đơn Thuốc ---
class Thuoc(db.Model):
    __tablename__ = 'thuoc'
    MaThuoc = Column(Integer, primary_key=True, autoincrement=True)
    TenThuoc = Column(String(255), nullable=False)  # Đã thêm trường này
    DonViTinh = Column(String(50), nullable=False)
    DonGia = Column(Numeric(10, 0), nullable=False)
    SoLuongTonKho = Column(Integer, default=0)
    HanSuDung = Column(Date)
    LieuDung = Column(Text)  # Hướng dẫn chung


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
    VAT = Column(Numeric(12, 0), default=0)
    PTTT = Column(String(50))  # Phương thức thanh toán (Momo, Cash...)
    TrangThai = Column(String(50), default="ChuaThanhToan")

    MaBenhNhan = Column(Integer, ForeignKey('benhnhan.MaNguoiDung'))
    MaPDT = Column(Integer, ForeignKey('phieudieutri.MaPDT'), unique=True)

if __name__=="__main__":
    BenhNhan()
    # with app.app_context():
    #     bn1 =BenhNhan(
    #         HoTen="Nguyễn Văn A",
    #         SDT="0909123456",
    #         TaiKhoan="tvt",
    #         MatKhau="123",  # Thực tế cần hash password
    #         NgaySinh=date(1990, 5, 15),
    #         DiaChi="123 Lê Lợi, Q1, TP.HCM",
    #         TienSuBenh="Dị ứng thuốc tê nhẹ"
    #     )
    #     db.session.add(bn1)
    #     db.session.commit()
        #db.create_all()