// Update dashboard stats
function updateDashboard() {
    fetch('/api/dashboard')
        .then(response => response.json())
        .then(data => {
            document.getElementById('contacts-count').textContent = data.contacts;
            document.getElementById('providers-count').textContent = data.providers;
            document.getElementById('projects-count').textContent = data.active_projects;
            document.getElementById('budget-total').textContent = '$' + data.total_budget.toLocaleString();
        })
        .catch(error => console.error('Error loading dashboard:', error));
}

// Load recent projects
function loadRecentProjects() {
    fetch('/api/projects/recent')
        .then(response => response.json())
        .then(projects => {
            const list = document.getElementById('recent-projects');
            if (list) {
                list.innerHTML = '';
                if (projects.length === 0) {
                    list.innerHTML = '<div class="list-group-item">No projects yet</div>';
                } else {
                    projects.forEach(project => {
                        const statusClass = {
                            'planned': 'warning',
                            'in_progress': 'primary',
                            'completed': 'success'
                        }[project.status] || 'secondary';
                        
                        list.innerHTML += `
                            <a href="/projects/${project.id}" class="list-group-item list-group-item-action d-flex justify-content-between align-items-center">
                                ${project.name}
                                <span class="badge bg-${statusClass}">${project.status.replace('_', ' ')}</span>
                            </a>
                        `;
                    });
                }
            }
        })
        .catch(error => console.error('Error loading projects:', error));
}

// Auto-hide alerts after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
});

// Format currency inputs
document.addEventListener('DOMContentLoaded', function() {
    const currencyInputs = document.querySelectorAll('input[type="number"][step="0.01"]');
    currencyInputs.forEach(input => {
        input.addEventListener('blur', function() {
            if (this.value) {
                this.value = parseFloat(this.value).toFixed(2);
            }
        });
    });
});

// Confirm delete actions
document.addEventListener('DOMContentLoaded', function() {
    const deleteButtons = document.querySelectorAll('.btn-danger[onclick*="confirm"]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item?')) {
                e.preventDefault();
            }
        });
    });
});

// Run when page loads
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('contacts-count')) {
        updateDashboard();
        loadRecentProjects();
    }
    
    // Add active class to current nav item
    const currentLocation = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentLocation) {
            link.classList.add('active');
        }
    });
});