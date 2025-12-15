let currentPatientId = null;
let currentTotal = 0;
let selectedServiceIds = []; // Mảng chứa các ID dịch vụ đã chọn
setFormEnabled(false)

// Format tiền tệ (VD: 100000 -> 100.000)
function formatCurrency(n) {
    return new Intl.NumberFormat('vi-VN').format(n);
}
//disabled khi chua chon benh nhan
function setFormEnabled(enabled) {
    document.getElementById('txtDiagnosis').disabled = !enabled;
    document.getElementById('cboServices').disabled = !enabled;
}

// STT 2: Xem thông tin bệnh nhân
async function selectPatient(pid, element) {
    // Highlight UI
    document.querySelectorAll('.queue-item').forEach(el => el.classList.remove('active'));
    element.classList.add('active');
    element.querySelector('.status').innerText = 'Đang khám';

//      Gọi API lấy thông tin
    try {
        const res = await fetch(`/api/patient/${pid}`);
        const data = await res.json();

        if (data.error) { alert('Không tìm thấy bệnh nhân'); return; }

        const birth = new Date(data.NgaySinh);
        const age = new Date().getFullYear() - birth.getFullYear()
                    - (new Date().getMonth() < birth.getMonth()
                    || (new Date().getMonth() === birth.getMonth()
                    && new Date().getDate() < birth.getDate()));

        // Binding dữ liệu lên UI
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

        // Reset form cho bệnh nhân mới
        resetFormPartially();

    } catch (err) {
        console.error(err);
    }
}

document.querySelectorAll('.queue-item').forEach(item => {
item.addEventListener('click', async function () {
    const pid = this.dataset.pid;
    console.log('PID =', pid);

    if (!pid) {
        alert('Không có mã bệnh nhân');
        return;
    }

    await selectPatient(pid, this);
});
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
    tr.id = `row-service-${rowCount}`; // ID để dễ xóa
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

    // (Optional) Đánh lại số thứ tự STT nếu cần thiết
}

function updateTotalLabel() {
    document.getElementById('lblTotal').innerText = formatCurrency(currentTotal);
}

function resetFormPartially() {
    document.getElementById('txtDiagnosis').value = "";
    document.getElementById('tblServiceBody').innerHTML = "";
    currentTotal = 0;
    updateTotalLabel();
}

//    // STT 6: Mở trang kê đơn (Mockup)
//    function openPrescription() {
//        if (!currentPatientId) {
//            alert("Vui lòng chọn bệnh nhân trước!");
//            return;
//        }
//        alert(`Đang mở form kê đơn thuốc cho ID: ${currentPatientId}`);
//        // window.open('/ke-don-thuoc?pid=' + currentPatientId, '_blank');
//    }
//
//    // STT 7: Lưu phiếu & Làm mới
//    async function saveExamination() {
//        if (!currentPatientId) {
//            alert("Chưa chọn bệnh nhân!");
//            return;
//        }
//
//        const diagnosis = document.getElementById('txtDiagnosis').value;
//        // Lấy danh sách dịch vụ từ bảng (để chính xác những gì đang hiển thị)
//        // Trong thực tế, có thể duy trì 1 mảng object services
//
//        const payload = {
//            patient_id: currentPatientId,
//            diagnosis: diagnosis,
//            total_amount: currentTotal,
//            // services: ... (List các dịch vụ đã chọn)
//        };
//
//        try {
//            const res = await fetch('/api/save-examination', {
//                method: 'POST',
//                headers: {'Content-Type': 'application/json'},
//                body: JSON.stringify(payload)
//            });
//            const result = await res.json();
//
//            if (result.success) {
//                alert(result.message);
//                // Reload trang để cập nhật lại Hàng chờ (Bệnh nhân đã khám sẽ mất đi hoặc đổi trạng thái)
//                location.reload();
//            } else {
//                alert("Lỗi: " + result.message);
//            }
//        } catch (err) {
//            console.error(err);
//            alert("Lỗi kết nối server");
//        }
//    }

//ke don
// --- BIẾN TOÀN CỤC ---
let prescriptionList = []; // Mảng chứa thuốc đã chọn
let currentSelectedMed = null; // Thuốc đang chọn tạm ở ô search

// STT 1: Load Form - Mở Modal
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

function removeMedicine(btn, index) {
    const row = btn.parentNode.parentNode;
    row.parentNode.removeChild(row);
      prescriptionList.splice(index, 1);
}

function renderPrescriptionTable() {
    const tbody = document.getElementById('tblPrescriptionBody');
    const rowCount = tbody.rows.length + 1;
    tbody.innerHTML = '';

    prescriptionList.forEach((item, index) => {
        const tr = document.createElement('tr');
        tr.id = `row--${rowCount}`; // ID để dễ xóa
        tr.dataset.medId = item.id;
        tr.innerHTML = `
            <td class="text-center">${index + 1}</td>
            <td>${item.name}</td>
            <td class="text-center">${item.unit}</td>
            <td class="text-center fw-bold">${item.quantity}</td>
            <td class="text-end">${formatCurrency(item.price)}</td>
            <td>${item.usage}</td>
            <td class="text-center">
                <i class="bi bi-trash text-danger" style="cursor:pointer;" onclick="removeMedicine(this,dataset.medId)"></i>
            </td>
        `;

        tbody.appendChild(tr);
    });
}

//huy
const btnCancelPrescription = document.getElementById('btnCancelPrescription');
btnCancelPrescription.addEventListener('click', function () {
    // Xác nhận hủy
    if (!confirm("Bạn có chắc muốn hủy kê đơn không?")) return;

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

    // Reset nút KÊ ĐƠN (nếu có)
//    const btnOpen = document.querySelector('.btn-prescribe');
//    if (btnOpen) {
//        btnOpen.innerText = "KÊ ĐƠN THUỐC";
//        btnOpen.classList.remove('btn-info', 'text-white');
//        btnOpen.classList.add('btn-outline-info');
//    }
});

//Xac nhan luu don thuoc

function confirmPrescription() {
    if (!confirm("Bạn có chắc muốn lưu kê đơn không?")) return;

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

