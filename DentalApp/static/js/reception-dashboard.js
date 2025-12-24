//xủy lý hủy
document.addEventListener('DOMContentLoaded', function() {
    
    // HTML theo ID
    const modalPatientName = document.getElementById('modalPatientName'); 
    const modalApptId = document.getElementById('modalApptId');

    //  Lấy các nút hủy
    const cancelButtons = document.querySelectorAll('.js-cancel-btn');
    const cancelModalEl = document.getElementById('cancelModal');
    
    //  Bootstrap 5
    if (cancelModalEl) {
        const cancelModal = new bootstrap.Modal(cancelModalEl);

        cancelButtons.forEach(button => {
            button.addEventListener('click', function() {
                const id = this.getAttribute('data-id');   // Lấy ID từ nút
                const name = this.getAttribute('data-name'); // Lấy Tên từ nút

                modalPatientName.textContent = name; 
                
                if(modalApptId) modalApptId.value = id;

                cancelModal.show();
            });
        });
    }
});

//STORAGE_KEY
document.addEventListener('DOMContentLoaded', function() {
   //
    const paymentTabBtn = document.getElementById('payment-tab');
    const appointmentTabBtn = document.getElementById('appointment-tab');
    const invoiceTableBody = document.getElementById('invoice-table-body');
    let isInvoiceLoaded = false;

    // Key để lưu vào bộ nhớ trình duyệt
    const STORAGE_KEY = 'active_dashboard_tab';

    // LOGIC GHI NHỚ TAB ---

    //Hàm lưu tab hiện tại mỗi khi người dùng bấm chuyển
    const tabEls = document.querySelectorAll('button[data-bs-toggle="tab"]');
    tabEls.forEach(tabEl => {
        tabEl.addEventListener('shown.bs.tab', function (event) {
            // Lưu ID của nút tab đang active
            localStorage.setItem(STORAGE_KEY, event.target.id);

            // Nếu bấm sang tab thanh toán thì gọi hàm load data
            if (event.target.id === 'payment-tab') {
                if (!isInvoiceLoaded) {
                    loadInvoices();
                }
            }
        });
    });
}
//Hàm khôi phục tab khi trang vừa load xong
const savedTabId = localStorage.getItem(STORAGE_KEY);
if (savedTabId) {
    // Tìm nút tab đã lưu
    const savedTabBtn = document.getElementById(savedTabId);
    if (savedTabBtn) {
        // Dùng Bootstrap API để bật tab đó lên
        const tabInstance = new bootstrap.Tab(savedTabBtn);
        tabInstance.show();
    }
} else {
    // mặt dinh là lich hẹn
}

//gọi API
async function loadInvoices() {
    const tbody = document.getElementById('invoice-table-body');

    // Lấy giá trị bộ lọc hiện tại trên giao diện
    const date = document.querySelector('input[name="date"]').value;
    const doctor = document.querySelector('select[name="doctor_id"]').value;
    const keyword = document.querySelector('input[name="keyword"]').value;

    // Tạo URL với tham số
    const url = `/api/get-invoices?date=${date}&doctor_id=${doctor}&keyword=${keyword}`;

    try {
        const res = await fetch(url);
        const html = await res.text();

        // Đổ HTML vào bảng
        tbody.innerHTML = html;
        isInvoiceLoaded = true; // Đánh dấu đã load

    } catch (error) {
        console.error(error);
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-danger">Lỗi tải dữ liệu</td></tr>';
    }
}

    // lọc load dl mới
    const filterForm = document.querySelector('form');
    if(filterForm){
        filterForm.addEventListener('submit', function(){
            isInvoiceLoaded = false;
        });
    }
});
