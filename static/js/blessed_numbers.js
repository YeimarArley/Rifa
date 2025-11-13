// static/js/blessed_numbers.js - VERSIÓN SIMPLIFICADA SIN ANIMACIONES

(function() {
    'use strict';

    // Configuración
    const CHECK_INTERVAL = 10000; // 10 segundos

    // Elementos del DOM
    let ticket1 = null;
    let ticket2 = null;

    /**
     * Inicializa los elementos del DOM
     */
    function initDOMElements() {
        // Buscar los dos primeros tickets
        const tickets = document.querySelectorAll('.tickets .ticket');
        
        if (tickets.length >= 2) {
            ticket1 = tickets[0];
            ticket2 = tickets[1];
            
            console.log('✅ Tickets encontrados:', ticket1, ticket2);
            return true;
        } else {
            console.error('❌ No se encontraron suficientes tickets');
            return false;
        }
    }

    /**
     * Actualiza el contenido de un ticket
     */
    function updateTicketContent(ticket, number) {
        if (!ticket) return;

        // Buscar el elemento <p> que contiene el número
        const numberElement = ticket.querySelector('.ticket-content p');
        
        if (numberElement) {
            if (number) {
                // Mostrar número
                numberElement.textContent = number;
                numberElement.style.fontSize = '1.8em';
                numberElement.classList.remove('coming-soon');
            } else {
                // Mostrar PRÓXIMAMENTE
                numberElement.textContent = 'PRÓXIMAMENTE';
                numberElement.style.fontSize = '1em';
                numberElement.classList.add('coming-soon');
            }
            console.log('📝 Ticket actualizado con:', number || 'PRÓXIMAMENTE');
        }
    }

    /**
     * Actualiza el estado de los números benditos
     */
    async function updateBlessedNumbers() {
        try {
            const response = await fetch('/api/blessed_numbers_status');
            
            if (!response.ok) {
                console.warn('⚠️ Error en respuesta API:', response.status);
                // Mostrar PRÓXIMAMENTE si hay error
                updateTicketContent(ticket1, null);
                updateTicketContent(ticket2, null);
                return;
            }

            const data = await response.json();
            console.log('📡 Estado de números benditos:', data);

            // Decidir qué mostrar
            if (data.visible && data.numbers && data.numbers.length > 0) {
                // MOSTRAR NÚMEROS REALES
                console.log('✨ Mostrando números benditos:', data.numbers);
                updateTicketContent(ticket1, data.numbers[0] || null);
                updateTicketContent(ticket2, data.numbers[1] || null);
            } else {
                // MOSTRAR PRÓXIMAMENTE
                console.log('⏳ Mostrando PRÓXIMAMENTE');
                updateTicketContent(ticket1, null);
                updateTicketContent(ticket2, null);
            }

        } catch (error) {
            console.error('❌ Error al obtener números benditos:', error);
            // En caso de error, mostrar PRÓXIMAMENTE
            updateTicketContent(ticket1, null);
            updateTicketContent(ticket2, null);
        }
    }

    /**
     * Inicializa el sistema
     */
    function init() {
        console.log('🚀 Inicializando sistema de números benditos...');

        // Buscar los tickets en el DOM
        if (!initDOMElements()) {
            console.error('💥 No se pudieron inicializar los tickets');
            return;
        }

        // Primera actualización inmediata
        updateBlessedNumbers();

        // Actualizar cada 10 segundos
        setInterval(updateBlessedNumbers, CHECK_INTERVAL);

        console.log('✅ Sistema inicializado correctamente');
    }

    // Ejecutar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();