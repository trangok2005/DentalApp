import { showAlert, Alert, showSimpleAlert } from './app.js';

let currentPatientId = null;
let selectedAppointmentId = null;
let isExamining = false;
let currentTotal = 0;

setFormEnabled(false);

function formatCurrency(n) {
    return new Intl.NumberFormat('vi-VN').format(n);
}

function setFormEnabled(enabled) {
    document.getElementById('txtDiagnosis').disabled = !enabled;
    document.getElementById('cboServices').disabled = !enabled;
}

document.addEventListener('DOMContentLoaded', () => {
    reloadPatientQueue();
});

// --- PHẦN 1: CHỌN BỆNH NHÂN & INIT SESSION ---
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
        if (p.maLH === selectedAppointmentId) div.classList.add('active');

        div.dataset.pid = p.maBenhNhan;
        div.dataset.appt = p.maLH;

        div.innerHTML = `${index + 1}. ${p.hoTen} – ${p.gioKham} <span class="status">${p.isLate ? '[Muộn giờ]' : '[Chờ khám]'}</span>`;

        div.addEventListener('click', async function () {
            await selectPatient(this.dataset.pid, this.dataset.appt, this);
        });
        container.appendChild(div);
    });
}

async function selectPatient(pid, apptId, element) {
    if (isExamining) return;

    // UI Effects
    document.querySelectorAll('.queue-item').forEach(el => el.classList.remove('active'));
    element.classList.add('active');
    element.querySelector('.status').innerText = 'Đang khám';
    isExamining = true;
    document.getElementById('patientQueueList').classList.add('queue-disabled');
    document.getElementById('btnCancelExam').classList.remove('d-none');

    try {
        // 1. Lấy thông tin bệnh nhân hiển thị
        const res = await fetch(`/api/patient/${pid}`);
        const data = await res.json();
        if (data.error) { Alert.error("Lỗi", 'Không tìm thấy bệnh nhân'); return; }

        // Render Info UI
        const birth = new Date(data.NgaySinh);
        const age = new Date().getFullYear() - birth.getFullYear();
        currentPatientId = data.MaNguoiDung;
        selectedAppointmentId = apptId;
        
        setFormEnabled(true);
        document.getElementById('lblPatientName').innerText = data.HoTen;
        document.getElementById('lblPatientAge').innerText = age;
        document.getElementById('lblHistory').innerText = data.TienSuBenh || 'Không';
        document.getElementById('iconWarning').style.display = data.TienSuBenh ? 'inline-block' : 'none';

        // 2. QUAN TRỌNG: Gọi API khởi tạo Session trên Server
        await fetch('/api/cart/init', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ maBenhNhan: pid, maLichHen: apptId })
        });

        // Reset bảng dịch vụ UI về rỗng (vì session mới tạo chưa có gì)
        renderServicesTable([]); 
        
    } catch (err) {
        console.error(err);
    }
}

// --- PHẦN 2: DỊCH VỤ (SERVICES) QUA SESSION ---

// Sự kiện chọn combobox
document.getElementById('cboServices').addEventListener('change', async function() {
    const cbo = document.getElementById('cboServices');
    if (cbo.value === "") return;

    const selectedOption = cbo.options[cbo.selectedIndex];
    
    // Tạo payload gửi lên server
    const payload = {
        id: cbo.value,
        name: selectedOption.getAttribute('data-name'),
        price: parseInt(selectedOption.getAttribute('data-price')),
        desc: selectedOption.getAttribute('data-desc')
    };

    try {
        // Gọi API thêm vào Session
        const res = await fetch('/api/cart/add-service', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        
        const data = await res.json(); // Data trả về là danh sách Services mới nhất
        
        if (res.status === 400) {
            Alert.error("Lỗi", data.error); // Lỗi trùng dịch vụ
        } else {
            renderServicesTable(data); // Vẽ lại bảng dựa trên dữ liệu Server trả về
        }
    } catch (e) { console.error(e); }

    cbo.selectedIndex = 0;
});

// Hàm vẽ bảng dịch vụ (Nhận list từ server)
function renderServicesTable(serviceList) {
    const tbody = document.getElementById('tblServiceBody');
    tbody.innerHTML = '';
    currentTotal = 0;

    serviceList.forEach((s, index) => {
        currentTotal += s.price;
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td class="text-center">${index + 1}</td>
            <td>${s.name}</td>
            <td class="text-center">${formatCurrency(s.price)}</td>
            <td>${s.desc}</td>
            <td class="text-center">
                <i class="bi bi-trash text-danger btn-remove-service" data-id="${s.id}" style="cursor:pointer;"></i>
            </td>
        `;
        tbody.appendChild(tr);
    });
    document.getElementById('lblTotal').innerText = formatCurrency(currentTotal);
}

// Xóa dịch vụ (Gọi API remove)
document.getElementById('tblServiceBody').addEventListener('click', async function (e) {
    if (e.target.classList.contains('btn-remove-service')) {
        const id = e.target.dataset.id;
        
        const res = await fetch('/api/cart/remove-service', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ id: id })
        });
        const updatedList = await res.json();
        renderServicesTable(updatedList);
    }
});

// --- PHẦN 3: KÊ ĐƠN THUỐC QUA SESSION ---

// Thêm thuốc (Gọi API Add Medicine)
async function addMedicineToGrid() {
    if (!currentSelectedMed) {
        Alert.warning("Chưa chọn thuốc", "Vui lòng chọn thuốc từ gợi ý!");
        return;
    }

    const qty = parseInt(document.getElementById('txtQuantity').value);
    const usage = document.getElementById('txtUsage').value.trim();

    // Validate Client cơ bản
    if (isNaN(qty) || qty <= 0) { Alert.warning("Lỗi", "Số lượng phải > 0"); return; }
    if (!usage) { Alert.warning("Lỗi", "Nhập liều dùng"); return; }

    const payload = {
        id: currentSelectedMed.id,
        name: currentSelectedMed.name,
        unit: currentSelectedMed.unit,
        price: currentSelectedMed.price,
        stock: currentSelectedMed.stock,
        quantity: qty,
        usage: usage
    };

    try {
        const res = await fetch('/api/cart/add-medicine', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        
        const data = await res.json();
        if (res.status === 400) {
            Alert.warning("Cảnh báo", data.error);
        } else {
            renderPrescriptionTable(data); // Vẽ lại bảng với data từ server
            resetInputSection();
        }
    } catch(e) { console.error(e); }
}

document.getElementById("btnAddMedicine").addEventListener('click', addMedicineToGrid);

// Hàm vẽ bảng thuốc (Nhận list từ Server)
function renderPrescriptionTable(medList) {
    const tbody = document.getElementById('tblPrescriptionBody');
    tbody.innerHTML = '';
    
    // Cập nhật text nút mở modal
    const btnOpen = document.getElementById('btnKeDonThuoc');
    if (medList.length > 0) {
        btnOpen.innerText = `KÊ ĐƠN THUỐC (${medList.length})`;
        btnOpen.classList.add('btn-info', 'text-white');
    } else {
        btnOpen.innerText = "KÊ ĐƠN THUỐC";
        btnOpen.classList.remove('btn-info', 'text-white');
    }

    medList.forEach((item, index) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td class="text-center">${index + 1}</td>
            <td>${item.name}</td>
            <td class="text-center">${item.unit}</td>
            <td class="text-center fw-bold">${item.quantity}</td>
            <td class="text-end">${formatCurrency(item.price)}</td>
            <td>${item.usage}</td>
            <td class="text-center">
                <i class="bi bi-trash text-danger btn-remove-med" data-id="${item.id}" style="cursor:pointer;"></i>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// Xóa thuốc (Gọi API Remove Medicine)
document.getElementById('tblPrescriptionBody').addEventListener('click', async function (e) {
    if (e.target.classList.contains('btn-remove-med')) {
        const id = e.target.dataset.id;
        
        const res = await fetch('/api/cart/remove-medicine', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ id: id })
        });
        const updatedList = await res.json();
        renderPrescriptionTable(updatedList);
    }
});

//Hủy kê thuốc
const btnCancelPrescription = document.getElementById('btnCancelPrescription');
btnCancelPrescription.addEventListener('click', async function () {
    // 1. Hỏi xác nhận trước khi xóa
    const isConfirmed = await showAlert(
        "Hủy kê đơn?",
        "Toàn bộ thuốc đã chọn trong danh sách sẽ bị xóa!"
    );

    if (!isConfirmed) return;

    try {
        // 2. Gọi API để xóa sạch thuốc trong Session Server
        const res = await fetch('/api/cart/clear-medicines', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        // 3. Reset giao diện về rỗng
        renderPrescriptionTable([]); // Truyền mảng rỗng để xóa bảng
        resetInputSection();         // Xóa các ô input tìm kiếm

        // 4. Đóng Modal
        const modalEl = document.getElementById('prescriptionModal');
        const modal = bootstrap.Modal.getInstance(modalEl);
        modal.hide();

    } catch (err) {
        console.error("Lỗi khi hủy đơn thuốc:", err);
        Alert.error("Lỗi", "Không thể hủy đơn thuốc lúc này.");
    }
});

// --- PHẦN 4: LƯU PHIẾU ---
document.getElementById('btnLuuPhieu').addEventListener('click', async () => {
    if (!currentPatientId) return;

    const diagnosis = document.getElementById("txtDiagnosis").value.trim();
    if (!diagnosis) { Alert.warning("Thiếu thông tin", "Nhập chẩn đoán"); return; }
    if (currentTotal === 0) { Alert.warning("Thiếu thông tin", "Chưa chọn dịch vụ"); return; }

    const isConfirmed = await showAlert("Xác nhận", "Hoàn tất phiếu khám?");
    if (!isConfirmed) return;

    try {
        // Chỉ gửi chẩn đoán, mọi thứ khác Server tự lấy từ Session
        const res = await fetch('/api/save-examination', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ chuanDoan: diagnosis })
        });

        const data = await res.json();
        if (data.success) {
            Alert.success("Thành công", "Đã lưu phiếu khám!");
            resetFormPartially();
        } else {
            Alert.error("Thất bại", data.message);
        }
    } catch (err) {
        Alert.error("Lỗi mạng", err.message);
    }
});

// --- CÁC HÀM PHỤ TRỢ (Giữ nguyên hoặc chỉnh nhẹ) ---

// Tìm thuốc & Chọn thuốc (Giữ nguyên logic cũ nhưng chú ý biến currentSelectedMed)
let currentSelectedMed = null;
const txtSearch = document.getElementById("txtSearchMedicine");
const suggestionBox = document.getElementById("suggestionBox");
// ... (Logic search thuốc giữ nguyên như code cũ của bạn) ...
txtSearch.addEventListener("input", async function () {
    const keyword = this.value.trim();
    if (keyword.length < 1) { suggestionBox.style.display = "none"; return; }
    try {
        const res = await fetch(`/api/medicines/search?q=${keyword}`);
        const data = await res.json();
        suggestionBox.innerHTML = "";
        if (!data || data.length === 0) { suggestionBox.style.display = "none"; return; }
        suggestionBox.style.display = "block";
        data.forEach(med => {
            const item = document.createElement("a");
            item.className = "list-group-item list-group-item-action";
            item.innerHTML = `<strong>${med.name}</strong> - Tồn: ${med.stock}`;
            item.onclick = (e) => { e.preventDefault(); selectMedicine(med); };
            suggestionBox.appendChild(item);
        });
    } catch (err) { console.error(err); }
});

function selectMedicine(med) {
    currentSelectedMed = med;
    txtSearch.value = med.name;
    document.getElementById('lblUnit').innerText = med.unit;
    document.getElementById('lblStock').innerText = `(Tồn: ${med.stock})`;
    document.getElementById('txtUsage').value = med.usage || '';
    document.getElementById('txtQuantity').value = 1;
    suggestionBox.style.display = 'none';
}

function resetInputSection() {
    txtSearch.value = '';
    document.getElementById('txtQuantity').value = 1;
    document.getElementById('txtUsage').value = '';
    document.getElementById('lblUnit').innerText = '';
    document.getElementById('lblStock').innerText = '';
    currentSelectedMed = null;
    txtSearch.focus();
}

// Reset Form khi hủy hoặc xong
function resetFormPartially() {
    isExamining = false;
    setFormEnabled(false);
    document.getElementById('txtDiagnosis').value = "";
    document.getElementById('tblServiceBody').innerHTML = "";
    document.getElementById('tblPrescriptionBody').innerHTML = "";
    currentTotal = 0;
    currentPatientId = null;
    
    updateTotalLabel();
    document.getElementById('lblPatientName').innerText = '...';
    document.getElementById('lblPatientAge').innerText = '...';
    document.getElementById('lblHistory').innerText = '...';
    document.getElementById('iconWarning').style.display = 'none';
    
    // Reset nút kê đơn
    const btnOpen = document.getElementById('btnKeDonThuoc');
    btnOpen.innerText = "KÊ ĐƠN THUỐC";
    btnOpen.classList.remove('btn-info', 'text-white');
    
    reloadPatientQueue();
    document.getElementById('patientQueueList').classList.remove('queue-disabled');
    document.getElementById('btnCancelExam').classList.add('d-none');
}

document.getElementById('btnCancelExam').addEventListener('click', async () => {
   const confirm = await showAlert("Hủy bỏ?", "Dữ liệu phiên làm việc sẽ mất.");
   if(confirm) {
       resetFormPartially();
       // Có thể gọi thêm API clear session nếu muốn chắc chắn
   }
});

function updateTotalLabel() {
    document.getElementById('lblTotal').innerText = formatCurrency(currentTotal);
}

// Nút mở modal kê đơn (Giữ nguyên, chỉ cần mở modal)
document.getElementById('btnKeDonThuoc').addEventListener('click', () => {
    if (!currentPatientId) { Alert.warning("Lỗi", "Chưa chọn bệnh nhân"); return; }
    document.getElementById('lblPrescriptionPatient').innerText = document.getElementById('lblPatientName').innerText;
    new bootstrap.Modal(document.getElementById('prescriptionModal')).show();
    setTimeout(() => document.getElementById('txtSearchMedicine').focus(), 500);
});

// Nút xác nhận trong modal (Chỉ cần ẩn modal vì data đã sync với server mỗi khi Add/Remove)
document.getElementById('btnConfirmPrescription').addEventListener('click', () => {
    bootstrap.Modal.getInstance(document.getElementById('prescriptionModal')).hide();
});

// Nút hủy trong modal (Cần gọi API xóa hết thuốc nếu muốn tính năng Hủy đúng nghĩa, hoặc chỉ đóng modal)
document.getElementById('btnCancelPrescription').addEventListener('click', async () => {
    // Tùy logic: ở đây tôi chỉ đóng modal, giữ nguyên những gì đã thêm
    bootstrap.Modal.getInstance(document.getElementById('prescriptionModal')).hide();
});