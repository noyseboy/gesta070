document.addEventListener('DOMContentLoaded', function() {
    const days = document.querySelectorAll('.day');
    const selectedDateInput = document.getElementById('selected_date');
    const selectedTimeInput = document.getElementById('selected_time');
    const selectedDetails = document.getElementById('selected_details');
    const verificarHorarioButton = document.getElementById('verificar_horario');

    let selectedDate = '';

    days.forEach(day => {
        day.addEventListener('click', function() {
            days.forEach(d => d.classList.remove('selected'));
            day.classList.add('selected');
            selectedDate = day.getAttribute('data-date');
            selectedDateInput.value = selectedDate;
            selectedDetails.innerText = `Data selecionada: ${selectedDate}`;
            
            // Atualiza os horários disponíveis
            updateAvailableTimes(selectedDate);
        });
    });

    function updateAvailableTimes(date) {
        const timeSelect = document.getElementById('selected_time');
        const options = timeSelect.options;

        for (let i = 1; i < options.length; i++) {
            options[i].style.display = 'block'; // Reset all options to visible
        }

        const occupiedTimes = agendamentos_prova_teorica
            .filter(a => a.data_hora.startsWith(date))
            .map(a => a.data_hora.split(' ')[1]);

        for (let i = 1; i < options.length; i++) {
            if (occupiedTimes.includes(options[i].value)) {
                options[i].style.display = 'none';
            }
        }
    }

    verificarHorarioButton.addEventListener('click', function() {
        const selectedTime = selectedTimeInput.value;
        if (selectedDate && selectedTime) {
            selectedDetails.innerText = `Data selecionada: ${selectedDate} | Horário selecionado: ${selectedTime}`;
        } else {
            selectedDetails.innerText = 'Nenhuma data ou horário selecionado.';
        }
    });
});
