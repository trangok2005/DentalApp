// Đảm bảo DOM đã load xong mới gắn sự kiện
document.getElementById('btn-pay-bill').addEventListener('click', async () {

    // 2. Lấy dữ liệu và Validate
    const maHD = document.querySelector('input[name="ma_hd"]').value;
    const ptttElem = document.querySelector('select[name="payment_method"]');
    const pttt = ptttElem ? ptttElem.value : null;

    // 3. Xác nhận trước khi gửi
    if (!confirm('Xác nhận thanh toán hóa đơn này?')) return;

    // 4. UX: Khóa nút để tránh bấm nhiều lần
    const originalText = btnPay.innerHTML;
    btnPay.disabled = true;
    btnPay.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang xử lý...';

    try {
        // 5. Gửi Request
        const res = await fetch('/api/pay', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                'MaHD': maHD,
                'PTTT': pttt
            })
        });

        // 6. Nhận phản hồi
        const result = await res.json();

        if (res.ok && result.success) {
            alert(result.message);
            // Reload trang hoặc chuyển hướng sau khi thành công
            window.location.href = "{{ url_for('reception_dashboard') }}";
        } else {
            alert('Thất bại: ' + result.message);
            // Mở lại nút nếu lỗi logic (ví dụ: đã thanh toán rồi)
            btnPay.disabled = false;
            btnPay.innerHTML = originalText;
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Lỗi kết nối đến máy chủ. Vui lòng thử lại.');

        // Mở lại nút nếu lỗi mạng
        btnPay.disabled = false;
        btnPay.innerHTML = originalText;
    }
});