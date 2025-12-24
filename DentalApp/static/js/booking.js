const dentistSelect = document.getElementById('dentistSelect');
const dateInput = document.getElementById('dateInput');
const slotsTableBody = document.getElementById('slotsTableBody');
const displayDate = document.getElementById('displayDate');
const statusText = document.getElementById('statusText');
const selectedTimeInput = document.getElementById('selectedTime');

// Hàm load danh sách giờ
async function loadSlots() {
    const dentist = dentistSelect.value;
    const date = dateInput.value;

    if(!dentist || !date) return;

    //hiển thị thông tin ngày
    const [y, m, d] = date.split('-');
    displayDate.innerText = `${d}/${m}/${y}`;

    //gửi dl
    const response = await fetch('/api/get-slots', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ dentist, date })
    });

    const data = await response.json();

    //xóa bảng cũ và reset ô chọn giờ
    slotsTableBody.innerHTML = '';
    selectedTimeInput.value = '';

    if (data.status === 'full') {
        statusText.innerText = `${data.booked_count}/5 ca đã đặt (Full)`;
        statusText.className = 'text-danger fw-bold';
        slotsTableBody.innerHTML = `<tr><td colspan="3" class="text-danger text-center">${data.message}</td></tr>`;
        return;
    }

    //cập nhật trạng thái text
    statusText.innerText = `${data.booked_count}/5 ca đã đặt`;
    statusText.className = 'text-dark';

    //Vẽ bảng
    data.slots.forEach((slot, index) => {
        const tr = document.createElement('tr');

        //xử lý class nếu đã đặt
        if (slot.status === 'Đã đặt') {
            tr.className = 'slot-booked';
        } else {
            // thêm sự kiện click chọn giờ
            tr.onclick = function() {
                // xóa highlight cũ
                document.querySelectorAll('.slot-row-selected').forEach(row => row.classList.remove('slot-row-selected'));
                //thêm highlight mới
                tr.classList.add('slot-row-selected');
                //điền vào ô input bên trái
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

//ktra user đã tồn tại khi dăt lich hộ
document.getElementById('patientPhone').addEventListener('blur', async function() {
    const feedback = document.getElementById('phoneFeedback');
    //ktra quyền
    const isStaff = this.getAttribute('data-is-staff') === 'true';
    if (!isStaff) return

    //ktra số
    const phone = this.value;
    if (phone.length < 9) return;

    //gửi
    try {
        const response = await fetch('/api/find-patient', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone: phone })
        });

        const data = await response.json();
        const nameInput = document.getElementById('patientName');

        if (data.found) {
        //  them tên vào và hiện thông báo
            nameInput.value = data.name;
            feedback.style.display = 'block';
        } else {
            feedback.style.display = 'none';
        }

    } catch (err) {
        console.error(err);
    }
});

//sự kiện thay đổi Nha sĩ hoặc Ngày
dentistSelect.addEventListener('change', loadSlots);
dateInput.addEventListener('change', loadSlots);

//xử lý nút Xác nhận
document.getElementById('btnConfirm').addEventListener('click', async () => {
    const time = selectedTimeInput.value;
    const name = document.getElementById('patientName').value;
    const phone = document.getElementById('patientPhone').value.trim();
    const note = document.getElementById('patientNote').value;

    if (!time || !name || !phone || !note) {
        alert('Vui lòng điền đầy đủ thông tin và chọn giờ khám!');
        return;
    }
    //chặn sdt rác
    regex = /^0[0-9]{9}$/;
    console.log(phone, phone.length);
    if (!regex.test(phone)) {
        alert('Số điện thoại không đúng định dạng!!!');
        document.getElementById('patientPhone').focus();
        return;
    }
    //gui
    const res = await fetch('/api/book', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            dentist_id: document.getElementById('dentistSelect').value,
            date: document.getElementById('dateInput').value,
            time: selectedTimeInput.value,
            phone: document.getElementById('patientPhone').value,
            name: document.getElementById('patientName').value,
            patientNote: document.getElementById('patientNote').value
       })
    });
    //nhan
    const result = await res.json();
    alert(result.message);

    if (result.success) {
        loadSlots(); // Reload lại bảng
        document.getElementById('bookingForm').reset();//  reset form nhập liệu
        dateInput.value = new Date().toISOString().split('T')[0];
    }
});

// Nút Hủy (Reset form)
document.getElementById('btnCancel').addEventListener('click', () => {
    document.getElementById('bookingForm').reset();
    // Reset lại ngày
    dateInput.value = new Date().toISOString().split('T')[0];
    //
    slotsTableBody.innerHTML = '';

});

