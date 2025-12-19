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