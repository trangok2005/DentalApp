
//// STT 2: Txt_TimKiem_Input & List_GoiY_Select
//const txtSearch = document.getElementById('txtSearchMedicine');
//const suggestionBox = document.getElementById('suggestionBox');
//
//txtSearch.addEventListener('input', async function() {
//    const keyword = this.value;
//    if (keyword.length < 1) {
//        suggestionBox.style.display = 'none';
//        return;
//    }
//
//    // Gọi API Search
//    const res = await fetch(`/api/medicines/search?q=${keyword}`);
//    const data = await res.json();
//
//    suggestionBox.innerHTML = '';
//    if (data.length > 0) {
//        suggestionBox.style.display = 'block';
//        data.forEach(med => {
//            // Render từng dòng gợi ý
//            const item = document.createElement('a');
//            item.className = 'list-group-item list-group-item-action';
//            item.innerHTML = `
//                <div class="d-flex justify-content-between">
//                    <strong>${med.name}</strong>
//                    <span class="badge bg-secondary">Tồn: ${med.stock}</span>
//                </div>
//                <small class="text-muted">${med.id} - ${med.price} đ/${med.unit}</small>
//            `;
//
//            // Sự kiện Click chọn
//            item.onclick = () => {
//                selectMedicine(med);
//            };
//            suggestionBox.appendChild(item);
//        });
//    } else {
//        suggestionBox.style.display = 'none';
//    }
//});
//
//function selectMedicine(med) {
//    currentSelectedMed = med;
//    txtSearch.value = med.name;
//    document.getElementById('lblUnit').innerText = med.unit;
//    document.getElementById('lblStock').innerText = `(Tồn kho: ${med.stock})`;
//    document.getElementById('txtUsage').value = med.usage || ""; // Tự điền cách dùng
//    document.getElementById('txtQuantity').value = 1;
//    document.getElementById('txtQuantity').max = med.stock; // Set max cho input number
//
//    suggestionBox.style.display = 'none'; // Ẩn gợi ý
//}
//
//// STT 2 (Tiếp): Btn_Them_Click
//function addMedicineToGrid() {
//    if (!currentSelectedMed) {
//        alert("Vui lòng chọn thuốc từ danh sách gợi ý!");
//        return;
//    }
//
//    const qty = parseInt(document.getElementById('txtQuantity').value);
//    const usage = document.getElementById('txtUsage').value;
//    const stock = currentSelectedMed.stock;
//
//    // Validate
//    if (qty <= 0) { alert("Số lượng phải > 0"); return; }
//    if (qty > stock) { alert(`Vượt quá tồn kho! (Tối đa: ${stock})`); return; }
//    if (!usage) { alert("Vui lòng nhập liều dùng!"); return; }
//
//    // Check trùng: Nếu đã có thuốc này trong list -> cộng dồn
//    const existingIndex = prescriptionList.findIndex(m => m.id === currentSelectedMed.id);
//    if (existingIndex >= 0) {
//        const newTotal = prescriptionList[existingIndex].quantity + qty;
//        if (newTotal > stock) {
//            alert(`Tổng số lượng (${newTotal}) vượt quá tồn kho (${stock})!`);
//            return;
//        }
//        prescriptionList[existingIndex].quantity = newTotal;
//        prescriptionList[existingIndex].usage = usage; // Cập nhật lại cách dùng mới nhất
//    } else {
//        // Thêm mới
//        prescriptionList.push({
//            id: currentSelectedMed.id,
//            name: currentSelectedMed.name,
//            unit: currentSelectedMed.unit,
//            price: currentSelectedMed.price,
//            quantity: qty,
//            usage: usage
//        });
//    }
//
//    renderPrescriptionTable();
//    resetInputSection();
//}
//
//function resetInputSection() {
//    txtSearch.value = '';
//    document.getElementById('txtQuantity').value = 1;
//    document.getElementById('txtUsage').value = '';
//    document.getElementById('lblStock').innerText = '';
//    currentSelectedMed = null;
//    txtSearch.focus();
//}
//
//// Render Table & STT 3: Xoa_Click
//function renderPrescriptionTable() {
//    const tbody = document.getElementById('tblPrescriptionBody');
//    tbody.innerHTML = '';
//
//    prescriptionList.forEach((item, index) => {
//        const tr = document.createElement('tr');
//        tr.innerHTML = `
//            <td class="text-center">${index + 1}</td>
//            <td>${item.name}</td>
//            <td class="text-center">${item.unit}</td>
//            <td class="text-center fw-bold">${item.quantity}</td>
//            <td class="text-end">${formatCurrency(item.price)}</td>
//            <td>${item.usage}</td>
//            <td class="text-center">
//                <button class="btn btn-sm btn-outline-danger border-0" onclick="removeMedicine(${index})">
//                    <i class="bi bi-x-lg"></i>
//                </button>
//            </td>
//        `;
//        tbody.appendChild(tr);
//    });
//}
//
//function removeMedicine(index) {
//    prescriptionList.splice(index, 1);
//    renderPrescriptionTable();
//}
//
//// STT 3 (Cuối): Btn_XacNhan_Click
//function confirmPrescription() {
//    // Đóng Modal (Bootstrap 5 API)
//    const modalEl = document.getElementById('prescriptionModal');
//    const modal = bootstrap.Modal.getInstance(modalEl);
//    modal.hide();
//
//    // Cập nhật giao diện bên ngoài (Optional)
//    const btnOpen = document.querySelector('.btn-prescribe'); // Nút Kê đơn ở màn hình chính
//    if (prescriptionList.length > 0) {
//        btnOpen.innerText = `KÊ ĐƠN THUỐC (${prescriptionList.length} thuốc)`;
//        btnOpen.classList.remove('btn-outline-info');
//        btnOpen.classList.add('btn-info', 'text-white');
//    } else {
//        btnOpen.innerText = "KÊ ĐƠN THUỐC";
//    }
//}