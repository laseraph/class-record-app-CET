// Main JavaScript for Class Record App

// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
    // Enable Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Enable Bootstrap popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 5000);
    });

    // File upload preview
    const fileInput = document.querySelector('input[type="file"]');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            const fileName = this.files[0] ? this.files[0].name : 'No file chosen';
            const fileLabel = this.nextElementSibling || this.parentElement.querySelector('.file-label');
            if (fileLabel) {
                fileLabel.textContent = fileName;
            }
        });
    }

    // Confirm before delete
    const deleteForms = document.querySelectorAll('form[onsubmit="return confirmDelete()"]');
    deleteForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });

    // Select student in grade entry
    const studentSelect = document.getElementById('studentSelect');
    if (studentSelect) {
        studentSelect.addEventListener('change', function() {
            updateGradeFields();
        });
    }
});

// Update grade fields when student changes
function updateGradeFields() {
    const studentId = document.getElementById('studentSelect').value;
    // In a real implementation, this would fetch the student's grades via AJAX
    // For now, just update the UI
    console.log('Selected student:', studentId);
}

// Select student from table
function selectStudent(studentId) {
    const select = document.getElementById('studentSelect');
    if (select) {
        select.value = studentId;
        updateGradeFields();
    }
}

// Confirm delete function
function confirmDelete() {
    return confirm('Are you sure you want to delete this item? This action cannot be undone.');
}

// Format number as percentage
function formatPercentage(value) {
    return value.toFixed(1) + '%';
}

// Format grade
function formatGrade(value) {
    if (value === null || value === undefined) return 'N/A';
    return value.toFixed(2);
}
