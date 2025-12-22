from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user
from models import UserRole  # Import Enum vai trò của bạn


def dentist_required(f):
    @wraps(f)
    def decorated_func(*args, **kwargs):
        # 1. Kiểm tra xem user có phải Nha Sĩ không?
        if current_user.VaiTro != UserRole.NhaSi:
            return redirect(url_for('index'))
        return f(*args, **kwargs)

    return decorated_func


def staff_required(f):
    @wraps(f)
    def decorated_func(*args, **kwargs):
        if current_user.VaiTro != UserRole.NhanVien:
            return redirect(url_for('index'))
        return f(*args, **kwargs)

    return decorated_func

def booking_required(f):
    @wraps(f)
    def decorated_func(*args, **kwargs):
        if current_user.VaiTro != UserRole.NhanVien and current_user.VaiTro != UserRole.BenhNhan:
            return redirect(url_for('index'))
        return f(*args, **kwargs)

    return decorated_func