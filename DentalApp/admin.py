# --- File: admin.py ---
from flask_admin import Admin, BaseView, expose, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, logout_user
from flask import redirect, url_for, request
from models import UserRole


# Chỉ cho phép Quản lý truy cập các bảng dữ liệu
class MyHomeScreen(AdminIndexView):
    @expose('/')
    def index(self):
        # Render thẳng file stats.html ra trang chủ
        return self.render('admin/stats.html')

    def is_accessible(self):
        return current_user.is_authenticated and \
            current_user.VaiTro == UserRole.QuanLy

    def inaccessible_callback(self, name, **kwargs):
        # Nếu chưa login hoặc không phải quản lý thì đá về trang Login
        return redirect(url_for('index'))

class AuthenticatedModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and \
            current_user.VaiTro == UserRole.QuanLy

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('index', next=request.url))

# View thống kê
class AnalyticsView(BaseView):
    @expose('/')
    def index(self):
        return self.render('admin/stats.html')

    def is_accessible(self):
        return current_user.is_authenticated and \
            current_user.VaiTro == UserRole.QuanLy

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('index'))

# Các modelview

class ThuocModelView(AuthenticatedModelView):
    column_list = ['MaThuoc', 'TenThuoc', 'DonViTinh', 'DonGia', 'SoLuongTonKho', 'HanSuDung']
    column_searchable_list = ['TenThuoc']
    # Cho phép lọc (VD: Lọc thuốc có giá > 100k, lọc tồn kho < 10)
    column_filters = ['TenThuoc', 'DonGia', 'SoLuongTonKho']
    column_editable_list = ['SoLuongTonKho', 'DonGia']
    # Dùng Modal (Popup) để sửa thay vì chuyển trang
    edit_modal = True
    create_modal = True
    page_size = 20

    column_labels = {
        'MaThuoc': 'Mã',
        'TenThuoc': 'Tên Thuốc',
        'DonViTinh': 'Đơn vị',
        'DonGia': 'Giá bán',
        'SoLuongTonKho': 'Tồn kho',
        'HanSuDung': 'Hạn dùng'
    }


# DỊCH VỤ
class DichVuModelView(AuthenticatedModelView):
    column_list = ['MaDV', 'TenDV', 'DonGia', 'MoTa']
    column_searchable_list = ['TenDV']
    column_filters = ['DonGia']
    edit_modal = True
    create_modal = True
    column_labels = dict(MaDV='Mã', TenDV='Tên Dịch Vụ', DonGia='Giá', MoTa='Mô tả')


# NHÂN VIÊN
class NhanVienModelView(AuthenticatedModelView):
    column_list = ['MaNguoiDung', 'HoTen']
    column_searchable_list = ['HoTen']
    column_labels = dict(MaNguoiDung='ID', HoTen='Họ Tên')

    can_create = True
    can_edit = False
    can_delete = False


# NHA SĨ
class NhaSiModelView(AuthenticatedModelView):
    column_list = ['MaNguoiDung', 'HoTen','ChuyenMon']
    column_searchable_list = ['HoTen','ChuyenMon']
    column_filters = ['ChuyenMon']  # Lọc theo chuyên môn (VD: Chỉnh nha, Nhổ răng)

    column_labels = {
        'MaNguoiDung': 'ID',
        'HoTen': 'Họ Tên Bác Sĩ',
        'ChuyenMon': 'Chuyên môn'
    }

    can_create = True
    can_edit = False
    can_delete = False


# BỆNH NHÂN
class BenhNhanModelView(AuthenticatedModelView):
    column_list = ['MaNguoiDung', 'HoTen', 'SDT', 'NgaySinh', 'DiaChi', 'TienSuBenh']
    column_searchable_list = ['HoTen', 'SDT']
    column_filters = ['NgaySinh', 'DiaChi']
    edit_modal = True
    create_modal = True
    column_labels = {
        'MaNguoiDung': 'ID',
        'HoTen': 'Tên Bệnh Nhân',
        'SDT': 'Số Điện Thoại',
        'NgaySinh': 'Ngày Sinh',
        'DiaChi': 'Địa Chỉ',
        'TienSuBenh': 'Tiền Sử Bệnh'
    }


# LỊCH HẸN
class LichHenModelView(AuthenticatedModelView):
    column_list = ['MaLH', 'benhnhan', 'nhasi', 'NgayKham', 'GioKham', 'TrangThai', 'GhiChu']
    column_filters = ['NgayKham', 'TrangThai', 'nhasi.HoTen']
    column_searchable_list = ['benhnhan.HoTen', 'benhnhan.SDT']
    edit_modal = True
    create_modal = True
    column_labels = {
        'MaLH': 'Mã',
        'benhnhan': 'Bệnh Nhân',
        'nhasi': 'Nha Sĩ Phụ Trách',
        'NgayKham': 'Ngày Khám',
        'GioKham': 'Giờ',
        'TrangThai': 'Trạng Thái',
        'GhiChu': 'Ghi Chú'
    }


# HÓA ĐƠN
class HoaDonModelView(AuthenticatedModelView):
    column_list = ['MaHD', 'benhnhan', 'NgayLap', 'TongTienDV', 'TongTienThuoc', 'VAT', 'PTTT', 'TrangThai']
    column_filters = ['NgayLap', 'PTTT', 'TrangThai', 'benhnhan.HoTen']
    column_searchable_list = ['benhnhan.HoTen']

    column_labels = {
        'MaHD': 'Số HĐ',
        'benhnhan': 'Khách Hàng',
        'NgayLap': 'Ngày Lập',
        'TongTienDV': 'Tiền Dịch Vụ',
        'TongTienThuoc': 'Tiền Thuốc',
        'PTTT': 'Thanh Toán',
        'TrangThai': 'Trạng Thái'
    }

    # Format tiền tệ (thêm dấu phẩy cho dễ nhìn: 500,000)
    def _format_money(view, context, model, name):
        value = getattr(model, name)
        if value is None: return "0"
        return "{:,.0f}".format(value).replace(",", ".")

    # Áp dụng format tiền cho các cột này
    column_formatters = {
        'TongTienDV': _format_money,
        'TongTienThuoc': _format_money,
        'VAT': _format_money
    }


# PHIẾU ĐIỀU TRỊ (Hồ sơ bệnh án)
class PhieuDieuTriModelView(AuthenticatedModelView):
    column_list = ['MaPDT', 'benhnhan', 'nhasi', 'NgayLap', 'ChuanDoan']
    column_filters = ['NgayLap', 'nhasi.HoTen']
    column_searchable_list = ['benhnhan.HoTen']
    can_export = True
    column_labels = {
        'MaPDT': 'Mã Phiếu',
        'benhnhan': 'Bệnh Nhân',
        'nhasi': 'Bác Sĩ',
        'NgayLap': 'Ngày Khám',
        'ChuanDoan': 'Chẩn Đoán'
    }

# Đăng xuất trong Admin
class LogoutView(BaseView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect(url_for('index'))

    def is_accessible(self):
        return current_user.is_authenticated