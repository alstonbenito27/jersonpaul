document.addEventListener('DOMContentLoaded', function () {
    var calendarEl = document.getElementById('calendar');

    // Get availability data from the server (rendered by Flask)
    var availability = JSON.parse('{{ availability|tojson }}');

    var events = availability.map(function (day) {
        return {
            title: day.status,  // 'available' or 'busy'
            start: day.date
        };
    });

    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        events: events,
        dateClick: function (info) {
            if (info.event && info.event.title === 'available') {
                window.location.href = '/book_service?date=' + info.dateStr;
            }
        }
    });

    calendar.render();
});
