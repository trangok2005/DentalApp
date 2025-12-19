from DentalApp import app, db
from models import NguoiDung, BenhNhan, NhaSi, DichVu, Thuoc, PhieuDieuTri, DonThuoc, ChiTietDonThuoc, UserRole
from datetime import date
import hashlib


def create_data():
    with app.app_context():
        print(">>> Đang xóa dữ liệu cũ (nếu muốn sạch sẽ)...")
        # db.drop_all() # Cẩn thận: Dòng này sẽ xóa sạch database cũ
        # db.create_all() # Tạo lại bảng

        print(">>> Đang tạo dữ liệu mẫu...")

        # 1. Tạo Bác sĩ & Bệnh nhân (Nếu chưa có)
        # Lưu ý: Mật khẩu demo là '123'
        hashed_password = hashlib.md5('123'.encode()).hexdigest()

        # Bác sĩ
        ns1 = NhaSi.query.filter_by(TaiKhoan='bacsi01').first()
        if not ns1:
            ns1 = NhaSi(
                HoTen="BS. Lê Văn A",
                TaiKhoan="bacsi01",
                MatKhau=hashed_password,
                VaiTro=UserRole.NhaSi,
                ChuyenMon="Chỉnh nha"
            )
            db.session.add(ns1)
            db.session.flush()  # Flush để lấy ID ngay

        # Bệnh nhân 1
        bn1 = BenhNhan.query.filter_by(TaiKhoan='benhnhan01').first()
        if not bn1:
            bn1 = BenhNhan(
                HoTen="Nguyễn Thị Khách Hàng",
                TaiKhoan="benhnhan01",
                MatKhau=hashed_password,
                VaiTro=UserRole.BenhNhan,
                SDT="0909111222",
                NgaySinh=date(1995, 5, 20),
                DiaChi="TP.HCM"
            )
            db.session.add(bn1)
            db.session.flush()

        # Bệnh nhân 2
        bn2 = BenhNhan.query.filter_by(TaiKhoan='benhnhan02').first()
        if not bn2:
            bn2 = BenhNhan(
                HoTen="Trần Văn Mới",
                TaiKhoan="benhnhan02",
                MatKhau=hashed_password,
                VaiTro=UserRole.BenhNhan,
                SDT="0909333444",
                NgaySinh=date(2000, 1, 1),
                DiaChi="Hà Nội"
            )
            db.session.add(bn2)
            db.session.flush()

        # 2. Tạo Dịch vụ
        dv1 = DichVu(TenDV="Cạo vôi răng", DonGia=200000, MoTa="Làm sạch mảng bám")
        dv2 = DichVu(TenDV="Trám răng Composite", DonGia=500000, MoTa="Trám thẩm mỹ")
        dv3 = DichVu(TenDV="Nhổ răng khôn (Tiểu phẫu)", DonGia=1500000, MoTa="Gây tê, nhổ răng 8")

        db.session.add_all([dv1, dv2, dv3])
        db.session.flush()

        # 3. Tạo Thuốc
        thuoc1 = Thuoc(TenThuoc="Panadol Extra", DonViTinh="Viên", DonGia=2000, SoLuongTonKho=1000,
                       LieuDung="Uống sau ăn")
        thuoc2 = Thuoc(TenThuoc="Amoxicillin 500mg", DonViTinh="Viên", DonGia=5000, SoLuongTonKho=500,
                       LieuDung="Kháng sinh")
        thuoc3 = Thuoc(TenThuoc="Nước súc miệng Kin", DonViTinh="Chai", DonGia=120000, SoLuongTonKho=50,
                       LieuDung="Súc miệng 2 lần/ngày")

        db.session.add_all([thuoc1, thuoc2, thuoc3])
        db.session.flush()

        # 4. Tạo Phiếu Điều Trị (QUAN TRỌNG: Đây là dữ liệu sẽ hiện lên form Hóa đơn)

        # --- Phiếu số 1: Vừa trám răng, vừa lấy thuốc ---
        # (Nguyễn Thị Khách Hàng - Cạo vôi + Trám răng + Panadol)
        pdt1 = PhieuDieuTri(
            NgayLap=date.today(),
            ChuanDoan="Sâu răng nhẹ, vôi răng nhiều",
            MaBenhNhan=bn1.MaNguoiDung,
            MaNhaSi=ns1.MaNguoiDung
            # Chưa có HoaDon -> Mặc định chưa thanh toán
        )
        db.session.add(pdt1)
        db.session.flush()

        # Thêm dịch vụ vào phiếu
        pdt1.dichvus.append(dv1)  # Cạo vôi (200k)
        pdt1.dichvus.append(dv2)  # Trám răng (500k)

        # Thêm đơn thuốc
        dt1 = DonThuoc(MaPDT=pdt1.MaPDT, NgayKeDon=date.today())
        db.session.add(dt1)
        db.session.flush()

        ct1 = ChiTietDonThuoc(MaDT=dt1.MaDT, MaThuoc=thuoc1.MaThuoc, SoLuong=10,
                              LieuDung="Sáng 1 viên, Chiều 1 viên")  # 10 viên * 2k = 20k
        db.session.add(ct1)

        # --- Phiếu số 2: Chỉ nhổ răng, không thuốc ---
        # (Trần Văn Mới - Nhổ răng khôn)
        pdt2 = PhieuDieuTri(
            NgayLap=date.today(),
            ChuanDoan="Răng 38 mọc lệch",
            MaBenhNhan=bn2.MaNguoiDung,
            MaNhaSi=ns1.MaNguoiDung
        )
        db.session.add(pdt2)
        db.session.flush()

        pdt2.dichvus.append(dv3)  # Nhổ răng (1tr5)

        # Lưu tất cả vào Database
        db.session.commit()
        print(">>> Đã tạo xong dữ liệu giả thành công!")
        print(f"Phiếu 1 (Có thuốc): Mã PDT {pdt1.MaPDT} - Bệnh nhân: {bn1.HoTen}")
        print(f"Phiếu 2 (Không thuốc): Mã PDT {pdt2.MaPDT} - Bệnh nhân: {bn2.HoTen}")


if __name__ == "__main__":
    create_data()