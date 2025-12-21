//document.addEventListener('DOMContentLoaded', function() {
//    const btnPay = document.getElementById('btn-pay-bill');
//
//    if (btnPay) {
//        // Sửa lỗi cú pháp async () =>
//        btnPay.addEventListener('click', async () => {
//
//            // 1. Lấy dữ liệu
//            const maHDInput = document.getElementById('ma_hd');
//            const ptttSelect = document.getElementById('payment_method');
//
//            if (!maHDInput || !ptttSelect) {
//                alert("Lỗi: Không tìm thấy thông tin hóa đơn.");
//                return;
//            }
//
//            const maHD = maHDInput.value;
//            const pttt = ptttSelect.value;
//
//            // 2. Xác nhận
//            if (!confirm('Xác nhận thanh toán hóa đơn này?')) return;
//
//            try {
//                // 4. Gửi Request
//                const res = await fetch('/api-pay', {
//                    method: 'POST',
//                    headers: {
//                        'Content-Type': 'application/json'
//                    },
//                    body: JSON.stringify({
//                        'MaHD': maHD,
//                        'PTTT': pttt
//                    })
//                });
//
////                // 5. Nhận kết quả
////                const result = await res.json();
////
////                if (res.ok && result.success) {
////                    alert(result.message);
////                    // Chuyển hướng về Dashboard
////                    window.location.href = "/cancel-appointment";
////                } else {
////                    alert('Thất bại: ' + result.message);
////                    // Mở lại nút
////                    btnPay.disabled = false;
////                    btnPay.innerHTML = originalText;
////                }
//
//
//        });
//    }
//});