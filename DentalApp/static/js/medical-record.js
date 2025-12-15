// Import hàm đã được export từ app.js
import { showAlert, Alert, showSimpleAlert } from './app.js';
let currentPatientId = null;
let selectedAppointmentId= null;
let currentTotal = 0;
let selectedServiceIds = []; // Mảng chứa các ID dịch vụ đã chọn
setFormEnabled(false);
let prescriptionList = []; // Mảng chứa thuốc đã chọn
let currentSelectedMed = null; // Thuốc đang chọn tạm ở ô search
let isExamining = false;


// format tiền
function formatCurrency(n) {
    return new Intl.NumberFormat('vi-VN').format(n);
}
//disabled khi chua chon benh nhan
function setFormEnabled(enabled) {
    document.getElementById('txtDiagnosis').disabled = !enabled;
    document.getElementById('cboServices').disabled = !enabled;
}

//hiển thị ds benh nhân ơ hàng chờ
document.addEventListener('DOMContentLoaded', () => {
    reloadPatientQueue();
});

//hien thi ds chờ
async function reloadPatientQueue() {
    const container = document.getElementById('patientQueueList');
    container.innerHTML = '';

    const res = await fetch('/api/patient-queue');
    const data = await res.json();

    if (data.length === 0) {
        container.innerHTML = '<div class="text-muted">Không có bệnh nhân chờ</div>';
        return;
    }

    data.forEach((p, index) => {
        const div = document.createElement('div');
        div.className = 'queue-item';

        if (p.isLate) div.classList.add('text-danger');

        // Nếu đang được chọn thì active
        if (p.maLH === selectedAppointmentId) {
            div.classList.add('active');
        }

        div.dataset.pid = p.maBenhNhan;
        div.dataset.appt = p.maLH;

        div.innerHTML = `
            ${index + 1}. ${p.hoTen} – ${p.gioKham}
            <span class="status">
                ${p.isLate ? '[Muộn giờ]' : '[Chờ khám]'}
            </span>
        `;

        //click chọn bệnh nhân
        div.addEventListener('click', async function () {
        const pid = this.dataset.pid;
        selectedAppointmentId = this.dataset.appt;

        if (!pid) {
            alert('Không có mã bệnh nhân');
            return;
        }
        await selectPatient(pid, this);
        });

        container.appendChild(div);
    });
}

// highlight vs lay thong tin benh nhan len UI
async function selectPatient(pid, element) {
    //chặn nếu đang chọn bệnh nhân rồi
    if (isExamining) return;
    // highlight UI
    document.querySelectorAll('.queue-item').forEach(el => el.classList.remove('active'));
    element.classList.add('active');
    element.querySelector('.status').innerText = 'Đang khám';
     // Disable danh sách chờ vs đổi cờ
    isExamining = true;
    document.getElementById('patientQueueList').classList.add('queue-disabled');
     // Hiện nút hủy
    document.getElementById('btnCancelExam').classList.remove('d-none');

// alo API lấy thông tin
    try {
        const res = await fetch(`/api/patient/${pid}`);
        const data = await res.json();


        if (data.error) { alert('Không tìm thấy bệnh nhân'); return; }

        const birth = new Date(data.NgaySinh);
        const age = new Date().getFullYear() - birth.getFullYear()
                    - (new Date().getMonth() < birth.getMonth()
                    || (new Date().getMonth() === birth.getMonth()
                    && new Date().getDate() < birth.getDate()));


        // up dữ liệu lên UI vs set nguoi kham
        currentPatientId = data.MaNguoiDung;
        setFormEnabled(true)
        document.getElementById('lblPatientName').innerText = data.HoTen;
        document.getElementById('lblPatientAge').innerText = age;
        document.getElementById('lblHistory').innerText = data.TienSuBenh;

        // Hiển thị cảnh báo nếu có tiền sử bệnh
        const warnIcon = document.getElementById('iconWarning');
        if (data.TienSuBenh) {
            warnIcon.style.display = 'inline-block';
        } else {
            warnIcon.style.display = 'none';
        }

    } catch (err) {
        console.error(err);
    }
}
// huy cua lập phiếu
document.getElementById('btnCancelExam').addEventListener('click', async () => {
    const isConfirmed = await showAlert(
        "Xác nhận hủy?",
        "Dữ liệu sẽ không được lưu lại!!"
    );
    if(!isConfirmed) return;
    resetFormPartially();
});

// STT 4: Thêm dịch vụ & Tính tiền
function addService() {
    const cbo = document.getElementById('cboServices');
    const selectedOption = cbo.options[cbo.selectedIndex];

    if (cbo.value === "") return;

    const sId = cbo.value;

    if (selectedServiceIds.includes(sId)) {
        alert("Dịch vụ này đã được chọn!");
        cbo.selectedIndex = 0;
        return;
    }

     // Đánh dấu đã chọn
    selectedServiceIds.push(sId);

    const sName = selectedOption.getAttribute('data-name');
    const sPrice = parseInt(selectedOption.getAttribute('data-price'));
    const sDesc = selectedOption.getAttribute('data-desc');


    // Thêm dòng mới vào bảng
    const tbody = document.getElementById('tblServiceBody');
    const rowCount = tbody.rows.length + 1;

    const tr = document.createElement('tr');
//    tr.id = `row-service-${rowCount}`; // ID để dễ xóa
    tr.innerHTML = `
        <td class="text-center">${rowCount}</td>
        <td>${sName}</td>
        <td class="text-center">${formatCurrency(sPrice)}</td>
        <td>${sDesc}</td>
        <td class="text-center">
            <i class="bi bi-trash text-danger" style="cursor:pointer;" onclick="removeService(this, ${sPrice})"></i>
        </td>
    `;
    tbody.appendChild(tr);

    // Tính tổng tiền
    currentTotal += sPrice;
    updateTotalLabel();

    // Reset dropdown về default
    cbo.selectedIndex = 0;
}

// STT 5: Xóa dịch vụ
function removeService(btn, price) {
    // Xóa dòng tr
    const row = btn.parentNode.parentNode;
    row.parentNode.removeChild(row);

    // Trừ tiền
    currentTotal -= price;
    updateTotalLabel();
    //
    reindexServiceTable();
}
//danh stt
function reindexServiceTable() {
    const rows = document.querySelectorAll('#tblServiceBody tr');
    rows.forEach((tr, index) => {
        // Cột STT là td đầu tiên
        tr.children[0].innerText = index + 1;
    });
}

function updateTotalLabel() {
    document.getElementById('lblTotal').innerText = formatCurrency(currentTotal);
}
//reset form
function resetFormPartially() {
    isExamining = false;
    setFormEnabled(false);
    document.getElementById('txtDiagnosis').value = "";
    document.getElementById('tblServiceBody').innerHTML = "";
    currentTotal = 0;
    prescriptionList = []
    selectedServiceIds=[]
    updateTotalLabel();
    //Reset thông tin bệnh nhân
    document.getElementById('lblPatientName').innerText = '...';
    document.getElementById('lblPatientAge').innerText = '...';
    document.getElementById('lblHistory').innerText = '...';
    document.getElementById('iconWarning').style.display = 'none';
    //Load lại hàng đợi
    reloadPatientQueue();
     //Mở lại danh sách
    document.getElementById('patientQueueList').classList.remove('queue-disabled');
    //Bỏ highlight
    document.querySelectorAll('.queue-item').forEach(item => item.classList.remove('active'));
    //Ẩn nút hủy
    document.getElementById('btnCancelExam').classList.add('d-none');
}

//KÊ ĐƠN

//load form + mở modal
document.getElementById('btnKeDonThuoc').addEventListener('click', async () => {
    if (!currentPatientId) {
        alert("Vui lòng chọn bệnh nhân trước!");
        return;
    }

    // Set tên bệnh nhân lên title
    const pName = document.getElementById('lblPatientName').innerText;
    document.getElementById('lblPrescriptionPatient').innerText = pName;

    // Load lại danh sách thuốc cũ (nếu có - logic sửa lại đơn)
    //renderPrescriptionTable();

    // Hiển thị Modal
    const myModal = new bootstrap.Modal(document.getElementById('prescriptionModal'));
    myModal.show();

    // Focus vào ô tìm kiếm sau khi modal mở
    setTimeout(() => document.getElementById('txtSearchMedicine').focus(), 500);
});
//tim thuoc
const txtSearch = document.getElementById("txtSearchMedicine");
const suggestionBox = document.getElementById("suggestionBox");

txtSearch.addEventListener("input", async function () {
    const keyword = this.value.trim();
    console.log(keyword);

    if (keyword.length < 1) {
        suggestionBox.style.display = "none";
        return;
    }

    try {
        const res = await fetch(`/api/medicines/search?q=${keyword}`);
        const data = await res.json();

        suggestionBox.innerHTML = "";

        if (!data || data.length === 0) {
            suggestionBox.style.display = "none";
            return;
        }

        suggestionBox.style.display = "block";

        data.forEach(med => {
            const item = document.createElement("a");
            item.href = "#";
            item.className = "list-group-item list-group-item-action";

            item.innerHTML = `
                <div class="d-flex justify-content-between">
                    <strong>${med.name}</strong>
                    <span class="badge bg-secondary">Tồn: ${med.stock}</span>
                </div>
                <small class="text-muted">${med.id} - ${med.price} đ/${med.unit}</small>
            `;

            item.onclick = (e) => {
                e.preventDefault();
                selectMedicine(med);
            };

            suggestionBox.appendChild(item);
        });
    } catch (err) {
        console.error("API error:", err);
    }
});

//chon thuoc
function selectMedicine(med) {
    currentSelectedMed = med;
    txtSearch.value = med.name;

    document.getElementById('lblUnit').innerText = med.unit;
    document.getElementById('lblStock').innerText = `(Tồn kho: ${med.stock})`;
    document.getElementById('txtUsage').value = med.usage || '';
    document.getElementById('txtQuantity').value = 1;
    document.getElementById('txtQuantity').max = med.stock;

    suggestionBox.style.display = 'none';
}

//them vao ds tam
function addMedicineToGrid() {
    if (!currentSelectedMed) {
        alert("Vui lòng chọn thuốc từ danh sách gợi ý!");
        return;
    }

    const qty = parseInt(document.getElementById('txtQuantity').value);
    const usage = document.getElementById('txtUsage').value.trim();
    const stock = currentSelectedMed.stock;

    // Validate
    if (isNaN(qty) || qty <= 0) {
        alert("Số lượng phải lớn hơn 0");
        return;
    }

    if (qty > stock) {
        alert(`Vượt quá tồn kho! (Tối đa: ${stock})`);
        return;
    }

    if (!usage) {
        alert("Vui lòng nhập liều dùng!");
        return;
    }

    // Kiểm tra trùng thuốc
    const existIndex = prescriptionList.findIndex(
        m => m.id === currentSelectedMed.id
    );

    if (existIndex >= 0) {
        const newQty = prescriptionList[existIndex].quantity + qty;

        if (newQty > stock) {
            alert(`Tổng số lượng (${newQty}) vượt quá tồn kho (${stock})!`);
            return;
        }

        prescriptionList[existIndex].quantity = newQty;
        prescriptionList[existIndex].usage = usage;
    } else {
        prescriptionList.push({
            id: currentSelectedMed.id,
            name: currentSelectedMed.name,
            unit: currentSelectedMed.unit,
            price: currentSelectedMed.price,
            quantity: qty,
            usage: usage
        });
    }

    renderPrescriptionTable();
    resetInputSection();
}

document.getElementById("btnAddMedicine").addEventListener('click', function () {
    addMedicineToGrid();
});

function resetInputSection() {
    // Ô tìm thuốc
    txtSearch.value = '';

    // Số lượng & liều dùng
    const txtQty = document.getElementById('txtQuantity');
    const txtUsage = document.getElementById('txtUsage');

    txtQty.value = 1;
    txtUsage.value = '';

    // Nhãn thông tin
    document.getElementById('lblUnit').innerText = '';
    document.getElementById('lblStock').innerText = '';

    // Reset thuốc đang chọn
    currentSelectedMed = null;

    // Ẩn danh sách gợi ý
    suggestionBox.style.display = 'none';

    // Focus lại ô tìm
    txtSearch.focus();
}

//render bang va xoa

function removeMedicine(btn) {

    const row = btn.parentNode.parentNode;
    const medId = row.dataset.medId; // ✅ ĐÚNG ID

    // Tim trong array
    const index = prescriptionList.findIndex(
        m => m.id == medId
    );

    if (index === -1) return;

    // xoa data
    prescriptionList.splice(index, 1);
    //xoa giao dien
    row.parentNode.removeChild(row);
}

function renderPrescriptionTable() {
    const tbody = document.getElementById('tblPrescriptionBody');
    const rowCount = tbody.rows.length;
    tbody.innerHTML = '';

    prescriptionList.forEach((item, index) => {
        const tr = document.createElement('tr');
        tr.id = `${rowCount}`; // ID để dễ xóa
        tr.dataset.medId = item.id;
        console.log(tr.dataset.medId)
        console.log(tr.id)
        tr.innerHTML = `
            <td class="text-center">${index + 1}</td>
            <td>${item.name}</td>
            <td class="text-center">${item.unit}</td>
            <td class="text-center fw-bold">${item.quantity}</td>
            <td class="text-end">${formatCurrency(item.price)}</td>
            <td>${item.usage}</td>
            <td class="text-center">
                <i class="bi bi-trash text-danger" style="cursor:pointer;" onclick="removeMedicine(this,)"></i>
            </td>
        `;

        tbody.appendChild(tr);
    });
}

//huy
const btnCancelPrescription = document.getElementById('btnCancelPrescription');
btnCancelPrescription.addEventListener('click', async () => {
    // Xác nhận hủy
   const isConfirmed = await showAlert(
        "Xác nhận hủy?",
        "Dữ liệu sẽ không được lưu lại!!"
    );
   if(!isConfirmed) return;

    // Reset dữ liệu
    prescriptionList = [];
    currentSelectedMed = null;

    // Reset giao diện
    resetInputSection();
    renderPrescriptionTable();

    // Đóng modal
    const modalEl = document.getElementById('prescriptionModal');
    const modal = bootstrap.Modal.getInstance(modalEl);
    modal.hide();

    //reset nút ke don
    const btnOpen = document.getElementById("btnKeDonThuoc");
    if (btnOpen) {
        btnOpen.innerText = "KÊ ĐƠN THUỐC";
        btnOpen.classList.remove('btn-info', 'text-white');
        btnOpen.classList.add('btn-outline-info');
    }
});

//Xac nhan luu don thuoc
function confirmPrescription() {
    const isConfirmed = await showAlert(
        "Xác nhận Lưu Đơn Thuốc?",
        "Sao khi lưu bạn có thể chỉnh sửa trước khi hoàn tất phiếu khám"
    );
    if(!isConfirmed) return;

    // Đóng Modal (Bootstrap 5 API)
    const modalEl = document.getElementById('prescriptionModal');
    const modal = bootstrap.Modal.getInstance(modalEl);
    modal.hide();

    // Cập nhật giao diện bên ngoài (Optional)
    const btnOpen = document.getElementById('btnKeDonThuoc'); // Nút Kê đơn ở màn hình chính
    console.log(prescriptionList)
    if (prescriptionList.length > 0) {
        btnOpen.innerText = `KÊ ĐƠN THUỐC (${prescriptionList.length} thuốc)`;
        btnOpen.classList.remove('btn-outline-info');
        btnOpen.classList.add('btn-info', 'text-white');
    } else {
        btnOpen.innerText = "KÊ ĐƠN THUỐC";
    }
}

btnConfirmPrescription.addEventListener('click', function () {
    confirmPrescription();
})

//Hoan thanh phieu khám và lưu CSDl
document.getElementById('btnLuuPhieu').addEventListener('click', async () => {
    const isConfirmed = await showAlert(
        "Xác nhận Hoàn tất Phiếu khám??",
        "Vui lòng đảm bảo thông tin chính xác trước khi xác nhận."
    );
    if(!isConfirmed) return;


    if (!currentPatientId) {
        Alert.error("Lỗi", "Chưa chọn bệnh nhân");
        return;
    }

    const payload = {
        maBenhNhan: currentPatientId,
        maLichHen: selectedAppointmentId,
        chuanDoan: document.getElementById('txtDiagnosis').value,
        services: selectedServiceIds,
        medicines: prescriptionList.map(m => ({
            maThuoc: m.id,
            soLuong: m.quantity,
            lieuDung: m.usage
        }))
    };

    try {
        const res = await fetch('/api/save-examination', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const data = await res.json();

        if (data.success) {
            alert("Lưu phiếu khám thành công!");
            resetFormPartially();
        } else {
            alert(data.message || "Lưu thất bại");
        }
    } catch (err) {
        console.error(err);
        alert("Lỗi kết nối server");
    }
})
