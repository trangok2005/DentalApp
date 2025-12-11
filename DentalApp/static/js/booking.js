
    const dentistSelect = document.getElementById('dentistSelect');
    const dateInput = document.getElementById('dateInput');
    const slotsTableBody = document.getElementById('slotsTableBody');
    const displayDate = document.getElementById('displayDate');
    const statusText = document.getElementById('statusText');
    const selectedTimeInput = document.getElementById('selectedTime');

    // Hàm load danh sách giờ (STT 2, 3, 4, 5)
    async function loadSlots() {
        const dentist = dentistSelect.value;
        const date = dateInput.value;

        // Hiển thị ngày lên giao diện phải
        const [y, m, d] = date.split('-');
        displayDate.innerText = `${d}/${m}/${y}`;

        const response = await fetch('/api/get-slots', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ dentist, date })
        });

        const data = await response.json();

        // Xóa bảng cũ
        slotsTableBody.innerHTML = '';
        selectedTimeInput.value = ''; // Reset ô giờ chọn

        if (data.status === 'full') {
            statusText.innerText = `${data.booked_count}/5 ca đã đặt (Full)`;
            statusText.className = 'text-danger fw-bold';
            slotsTableBody.innerHTML = `<tr><td colspan="3" class="text-danger text-center">${data.message}</td></tr>`;
            return;
        }

        // Cập nhật trạng thái text
        statusText.innerText = `${data.booked_count}/5 ca đã đặt`;
        statusText.className = 'text-dark';

        // STT 5: Render Grid
        data.slots.forEach((slot, index) => {
            const tr = document.createElement('tr');

            // Xử lý class nếu đã đặt
            if (slot.status === 'Đã đặt') {
                tr.className = 'slot-booked';
            } else {
                // STT 6: Sự kiện Click chọn giờ
                tr.onclick = function() {
                    // Remove highlight cũ
                    document.querySelectorAll('.slot-row-selected').forEach(row => row.classList.remove('slot-row-selected'));
                    // Add highlight mới
                    tr.classList.add('slot-row-selected');
                    // Điền vào ô input bên trái
                    selectedTimeInput.value = slot.time;
                };
            }

            tr.innerHTML = `
                <td>${index + 1}</td>
                <td>[${slot.time}]</td>
                <td>${slot.status}</td>
            `;
            slotsTableBody.appendChild(tr);
        });
    }

    // Sự kiện thay đổi Nha sĩ hoặc Ngày
    dentistSelect.addEventListener('change', loadSlots);
    dateInput.addEventListener('change', loadSlots);

    // STT 8: Xử lý nút Xác nhận
    document.getElementById('btnConfirm').addEventListener('click', async () => {
        const time = selectedTimeInput.value;
        const name = document.getElementById('patientName').value;
        const phone = document.getElementById('patientPhone').value;
        const note = document.getElementById('ghiChu').value;

        if (!time || !name || !phone || !service) {
            alert('Vui lòng điền đầy đủ thông tin và chọn giờ khám!');
            return;
        }

        const payload = {
            dentist: dentistSelect.value,
            date: dateInput.value,
            time: time,
            name: name,
            phone: phone,
            service: service
        };

        const res = await fetch('/api/book', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });

        const result = await res.json();
        alert(result.message);
        if (result.success) {
            loadSlots(); // Reload lại bảng
            document.getElementById('bookingForm').reset();//  reset form nhập liệu
            dateInput.value = new Date().toISOString().split('T')[0];
        }
    });

    // STT 9: Nút Hủy (Reset form)
    document.getElementById('btnCancel').addEventListener('click', () => {
        document.getElementById('bookingForm').reset();
        // Reset lại ngày về hôm nay vì form reset sẽ xóa hết
        dateInput.value = new Date().toISOString().split('T')[0];
        loadSlots();
    });

    // Load lần đầu khi chạy trang (STT 1)
    loadSlots();
