const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
tooltipTriggerList.forEach(item => {
    new bootstrap.Tooltip(item)
})

/**
 * Hàm hiển thị thông báo SweetAlert2 đơn giản và đẹp.
 * @param {string} title - Tiêu đề của hộp thoại.
 * @param {string} text - Nội dung mô tả của hộp thoại.
 * @param {('success'|'error'|'warning'|'info'|'question')} icon - Loại biểu tượng.
 * @param {boolean} [isConfirm=false] - Nếu true, sẽ hiển thị nút Hủy bỏ (Cancel) để xác nhận.
 * @returns {Promise<SweetAlertResult>} Trả về Promise chứa kết quả tương tác của người dùng.
 */
export function showSimpleAlert({ title, text, icon, isConfirm = false }) {

    // Cấu hình cơ bản và chung (giúp alert trông đẹp hơn)
    const baseOptions = {
        title: title || "Thông báo", // Giá trị mặc định nếu title bị bỏ trống
        text: text,
        icon: icon,

        // Thiết lập UI đẹp
        showCancelButton: isConfirm, // Chỉ hiển thị nút Cancel nếu là Confirm
        confirmButtonText: isConfirm ? "Xác nhận" : "Đóng",
        cancelButtonText: "Hủy bỏ",

        // Màu nút mặc định (có thể tùy chỉnh thêm nếu muốn)
        confirmButtonColor: icon === 'error' ? '#d33' : '#3085d6',
        cancelButtonColor: '#aaa',

        allowOutsideClick: false,
        allowEscapeKey: true,
    };

    // Nếu không phải là xác nhận, đặt hẹn giờ tự đóng
    if (!isConfirm) {
        baseOptions.timer = 3000;
        baseOptions.timerProgressBar = true;
    }

    return Swal.fire(baseOptions);
}


// --- Hàm tiện ích  ---
export const Alert = {
    /** Hiển thị thông báo thành công (có tự đóng) */
    success: (title, text) => showSimpleAlert({ title, text, icon: 'success' }),

    /** Hiển thị thông báo lỗi (có tự đóng) */
    error: (title, text) => showSimpleAlert({ title, text, icon: 'error' }),

    /** Hiển thị cảnh báo (có tự đóng) */
    warning: (title, text) => showSimpleAlert({ title, text, icon: 'warning' }),

    /** Hiển thị thông tin (có tự đóng) */
    info: (title, text) => showSimpleAlert({ title, text, icon: 'info' }),

    /** Dùng để xác nhận (Có nút Cancel, không tự đóng) */
    confirm: (title, text) => showSimpleAlert({ title, text, icon: 'question', isConfirm: true }),
};

export async function showAlert(info1, info2) {

    // Gọi hàm xác nhận
    const result = await Alert.confirm(
        info1, info2
    );

    // Kiểm tra kết quả
    if (result.isConfirmed) {
        return true;
    }
    else return false;
}