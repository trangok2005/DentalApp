
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
    tooltipTriggerList.forEach(item => {
        new bootstrap.Tooltip(item)
    })
