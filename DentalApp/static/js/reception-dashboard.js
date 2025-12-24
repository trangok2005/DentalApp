// ---XỬ LÝ MODAL HỦY LỊCH HẸN ---
document.addEventListener('DOMContentLoaded', function() {

    // HTML theo ID
    const modalPatientName = document.getElementById('modalPatientName');
    const modalApptId = document.getElementById('modalApptId');

    // Lấy các nút hủy
    const cancelButtons = document.querySelectorAll('.js-cancel-btn');
    const cancelModalEl = document.getElementById('cancelModal');

    // Bootstrap 5 Logic
    if (cancelModalEl) {
        const cancelModal = new bootstrap.Modal(cancelModalEl);

        cancelButtons.forEach(button => {
            button.addEventListener('click', function() {
                const id = this.getAttribute('data-id');
                const name = this.getAttribute('data-name');

                if(modalPatientName) modalPatientName.textContent = name;
                if(modalApptId) modalApptId.value = id;

                cancelModal.show();
            });
        });
    }

});


// --- XỬ LÝ TAB VÀ LOAD HÓA ĐƠN ---
document.addEventListener('DOMContentLoaded', function() {

    const paymentTabBtn = document.getElementById('payment-tab');
    const appointmentTabBtn = document.getElementById('appointment-tab');
    const invoiceTableBody = document.getElementById('invoice-table-body');
    let isInvoiceLoaded = false;

    // Key để lưu vào bộ nhớ trình duyệt
    const STORAGE_KEY = 'active_dashboard_tab';

    // GHI NHỚ TAB
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

    // khôi phục tab khi trang vừa load xong
    const savedTabId = localStorage.getItem(STORAGE_KEY);
    if (savedTabId) {
        const savedTabBtn = document.getElementById(savedTabId);
        if (savedTabBtn) {
            const tabInstance = new bootstrap.Tab(savedTabBtn);
            tabInstance.show();

            // Nếu tab được lưu là tab thanh toán, load luôn dữ liệu
            if (savedTabId === 'payment-tab') {
                 loadInvoices();
            }
        }
    }

    // \Hàm gọi API (Đã sửa lỗi thiếu ngoặc)
    async function loadInvoices() {
        const tbody = document.getElementById('invoice-table-body');
        if (!tbody) return; // Kiểm tra null cho an toàn

        // Lấy giá trị bộ lọc
        const dateInput = document.querySelector('input[name="date"]');
        const doctorInput = document.querySelector('select[name="doctor_id"]');
        const keywordInput = document.querySelector('input[name="keyword"]');

        const date = dateInput ? dateInput.value : '';
        const doctor = doctorInput ? doctorInput.value : '';
        const keyword = keywordInput ? keywordInput.value : '';

        // Tạo URL
        const url = `/api/get-invoices?date=${date}&doctor_id=${doctor}&keyword=${keyword}`;

        try {
            const res = await fetch(url);
            const html = await res.text();

            // Đổ HTML vào bảng
            tbody.innerHTML = html;
            isInvoiceLoaded = true;

        } catch (error) {
            console.error(error);
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-danger">Lỗi tải dữ liệu</td></tr>';
        }

        // Sự kiện submit form lọc (để reset biến isInvoiceLoaded)
        const filterForm = document.querySelector('form'); // Nên đặt ID cụ thể cho form nếu có nhiều form
        if(filterForm){
            filterForm.addEventListener('submit', function(){
                isInvoiceLoaded = false;
            });
        }
    }

});