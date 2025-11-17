// Banner de cookies para el sitio web
(function() {
    'use strict';

    // Crear el banner de cookies
    function createCookieBanner() {
        const banner = document.createElement('div');
        banner.id = 'cookie-banner';
        banner.innerHTML = `
            <div style="
                position: fixed;
                bottom: 0;
                left: 0;
                right: 0;
                background: rgba(0, 0, 0, 0.9);
                color: white;
                padding: 8px 20px;
                text-align: center;
                font-family: 'Segoe UI', sans-serif;
                font-size: 12px;
                z-index: 10000;
                box-shadow: 0 -2px 10px rgba(0,0,0,0.3);
                border-top: 2px solid #4CAF50;
            ">
                <p style="margin: 0 0 10px 0;">
                    Este sitio web utiliza cookies para mejorar tu experiencia. Al continuar navegando, aceptas nuestro uso de cookies.
                    <a href="../PoliticaPrivacidad.html" style="color: #4CAF50; text-decoration: underline;" target="_blank">Más información</a>
                </p>
                <button id="accept-cookies" style="
                    background: #4CAF50;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-weight: bold;
                    margin-right: 10px;
                ">Aceptar</button>
                <button id="reject-cookies" style="
                    background: #666;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-weight: bold;
                ">Rechazar</button>
            </div>
        `;
        document.body.appendChild(banner);

        // Funcionalidad de los botones
        document.getElementById('accept-cookies').addEventListener('click', function() {
            localStorage.setItem('cookiesAccepted', 'true');
            banner.style.display = 'none';
        });

        document.getElementById('reject-cookies').addEventListener('click', function() {
            localStorage.setItem('cookiesAccepted', 'false');
            banner.style.display = 'none';
        });
    }

    // Verificar si ya se aceptaron las cookies
    function checkCookieConsent() {
        const accepted = localStorage.getItem('cookiesAccepted');
        if (accepted === null) {
            createCookieBanner();
        }
    }

    // Inicializar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', checkCookieConsent);
    } else {
        checkCookieConsent();
    }
})();
