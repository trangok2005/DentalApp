# --- File: admin.py ---
from flask_admin import Admin, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, logout_user
from flask import redirect, url_for, request
from models import UserRole


# 1. Class bảo vệ dữ liệu (ModelView)
# Chỉ cho phép Quản lý truy cập các bảng dữ liệu
class AuthenticatedModelView(ModelView):
    def is_accessible(self):
        # Điều kiện: Đã đăng nhập + Là Nhân viên + Bộ phận Quản lý
        return current_user.is_authenticated and \
            current_user.VaiTro == UserRole.QuanLy

    def inaccessible_callback(self, name, **kwargs):
        # Nếu không được phép thì đá về trang đăng nhập
        return redirect(url_for('login_index', next=request.url))


# 2. Class cho trang Thống kê (Custom View)
class AnalyticsView(BaseView):
    @expose('/')
    def index(self):
        # Render ra file HTML riêng của Admin
        return self.render('admin/stats.html')

    def is_accessible(self):
        return current_user.is_authenticated and \
            current_user.VaiTro == UserRole.QuanLy

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login_index'))


# 3. Class cho nút Đăng xuất trong Admin
class LogoutView(BaseView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect(url_for('index'))

    def is_accessible(self):
        return current_user.is_authenticated