function deleteNote(button) {
    const listItem = button.closest('.list-group-item');
    const noteId = listItem.getAttribute('data-note-id');
    
    console.log('🔄 Attempting to delete note:', noteId);
    console.log('🔍 Button parent:', button.parentNode);
    console.log('📋 List item:', listItem);

    if (!noteId) {
        alert('Error: Could not find note ID');
        return;
    }

    fetch('/delete-note', {
        method: "POST",
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ noteId: noteId })
    })
    .then(response => {
        console.log('📡 Response status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('📦 Response data:', data);
        if (data.success) {
            listItem.remove();
            console.log('✅ Note deleted from DOM');
        } else {
            alert('Error: ' + (data.error || 'Failed to delete note'));
        }
    })
    .catch(error => {
        console.error('❌ Fetch error:', error);
        alert('Network error - please try again');
    });
}

// Auto-dismiss flash messages after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
});


function toggleShare(noteId, makePublic) {
    console.log('🔄 Toggling share for note:', noteId, 'Make public:', makePublic);
    
    fetch('/toggle-share', {
        method: "POST",
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
            noteId: noteId,
            public: makePublic 
        })
    })
    .then(response => {
        console.log('📡 Response status:', response.status);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('📦 Response data:', data);
        if (data.success) {
            // Find and update all buttons for this note
            const buttons = document.querySelectorAll(`button[onclick*="toggleShare(${noteId},"]`);
            buttons.forEach(button => {
                if (makePublic) {
                    // Change to Unshare button
                    button.classList.remove('share-btn');
                    button.classList.add('unshare-btn');
                    button.textContent = '🔒 Unshare';
                    button.onclick = function() { toggleShare(noteId, false); };
                } else {
                    // Change to Share button
                    button.classList.remove('unshare-btn');
                    button.classList.add('share-btn');
                    button.textContent = '🔓 Share';
                    button.onclick = function() { toggleShare(noteId, true); };
                }
            });
            
            // Show success message
            const alertDiv = document.createElement('div');
            alertDiv.className = 'alert alert-success alert-dismissible fade show';
            alertDiv.innerHTML = `
                Note sharing updated successfully!
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            document.querySelector('.container').insertBefore(alertDiv, document.querySelector('.container').firstChild);
            
            // Auto remove after 3 seconds
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.remove();
                }
            }, 3000);
            
        } else {
            alert('Error: ' + (data.error || 'Failed to update share status'));
        }
    })
    .catch(error => {
        console.error('❌ Fetch error:', error);
        alert('Network error - please check console for details');
    });
}

// Add these functions to your existing index.js

function deleteStudent(studentId) {
    if (!confirm('Are you sure you want to delete this student profile? This action cannot be undone.')) {
        return;
    }
    
    fetch('/delete-student', {
        method: "POST",
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ studentId: studentId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const studentCard = document.querySelector(`[data-student-id="${studentId}"]`);
            if (studentCard) {
                studentCard.style.opacity = '0.5';
                setTimeout(() => {
                    studentCard.remove();
                    showFlashMessage('Student profile deleted successfully!', 'success');
                }, 300);
            }
        } else {
            alert('Error: ' + (data.error || 'Failed to delete student profile'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Network error - please try again');
    });
}

function deleteTeacher(teacherId) {
    if (!confirm('Are you sure you want to delete this teacher profile? This action cannot be undone.')) {
        return;
    }
    
    fetch('/delete-teacher', {
        method: "POST",
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ teacherId: teacherId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const teacherCard = document.querySelector(`[data-teacher-id="${teacherId}"]`);
            if (teacherCard) {
                teacherCard.style.opacity = '0.5';
                setTimeout(() => {
                    teacherCard.remove();
                    showFlashMessage('Teacher profile deleted successfully!', 'success');
                }, 300);
            }
        } else {
            alert('Error: ' + (data.error || 'Failed to delete teacher profile'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Network error - please try again');
    });
}