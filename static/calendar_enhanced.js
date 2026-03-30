// Enhanced calendar initialization script
document.addEventListener('DOMContentLoaded', function() {
    // Handle calendar collapse/expand
    const calendarCollapseBtn = document.querySelector('[data-bs-target="#calendarBody"]');
    const calendarArrow = document.getElementById('calendarArrow');

    if (calendarCollapseBtn && calendarArrow) {
        calendarCollapseBtn.addEventListener('click', function() {
            const isExpanded = this.getAttribute('aria-expanded') === 'true';
            calendarArrow.style.transform = isExpanded ? 'rotate(180deg)' : 'rotate(0deg)';
            calendarArrow.style.transition = 'transform 0.3s ease';
        });
    }

    // Initialize FullCalendar with project tasks
    const calendarEl = document.getElementById('project-calendar');
    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        locale: 'fr',
        firstDay: 1, // Monday first day of week
        headerToolbar: false, // We're using custom toolbar
        height: 'auto',
        contentHeight: 'auto',
        aspectRatio: 1.5,
        events: function(info, successCallback, failureCallback) {
            // Get tasks from Gantt and convert to calendar events
            const tasks = gantt.getTaskByTime();
            const events = tasks.map(task => ({
                id: task.id,
                title: task.text,
                start: task.start_date,
                end: task.end_date,
                backgroundColor: task.progress >= 1 ? '#28a745' : 
                               (new Date(task.end_date) < new Date() ? '#dc3545' : '#0d6efd'),
                borderColor: task.progress >= 1 ? '#28a745' : 
                            (new Date(task.end_date) < new Date() ? '#dc3545' : '#0d6efd')
            }));
            successCallback(events);
        },
        editable: false,
        selectable: true,
        eventClick: function(info) {
            // Navigate to the task in Gantt when clicked
            const taskId = info.event.id;
            gantt.showTask(taskId);
        },
        dateClick: function(info) {
            // Handle date click - add new event
            console.log('Date clicked: ' + info.dateStr);
            // You can open a modal to add event here
        },
        dayCellDidMount: function(info) {
            // Add custom tooltip or styling for specific dates
            if (info.date.toDateString() === new Date().toDateString()) {
                info.el.style.backgroundColor = 'rgba(13, 110, 253, 0.05)';
            }
        }
    });
    calendar.render();

    // Update event count
    function updateEventCount() {
        const events = calendar.getEvents();
        document.getElementById('event-count').textContent = events.length;
    }

    // Custom toolbar controls
    document.getElementById('calendar-today')?.addEventListener('click', function() {
        calendar.today();
        updateMonthYear();
    });

    document.getElementById('calendar-prev')?.addEventListener('click', function() {
        calendar.prev();
        updateMonthYear();
    });

    document.getElementById('calendar-next')?.addEventListener('click', function() {
        calendar.next();
        updateMonthYear();
    });

    // View switching
    document.querySelectorAll('[data-view]').forEach(btn => {
        btn.addEventListener('click', function() {
            const view = this.getAttribute('data-view');
            calendar.changeView(view);

            // Update active state
            document.querySelectorAll('[data-view]').forEach(b => {
                b.classList.remove('active');
            });
            this.classList.add('active');

            updateMonthYear();
        });
    });

    function updateMonthYear() {
        const currentDate = calendar.getDate();
        const monthNames = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin',
                           'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'];
        const monthYear = `${monthNames[currentDate.getMonth()]} ${currentDate.getFullYear()}`;
        document.getElementById('calendar-month-year').textContent = monthYear;
    }

    // Initial update
    calendar.on('datesSet', updateMonthYear);
    calendar.on('eventAdd', updateEventCount);
    calendar.on('eventRemove', updateEventCount);

    // Update calendar when Gantt tasks change
    gantt.attachEvent("onAfterTaskUpdate", function(id, item) {
        calendar.refetchEvents();
        updateEventCount();
    });
    gantt.attachEvent("onAfterTaskAdd", function(id, item) {
        calendar.refetchEvents();
        updateEventCount();
    });
    gantt.attachEvent("onAfterTaskDelete", function(id, item) {
        calendar.refetchEvents();
        updateEventCount();
    });

    updateMonthYear();
    updateEventCount();
});
