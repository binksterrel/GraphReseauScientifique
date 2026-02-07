/**
 * HEADER.JS - Shared Header Component
 * Clean Swiss Minimalist Design
 */

document.addEventListener("DOMContentLoaded", function () {
    const headerContainer = document.getElementById("app-header");
    if (!headerContainer) return;

    const currentPage = window.location.pathname.split("/").pop() || "index.html";

    // Create style element
    const styleEl = document.createElement('style');
    styleEl.textContent = `
        .app-header {
            position: fixed;
            top: 24px;
            left: 50%;
            transform: translateX(-50%);
            width: calc(100% - 48px);
            max-width: 1200px;
            height: 64px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 12px 0 32px;
            z-index: 1000;
            background: rgba(255, 255, 255, 0.7);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.5);
            box-shadow: 
                0 4px 20px -2px rgba(0, 0, 0, 0.05),
                0 0 0 1px rgba(0, 0, 0, 0.05);
            border-radius: 100px;
            transition: all 0.3s ease;
        }

        .header-logo {
            font-family: 'Inter', sans-serif;
            font-size: 14px;
            font-weight: 700;
            letter-spacing: -0.01em;
            color: #111;
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .header-logo::before {
            content: '';
            display: block;
            width: 8px;
            height: 8px;
            background: #111;
            border-radius: 50%;
            box-shadow: 0 0 10px rgba(0,0,0,0.2);
        }

        .header-nav {
            display: flex;
            gap: 6px;
            background: rgba(0,0,0,0.03);
            padding: 4px;
            border-radius: 16px;
        }

        .nav-link {
            font-family: 'Inter', sans-serif;
            font-size: 13px;
            font-weight: 500;
            color: #666;
            text-decoration: none;
            padding: 8px 16px;
            border-radius: 12px;
            transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
            position: relative;
            z-index: 1;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .nav-link:hover {
            color: #111;
            background: rgba(255,255,255,0.5);
        }

        .nav-link.active {
            color: #fff;
            background: #111;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            font-weight: 600;
        }

        /* Hide icons on Desktop */
        .nav-link svg {
            display: none;
        }

        /* Mobile Menu Button */
        .mobile-menu-btn {
            display: none;
            background: none;
            border: none;
            padding: 12px;
            cursor: pointer;
            font-size: 24px;
            line-height: 1;
        }

        /* Mobile Styles - Bottom Dock Design (App-Like) */
        @media (max-width: 768px) {
            /* ... existing styles ... */
            
            /* Dock Items */
            .nav-link {
                flex: 1;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                height: 100%;
                padding: 0;
                background: transparent !important;
                border-radius: 0;
                color: #999;
                font-size: 10px;
                font-weight: 500;
                gap: 4px;
                transition: all 0.2s cubic-bezier(0.25, 1, 0.5, 1);
            }
            
            .nav-link svg {
                display: block; /* Show icons on mobile */
                width: 24px;
                height: 24px;
                stroke-width: 2px;
                transition: all 0.2s;
            }
            .app-header {
                top: 0;
                left: 0 !important; /* Force left 0 to override desktop 50% */
                right: 0;
                width: 100%;
                max-width: 100%;
                height: 60px;
                transform: none !important; /* CRITICAL: Remove desktop transform to fix positioning */
                border: none;
                background: transparent; /* Transparent header */
                backdrop-filter: none;
                -webkit-backdrop-filter: none;
                box-shadow: none;
                border-radius: 0;
                padding: 0 20px;
                pointer-events: none; /* Let clicks pass through except on logo */
                justify-content: center; /* Center logo */
            }
            
            .header-logo {
                font-size: 14px;
                pointer-events: auto;
                background: rgba(255, 255, 255, 0.8);
                padding: 8px 16px;
                border-radius: 100px;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.4);
                box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            }
            
            .header-logo::before {
                display: block; /* Show dot */
                width: 6px;
                height: 6px;
                margin-right: 8px; /* Add spacing */
            }
            
            /* Hide Burger */
            .mobile-menu-btn {
                display: none !important;
            }
            
            /* Bottom Dock Navigation */
            .header-nav {
                position: fixed;
                bottom: 24px;
                left: 50%;
                transform: translateX(-50%);
                width: calc(100% - 48px);
                max-width: 360px;
                height: 64px;
                background: rgba(255, 255, 255, 0.85); /* Glass look */
                backdrop-filter: blur(40px); /* Heavy blur */
                -webkit-backdrop-filter: blur(40px);
                border: 1px solid rgba(255, 255, 255, 0.5);
                box-shadow: 
                    0 10px 30px -10px rgba(0, 0, 0, 0.15),
                    0 4px 10px rgba(0, 0, 0, 0.05),
                    inset 0 1px 0 rgba(255, 255, 255, 0.5);
                border-radius: 20px;
                padding: 0 8px;
                display: flex;
                flex-direction: row;
                justify-content: space-between; /* Spread items */
                align-items: center;
                gap: 0;
                z-index: 2000;
                pointer-events: auto;
            }
            
            /* Dock Items */
            .nav-link {
                flex: 1;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                height: 100%;
                padding: 0;
                background: transparent !important;
                border-radius: 0;
                color: #999;
                font-size: 10px;
                font-weight: 500;
                gap: 4px;
                transition: all 0.2s cubic-bezier(0.25, 1, 0.5, 1);
            }
            
            .nav-link svg {
                width: 24px;
                height: 24px;
                stroke-width: 2px;
                transition: all 0.2s;
            }
            
            .nav-text {
                display: block; /* Show labels */
                transform: translateY(0);
                opacity: 0.8;
            }
            
            /* Active State */
            .nav-link.active {
                color: #111;
                background: transparent !important;
                box-shadow: none !important;
            }
            
            .nav-link.active svg {
                stroke-width: 2.5px;
                transform: translateY(-2px);
            }
            
            .nav-link:active {
                transform: scale(0.9);
                opacity: 0.7;
            }
            
            /* Hide Backdrop */
            .menu-backdrop {
                display: none;
            }
        }
    `;
    document.head.appendChild(styleEl);

    // Create header HTML
    const headerDiv = document.createElement('div');
    headerDiv.className = 'app-header';
    
    // Logo
    const logo = document.createElement('a');
    logo.href = 'index.html';
    logo.className = 'header-logo';
    logo.textContent = 'EPISTEME NETWORK';
    
    // Mobile menu button (Burger)
    const menuBtn = document.createElement('button');
    menuBtn.className = 'mobile-menu-btn';
    menuBtn.setAttribute('aria-label', 'Menu');
    
    // Create 3 lines for burger icon
    for(let i=0; i<3; i++) {
        const line = document.createElement('span');
        line.className = 'burger-line';
        menuBtn.appendChild(line);
    }
    
    // Create backdrop for mobile menu
    const backdrop = document.createElement('div');
    backdrop.className = 'menu-backdrop';
    document.body.appendChild(backdrop);

    menuBtn.onclick = function() {
        const nav = document.getElementById('header-nav');
        const isOpen = nav.classList.toggle('open');
        menuBtn.classList.toggle('active');
        backdrop.classList.toggle('active');
        
        // Lock body scroll
        if (isOpen) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = '';
        }
    };
    
    // Close menu on backdrop click
    backdrop.onclick = function() {
        const nav = document.getElementById('header-nav');
        nav.classList.remove('open');
        menuBtn.classList.remove('active');
        backdrop.classList.remove('active');
        document.body.style.overflow = '';
    };
    
    // Navigation
    const nav = document.createElement('nav');
    nav.className = 'header-nav';
    nav.id = 'header-nav';
    
    const links = [
        { 
            href: 'index.html', 
            text: 'Index',
            icon: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>`
        },
        { 
            href: 'graph.html', 
            text: 'Graphe',
            icon: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"></path><path d="M2 12h20"></path></svg>`
        },
        { 
            href: 'top.html', 
            text: 'Top 100',
            icon: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>`
        },
        { 
            href: 'small_world.html', 
            text: 'Analyse',
            icon: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>`
        },
        { 
            href: 'about.html', 
            text: 'Info',
            icon: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M12 16v-4"></path><path d="M12 8h.01"></path></svg>`
        }
    ];
    
    links.forEach(link => {
        const a = document.createElement('a');
        a.href = link.href;
        a.className = 'nav-link';
        // Add Icon and Text
        a.innerHTML = `${link.icon}<span class="nav-text">${link.text}</span>`;
        
        // Check if active
        if (currentPage === link.href || (currentPage === '' && link.href === 'index.html')) {
            a.classList.add('active');
        }
        
        // No close menu logic needed anymore as it's always visible
        
        nav.appendChild(a);
    });
    
    // Assemble header
    headerDiv.appendChild(logo);
    headerDiv.appendChild(menuBtn);
    headerDiv.appendChild(nav);
    
    headerContainer.appendChild(headerDiv);
    
    // Dispatch custom event to notify that header is ready
    window.dispatchEvent(new CustomEvent('headerLoaded'));
});
