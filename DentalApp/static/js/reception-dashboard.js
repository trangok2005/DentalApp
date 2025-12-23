//xủy lý hủy
document.addEventListener('DOMContentLoaded', function() {
    
    // HTML theo ID
    const modalPatientName = document.getElementById('modalPatientName'); 
    const modalApptId = document.getElementById('modalApptId');

//     Nếu không tìm thấy thẻ thì báo lỗi
//    if (!modalPatientName) {
//        console.error("LỖI: Không tìm thấy thẻ có id='modalPatientName' trong HTML!");
//        return;
//    }

    // 2. Lấy các nút hủy
    const cancelButtons = document.querySelectorAll('.js-cancel-btn');
    const cancelModalEl = document.getElementById('cancelModal');
    
    // Nếu dùng Bootstrap 5
    if (cancelModalEl) {
        const cancelModal = new bootstrap.Modal(cancelModalEl);

        cancelButtons.forEach(button => {
            button.addEventListener('click', function() {
                const id = this.getAttribute('data-id');   // Lấy ID từ nút
                const name = this.getAttribute('data-name'); // Lấy Tên từ nút

                // --- DÒNG GÂY LỖI CỦA BẠN LÀ Ở ĐÂY ---
                // Nếu modalPatientName là null thì dòng dưới sẽ báo lỗi TypeError
                modalPatientName.textContent = name; 
                
                if(modalApptId) modalApptId.value = id;

                cancelModal.show();
            });
        });
    }
});

//Thanh toán
document.addEventListener('DOMContentLoaded', function() {

   // --- PHẦN 1: CẤU HÌNH BIẾN ---
    const paymentTabBtn = document.getElementById('payment-tab');
    const appointmentTabBtn = document.getElementById('appointment-tab');
    const invoiceTableBody = document.getElementById('invoice-table-body');
    let isInvoiceLoaded = false;

    // Key để lưu vào bộ nhớ trình duyệt
    const STORAGE_KEY = 'active_dashboard_tab';

    // --- PHẦN 2: LOGIC GHI NHỚ TAB ---

    // 2.1. Hàm lưu tab hiện tại mỗi khi người dùng bấm chuyển
    const tabEls = document.querySelectorAll('button[data-bs-toggle="tab"]');
    tabEls.forEach(tabEl => {
        tabEl.addEventListener('shown.bs.tab', function (event) {
            // Lưu ID của nút tab đang active (VD: 'payment-tab' hoặc 'appointment-tab')
            localStorage.setItem(STORAGE_KEY, event.target.id);

            // Nếu bấm sang tab thanh toán thì gọi hàm load data
            if (event.target.id === 'payment-tab') {
                if (!isInvoiceLoaded) {
                    loadInvoices();
                }
            }
        });
    });

    // 2.2. Hàm khôi phục tab khi trang vừa load xong
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
        // Nếu chưa lưu gì cả (lần đầu vào), mặc định load tab Lịch hẹn
        // Không cần làm gì vì HTML đã set 'active' cho tab lịch hẹn rồi
    }

    // 3 Hàm gọi API
    async function loadInvoices() {
        const tbody = document.getElementById('invoice-table-body');

        // 1. Lấy giá trị bộ lọc hiện tại trên giao diện
        const date = document.querySelector('input[name="date"]').value;
        const doctor = document.querySelector('select[name="doctor_id"]').value;
        const keyword = document.querySelector('input[name="keyword"]').value;

        // 2. Tạo URL với tham số
        const url = `/api/get-invoices?date=${date}&doctor_id=${doctor}&keyword=${keyword}`;

        try {
            const res = await fetch(url);
            const html = await res.text();

            // 3. Đổ HTML vào bảng
            tbody.innerHTML = html;
            isInvoiceLoaded = true; // Đánh dấu đã load

        } catch (error) {
            console.error(error);
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-danger">Lỗi tải dữ liệu</td></tr>';
        }
    }

    // (Tùy chọn) Nếu người dùng bấm nút "Lọc", ta cần reset lại trạng thái để tab Payment load lại dữ liệu mới
    const filterForm = document.querySelector('form'); // Form lọc
    if(filterForm){
        filterForm.addEventListener('submit', function(){
            isInvoiceLoaded = false;
        });
    }
});
