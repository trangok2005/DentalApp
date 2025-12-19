function autoFillData() {
        // 1. Lấy Mã PDT người dùng chọn
        const select = document.getElementById('selectPhieuDieuTri');
        const maPDT = select.value;

        // Nếu chưa chọn gì thì reset form
        if (!maPDT) {
            resetForm();
            return;
        }

        // 2. Gọi API Flask
        fetch('/api/get-dental-bill-info/' + maPDT)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // 3. Format tiền tệ Việt Nam (VD: 500,000 đ)
                    const fmt = new Intl.NumberFormat('vi-VN');

                    // 4. Điền dữ liệu vào các ô input
                    document.getElementById('tenBenhNhan').value = data.ho_ten;
                    document.getElementById('tienKham').value = fmt.format(data.tien_kham);
                    document.getElementById('tienThuoc').value = fmt.format(data.tien_thuoc);
                    document.getElementById('thueVAT').value = fmt.format(data.vat);
                    document.getElementById('tongTien').value = fmt.format(data.tong_tien);
                } else {
                    alert('Lỗi: ' + (data.message || 'Không thể lấy dữ liệu'));
                    resetForm();
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Đã xảy ra lỗi kết nối server!');
            });
    }

    function resetForm() {
        document.getElementById('tenBenhNhan').value = '';
        document.getElementById('tienKham').value = '';
        document.getElementById('tienThuoc').value = '';
        document.getElementById('thueVAT').value = '';
        document.getElementById('tongTien').value = '';
    }

    // Hàm xử lý thanh toán
    function submitDentalBill() {
        // 1. Lấy dữ liệu từ giao diện
        const maPDT = document.getElementById('selectPhieuDieuTri').value;
        const ghiChu = document.getElementById('ghiChu').value;

        // Lấy phương thức thanh toán (Radio button)
        let pttt = 'TienMat';
        if (document.getElementById('banking').checked) {
            pttt = 'ChuyenKhoan';
        }

        // Kiểm tra hợp lệ
        if (!maPDT) {
            alert("Vui lòng chọn phiếu điều trị!");
            return;
        }

        // Hỏi xác nhận lần cuối
        if (!confirm("Bạn có chắc chắn muốn tạo hóa đơn và xác nhận thanh toán?")) {
            return;
        }

        // 2. Gửi dữ liệu về Server (Python)
        fetch('/api/pay', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                'maPDT': maPDT,
                'paymentMethod': pttt,
                'ghiChu': ghiChu
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert("Thành công: " + data.message);
                // Load lại trang để phiếu vừa thanh toán biến mất khỏi danh sách
                location.reload();
            } else {
                alert("Thất bại: " + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert("Lỗi kết nối server!");
        });
    }