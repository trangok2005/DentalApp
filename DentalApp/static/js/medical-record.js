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
        "Xác nhận hủy lập phiếu?",
        "Dữ liệu sẽ không được lưu lại!!"
    );

    if (!isConfirmed) return;

    resetFormPartially();

    const btnOpen = document.getElementById("btnKeDonThuoc");
    if (btnOpen) {
        btnOpen.innerText = "KÊ ĐƠN THUỐC";
        btnOpen.classList.remove('btn-info', 'text-white');
        btnOpen.classList.add('btn-outline-info');
    }
});


// STT 4: Thêm dịch vụ & Tính tiền
document.getElementById('cboServices').addEventListener('change', function() {
     const cbo = document.getElementById('cboServices');
    const selectedOption = cbo.options[cbo.selectedIndex];

    if (cbo.value === "") return;

    const sId = cbo.value;

    if (selectedServiceIds.includes(sId)) {
        Alert.error("", "Dịch vụ này đã được chọn!");
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
   //id = `row-service-${rowCount}`; // để dễ xóa
   tr.innerHTML = `
        <td class="text-center">${rowCount}</td>
        <td>${sName}</td>
        <td class="text-center">${formatCurrency(sPrice)}</td>
        <td>${sDesc}</td>
        <td class="text-center">
            <i class="bi bi-trash text-danger btn-remove-service" style="cursor:pointer;"></i>
        </td>
   `;
    tbody.appendChild(tr);

    // Tính tổng tiền
    currentTotal += sPrice;
    updateTotalLabel();

    // Reset dropdown về default
    cbo.selectedIndex = 0;
});

// Xóa dịch vụ
//xoa khoi list, xoa UI, cap nhat stt
function removeItem(list, row, Id, tBody) {
    const index = list.findIndex(m => m.id == Id);
    if (index !== -1) {
        list.splice(index, 1);
    }
    row.remove();
    reindexTable(tBody);
}

document.getElementById('tblServiceBody').addEventListener('click', function (e) {
    const btn = e.target.closest('.btn-remove-service');
    if (!btn) return;

    const row = btn.closest('tr');
    const price = parseInt(row.dataset.price);
    const serviceId = row.dataset.serviceId;

    // Trừ tiền
    currentTotal -= price;
    updateTotalLabel();

    //goi ham xoa
    removeItem(selectedServiceIds, row, serviceId, "#tblServiceBody")
});
//danh stt
function reindexTable(tbodySelector) {
    const rows = document.querySelectorAll(`${tbodySelector} tr`);
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
    currentPatientId = null;
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
        Alert.warning("Chưa chọn bênh nhân", "Vui lòng chọn bệnh nhân trước!");
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

//btn them thuoc vao ds tam
function addMedicineToGrid() {
    if (!currentSelectedMed) {
        Alert.warning("Chưa chọn thuốc", "Vui lòng chọn thuốc từ danh sách gợi ý!");
        return;
    }

    const qty = parseInt(document.getElementById('txtQuantity').value);
    const usage = document.getElementById('txtUsage').value.trim();
    const stock = currentSelectedMed.stock;

    // Validate
    if (isNaN(qty) || qty <= 0) {
        Alert.warning("Lưu ý", "Số lượng phải lớn hơn 0");
        return;
    }

    if (qty > stock) {
         Alert.warning("Lưu ý", `Vượt quá tồn kho! (Tối đa: ${stock})`);
        return;
    }

    if (!usage) {
         Alert.warning("Lưu ý", "Vui lòng nhập liều dùng!");
        return;
    }

    // Kiểm tra trùng thuốc
    const existIndex = prescriptionList.findIndex(
        m => m.id === currentSelectedMed.id
    );

    if (existIndex >= 0) {
        const newQty = prescriptionList[existIndex].quantity + qty;

        if (newQty > stock) {
            Alert.warning("Cảnh báo", `Tổng số lượng (${newQty}) vượt quá tồn kho (${stock})!`);
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

//reset form tim thuốc
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
function renderPrescriptionTable() {
    const tbody = document.getElementById('tblPrescriptionBody');
    const rowCount = tbody.rows.length;
    tbody.innerHTML = '';

    prescriptionList.forEach((item, index) => {
        const tr = document.createElement('tr');
        //tr.id = `${rowCount}`;
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
                <i class="bi bi-trash text-danger btn-remove-med" style="cursor:pointer;"></i>
            </td>
        `;

        tbody.appendChild(tr);
    });
}

document.getElementById('tblPrescriptionBody').addEventListener('click', async function (e) {
    const btn = e.target.closest('.btn-remove-med');
    if (!btn) return;

    const row = btn.closest('tr');
    const medId = row.dataset.medId;
    //goi ham xoa
    removeItem(prescriptionList, row, medId, "#tblPrescriptionBody");
});

//huy kê đơn
const btnCancelPrescription = document.getElementById('btnCancelPrescription');
btnCancelPrescription.addEventListener('click', async function () {
    const isConfirmed = await showAlert(
        "Xác nhận hủy kê đơn?",
        "Dữ liệu sẽ không được lưu lại!!"
    );

    if (!isConfirmed) return;

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

    // Reset nút kê đơn
    const btnOpen = document.getElementById("btnKeDonThuoc");
    if (btnOpen) {
        btnOpen.innerText = "KÊ ĐƠN THUỐC";
        btnOpen.classList.remove('btn-info', 'text-white');
        btnOpen.classList.add('btn-outline-info');
    }
});

// lưu đơn thuốc
btnConfirmPrescription.addEventListener('click',async () => {
    const isConfirmed = await showAlert(
        "Xác nhận Lưu Đơn Thuốc?",
        "Sau khi lưu bạn có thể chỉnh sửa trước khi hoàn tất phiếu khám"
    );

    if (!isConfirmed) return;


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
})

//Hoan thanh phieu khám và lưu CSDl
document.getElementById('btnLuuPhieu').addEventListener('click', async () => {
    if (!currentPatientId) {
        Alert.error("Thiếu thông tin", "Chưa chọn bệnh nhân");
        return;
    }

    const diagnosis = document.getElementById("txtDiagnosis")
    if (!diagnosis.value.trim()) {
        Alert.warning("Thiếu thông tin", "Vui lòng nhập chẩn đoán");
        diagnosis.focus();
        return;
    }

    // Kiểm tra đã chọn dịch vụ
    if (!selectedServiceIds || selectedServiceIds.length === 0) {
        Alert.warning("Thiếu thông tin", "Vui lòng chọn ít nhất 1 dịch vụ");
        return;
    }

    const isConfirmed = await showAlert(
        "Xác nhận Hoàn tất Phiếu khám?",
       "Kiểm tra thông tin trước khi xác nhận!!"
    );

    if (!isConfirmed) return;


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
            Alert.success("Hoàn tất","Lưu phiếu khám thành công!");
            resetFormPartially();
        } else {
            Alert.error(data.message, "Lưu thất bại");
        }
    } catch (err) {
        console.error(err);
        Alert.error("Lỗi","Lỗi kết nối server");
    }
})
