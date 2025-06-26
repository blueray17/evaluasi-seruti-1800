// ==UserScript==
// @name         BPS Data Token Extractor
// @namespace    http://tampermonkey.net/
// @version      1.1
// @description  Extract and send CSRF, XSRF, and Cookies from BPS SERUTI to local server
// @author       ChatGPT
// @match        https://webapps.bps.go.id/olah/seruti/query*
// @grant        none
// @icon         https://www.google.com/s2/favicons?sz=64&domain=go.id
// ==/UserScript==

(function() {
    'use strict';

    // Fungsi membuat tombol UI
    function createButton() {
        const btn = document.createElement('button');
        btn.id = 'token-btn';
        btn.textContent = '🔐 Kirim Token ke Localhost';
        Object.assign(btn.style, {
            position: 'fixed',
            bottom: '20px',
            right: '20px',
            padding: '10px 15px',
            background: '#2c3e50',
            color: '#fff',
            border: 'none',
            borderRadius: '5px',
            cursor: 'pointer',
            zIndex: 9999,
            fontWeight: 'bold',
            boxShadow: '0 2px 10px rgba(0,0,0,0.2)'
        });
        document.body.appendChild(btn);
        return btn;
    }

    // Ambil token dari cookie
    function getCookie(name) {
        const match = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'));
        return match ? decodeURIComponent(match[1]) : '';
    }

    // Fungsi utama ambil token
    function fetchTokens() {
        const cookies = document.cookie;
        //const xsrfToken = getCookie('XSRF-TOKEN');

        const xsrfMeta = document.querySelector('meta[name="xsrf-token"]');
        const xsrfToken = xsrfMeta ? xsrfMeta.content : getCookie('xsrftoken') || getCookie('XSRF-TOKEN') || '';

        const csrfMeta = document.querySelector('meta[name="csrf-token"]');
        const csrfToken = csrfMeta ? csrfMeta.content : getCookie('csrftoken') || getCookie('CSRF-TOKEN') || '';

        return {
            cookies,
            xsrfToken,
            csrfToken
        };
    }

    // Tambahkan tombol
    const button = createButton();

    // Tambahkan event listener ke tombol
    button.addEventListener('click', () => {
        const { cookies, xsrfToken, csrfToken } = fetchTokens();

        const payload = {
            CSRF_TOKEN: csrfToken,
            XSRF_TOKEN: xsrfToken,
            COOKIES: cookies
        };

        console.log("📦 Payload yang dikirim:", payload);

        fetch('http://localhost:8000/update-env', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        })
        .then(res => {
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return res.json();
        })
        .then(data => {
            alert('✅ Token berhasil dikirim:\n' + JSON.stringify(payload, null, 2));
            console.log('✅ Server response:', data);
        })
        .catch(err => {
            alert('❌ Gagal kirim token:\n' + err.message);
            console.error('❌ Error:', err);
        });
    });
})();
