document.addEventListener('DOMContentLoaded', () => {
    // Initialize Lucide icons
    lucide.createIcons();

    // Authentication State
    let currentUserEmail = localStorage.getItem('inboxpilot_user_email') || null;
    let isAuthenticated = !!currentUserEmail;

    // App State
    let categoriesConfig = [];
    let currentQueue = 'Queries';
    let emailRecords = [];

    // Elements
    const tabButtons = document.querySelectorAll('.nav-item');
    const tabPanes = document.querySelectorAll('.tab-pane');
    const queuesContainer = document.getElementById('sidebar-queues-list');
    const emailsContainer = document.getElementById('emails-container');
    const queueTitle = document.getElementById('queue-title');
    const queueSubtitle = document.getElementById('queue-subtitle');
    const queueCountBadge = document.getElementById('queue-count-badge');
    const searchInput = document.getElementById('email-search-input');
    const runTriageBtn = document.getElementById('run-triage-btn');

    // Sign in form elements
    const signinForm = document.getElementById('signin-form');
    const signinEmailInput = document.getElementById('signin-email-input');
    const ssoGoogleBtn = document.getElementById('sso-google-btn');
    const userAvatar = document.querySelector('.user-avatar');

    // Tab Switching with Authentication Guard
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-tab');
            
            // Lock access to features if not authenticated
            if (!isAuthenticated && targetTab !== 'signin') {
                showToast('🔒 Please sign in with your email first to access workspace features!', 'error');
                switchTab('signin');
                return;
            }

            switchTab(targetTab);
        });
    });

    function switchTab(tabId) {
        tabButtons.forEach(b => {
            if (b.getAttribute('data-tab') === tabId) b.classList.add('active');
            else b.classList.remove('active');
        });
        tabPanes.forEach(p => {
            if (p.id === `tab-${tabId}`) p.classList.add('active');
            else p.classList.remove('active');
        });
    }

    // Handle Sign In Submit
    if (signinForm) {
        signinForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const email = signinEmailInput.value.trim();
            if (email) {
                performLogin(email);
            }
        });
    }

    if (ssoGoogleBtn) {
        ssoGoogleBtn.addEventListener('click', async () => {
            try {
                const res = await fetch('/api/auth/google-url');
                const data = await res.json();
                if (data.url && data.url !== '#') {
                    window.location.href = data.url;
                } else {
                    performLogin('authorized.user@company.com');
                }
            } catch (err) {
                performLogin('authorized.user@company.com');
            }
        });
    }

    function performLogin(email) {
        currentUserEmail = email;
        isAuthenticated = true;
        localStorage.setItem('inboxpilot_user_email', email);
        showToast(`Welcome ${email}! Workspace unlocked.`, 'success');
        
        updateAuthUI();
        loadCategories();
        loadEmails();
        switchTab('dashboard');
    }

    function performLogout() {
        currentUserEmail = null;
        isAuthenticated = false;
        localStorage.removeItem('inboxpilot_user_email');
        emailRecords = [];
        showToast('Signed out successfully. Workspace locked.', 'info');
        
        updateAuthUI();
        switchTab('signin');
    }

    function updateAuthUI() {
        if (userAvatar) {
            if (isAuthenticated) {
                userAvatar.innerHTML = `<button id="signout-header-btn" title="Sign Out (${escapeHtml(currentUserEmail)})" style="background:none; border:none; color:var(--danger); cursor:pointer; font-size:12px; font-weight:bold;"><i data-lucide="log-out"></i></button>`;
                document.getElementById('signout-header-btn').addEventListener('click', performLogout);
            } else {
                userAvatar.innerHTML = `<i data-lucide="shield-check"></i>`;
            }
            lucide.createIcons();
        }

        if (!isAuthenticated) {
            queueTitle.textContent = "Workspace Locked";
            queueSubtitle.textContent = "Authentication Required";
            queueCountBadge.textContent = "0 Emails";
            emailsContainer.innerHTML = `
                <div class="card glass-card" style="text-align:center; padding:50px 20px;">
                    <div style="font-size:36px; margin-bottom:10px;">🔒</div>
                    <h3 style="font-family:var(--font-heading); font-size:20px; margin-bottom:8px;">Access Locked</h3>
                    <p style="color:var(--text-muted); max-width:400px; margin:0 auto 20px auto;">You must sign in with your authorized email address on the Sign In Portal before email feeds and triage tools become accessible.</p>
                    <button class="btn btn-primary" onclick="document.querySelector('[data-tab=signin]').click()" style="margin:0 auto;">Go to Sign In Portal</button>
                </div>
            `;
        }
    }

    // Fetch Categories
    async function loadCategories() {
        if (!isAuthenticated) return;
        try {
            const res = await fetch('/api/categories');
            categoriesConfig = await res.json();
            renderQueuesSidebar();
            renderCategoryManager();
        } catch (err) {
            console.error('Failed to load categories', err);
        }
    }

    // Render Queues Sidebar
    function renderQueuesSidebar() {
        queuesContainer.innerHTML = '';
        const enabled = categoriesConfig.filter(c => c.enabled && !c.archived);

        const queues = [...enabled.map(c => ({ label: c.label, name: c.name })), { label: 'Escalated', name: 'Escalated' }];

        queues.forEach(q => {
            const btn = document.createElement('button');
            btn.className = `queue-item ${currentQueue === q.label ? 'active' : ''}`;
            btn.innerHTML = `
                <i data-lucide="${q.name === 'Escalated' ? 'alert-triangle' : 'folder'}"></i>
                <span>${q.label}</span>
                <span class="queue-count" id="count-${q.name}">0</span>
            `;
            btn.addEventListener('click', () => {
                if (!isAuthenticated) {
                    showToast('🔒 Please sign in first to access queues.', 'error');
                    switchTab('signin');
                    return;
                }
                document.querySelectorAll('.queue-item').forEach(i => i.classList.remove('active'));
                btn.classList.add('active');
                currentQueue = q.label;
                loadEmails();
            });
            queuesContainer.appendChild(btn);
        });
        lucide.createIcons();
    }

    // Load & Render Emails
    async function loadEmails() {
        if (!isAuthenticated) {
            updateAuthUI();
            return;
        }

        queueTitle.textContent = `${currentQueue} Queue`;
        queueSubtitle.textContent = `Showing processed emails for ${currentUserEmail} in ${currentQueue} sorted from most to least recent.`;
        emailsContainer.innerHTML = '<div class="text-subtle">Loading email feed...</div>';

        try {
            const res = await fetch(`/api/emails?queue=${encodeURIComponent(currentQueue)}`);
            emailRecords = await res.json();
            renderEmailsFeed();
        } catch (err) {
            console.error('Failed to load emails', err);
            emailsContainer.innerHTML = '<div class="text-subtle">Error loading emails.</div>';
        }
    }

    function renderEmailsFeed() {
        if (!isAuthenticated) return;

        const query = searchInput.value.toLowerCase();
        const filtered = emailRecords.filter(e => 
            (e.sender && e.sender.toLowerCase().includes(query)) ||
            (e.subject && e.subject.toLowerCase().includes(query)) ||
            (e.body_content && e.body_content.toLowerCase().includes(query))
        );

        queueCountBadge.textContent = `${filtered.length} Email${filtered.length === 1 ? '' : 's'}`;

        if (filtered.length === 0) {
            emailsContainer.innerHTML = '<div class="card glass-card text-subtle" style="text-align:center; padding:40px;">No emails found in this queue.</div>';
            return;
        }

        emailsContainer.innerHTML = '';
        filtered.forEach(email => {
            const card = document.createElement('div');
            card.className = 'email-card';
            
            const isFollowup = email.is_followup;
            const isEscalated = email.escalated;
            const confidence = email.confidence || 'N/A';
            const sentiment = email.sentiment || 'Neutral';
            const dateStr = email.date || 'Recent';

            card.innerHTML = `
                <div class="email-header">
                    <div class="email-sender">
                        <i data-lucide="user"></i>
                        <span>${escapeHtml(email.sender || 'Customer')}</span>
                    </div>
                    <span class="email-date">${escapeHtml(dateStr)}</span>
                </div>
                <div class="email-subject">${escapeHtml(email.subject || 'Support Ticket')}</div>
                <div class="email-snippet">${escapeHtml(email.body_content ? email.body_content.substring(0, 120) + '...' : '')}</div>
                <div class="tag-pills">
                    ${isFollowup ? '<span class="pill pill-followup"><i data-lucide="mail-check"></i> 📬 Follow-up</span>' : ''}
                    ${isEscalated ? '<span class="pill pill-escalated"><i data-lucide="alert-circle"></i> Escalated</span>' : ''}
                    <span class="pill pill-confidence">AI Confidence: ${confidence}</span>
                    <span class="pill pill-sentiment">Sentiment: ${sentiment}</span>
                </div>
                ${email.draft_reply ? `
                    <div class="draft-box">
                        <div class="draft-title"><i data-lucide="sparkles"></i> AI Compliant Draft Reply:</div>
                        <div class="draft-body">${escapeHtml(email.draft_reply)}</div>
                    </div>
                ` : ''}
            `;
            emailsContainer.appendChild(card);
        });
        lucide.createIcons();
    }

    searchInput.addEventListener('input', renderEmailsFeed);

    // Run Triage Trigger
    runTriageBtn.addEventListener('click', async () => {
        if (!isAuthenticated) {
            showToast('🔒 Please sign in first to run AI triage.', 'error');
            switchTab('signin');
            return;
        }
        runTriageBtn.disabled = true;
        runTriageBtn.innerHTML = '<i data-lucide="loader"></i> Processing...';
        lucide.createIcons();
        showToast('Running AI Triage on incoming emails...', 'info');

        try {
            const res = await fetch('/api/triage', { method: 'POST' });
            const data = await res.json();
            showToast(data.message || 'Triage completed successfully!', 'success');
            loadEmails();
        } catch (err) {
            showToast('Triage execution failed.', 'error');
        } finally {
            runTriageBtn.disabled = false;
            runTriageBtn.innerHTML = '<i data-lucide="play"></i> <span>Run AI Triage</span>';
            lucide.createIcons();
        }
    });

    // Render Category Manager
    function renderCategoryManager() {
        if (!isAuthenticated) return;
        const enabled = categoriesConfig.filter(c => c.enabled && !c.archived);
        const totalEnabled = enabled.length;
        const maxCat = 8;
        const minCat = 1;

        document.getElementById('active-cat-count').textContent = totalEnabled;
        document.getElementById('max-cat-count').textContent = maxCat;

        const statusMsg = document.getElementById('cap-status-msg');
        if (totalEnabled >= maxCat) {
            statusMsg.textContent = `You have reached the maximum limit of ${maxCat} active categories. Disable or remove a category to add new ones.`;
            statusMsg.style.color = '#f59e0b';
        } else {
            statusMsg.textContent = `You can add up to ${maxCat - totalEnabled} more category/categories.`;
            statusMsg.style.color = '#10b981';
        }

        // Standard Categories
        const stdContainer = document.getElementById('standard-categories-list');
        stdContainer.innerHTML = '';
        const stdCats = categoriesConfig.filter(c => c.is_standard);
        stdCats.forEach(c => {
            const div = document.createElement('div');
            div.className = 'cat-setting-item';
            div.innerHTML = `
                <div class="cat-info">
                    <h4>${escapeHtml(c.label)}</h4>
                    <p>${escapeHtml(c.description)}</p>
                </div>
                <input type="checkbox" data-cat="${c.name}" ${c.enabled ? 'checked' : ''} ${totalEnabled >= maxCat && !c.enabled ? 'disabled' : ''}>
            `;
            stdContainer.appendChild(div);
        });

        // Custom Categories
        const customContainer = document.getElementById('custom-categories-list');
        customContainer.innerHTML = '';
        const customCats = categoriesConfig.filter(c => !c.is_standard && !c.archived);
        if (customCats.length === 0) {
            customContainer.innerHTML = '<div class="text-subtle">No custom categories configured yet.</div>';
        } else {
            customCats.forEach(c => {
                const div = document.createElement('div');
                div.className = 'cat-setting-item';
                div.innerHTML = `
                    <div class="cat-info">
                        <h4>${escapeHtml(c.label)}</h4>
                        <p>${escapeHtml(c.description)}</p>
                    </div>
                    <button class="btn btn-accent btn-sm remove-custom-btn" data-cat="${c.name}">Remove</button>
                `;
                customContainer.appendChild(div);
            });
        }

        // Add Event Listeners for Remove
        document.querySelectorAll('.remove-custom-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                if (totalEnabled <= minCat) {
                    showToast(`Cannot remove category. At least ${minCat} active category is required.`, 'error');
                    return;
                }
                const catName = btn.getAttribute('data-cat');
                await toggleCategory(catName, false, true);
            });
        });

        // Definitions at bottom (only Name and Definition)
        const defsContainer = document.getElementById('active-definitions-list');
        defsContainer.innerHTML = '';
        enabled.forEach(c => {
            const div = document.createElement('div');
            div.className = 'def-item';
            div.innerHTML = `<strong>${escapeHtml(c.label)}</strong>: ${escapeHtml(c.description)}`;
            defsContainer.appendChild(div);
        });
    }

    async function toggleCategory(name, enableState, archive = false) {
        try {
            const res = await fetch('/api/categories/toggle', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, enabled: enableState, archived: archive })
            });
            const data = await res.json();
            if (res.ok) {
                showToast(data.message, 'success');
                loadCategories();
            } else {
                showToast(data.error || 'Failed to update category', 'error');
            }
        } catch (err) {
            showToast('API connection error', 'error');
        }
    }

    // Add Category Form Submit
    document.getElementById('add-category-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('new-cat-name').value.trim();
        const desc = document.getElementById('new-cat-desc').value.trim();
        const mode = document.getElementById('new-cat-mode').value;

        try {
            const res = await fetch('/api/categories/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, description: desc, automation_mode: mode })
            });
            const data = await res.json();
            if (res.ok) {
                showToast(`Category '${name}' added successfully!`, 'success');
                document.getElementById('add-category-form').reset();
                loadCategories();
            } else {
                showToast(data.error || 'Failed to add category', 'error');
            }
        } catch (err) {
            showToast('API connection error', 'error');
        }
    });

    // Toast Helper
    function showToast(msg, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.textContent = msg;
        if (type === 'error') toast.style.borderLeftColor = '#ef4444';
        if (type === 'success') toast.style.borderLeftColor = '#10b981';
        container.appendChild(toast);
        setTimeout(() => toast.remove(), 4000);
    }

    function escapeHtml(str) {
        return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
    }

    // Initial Authentication check on load
    if (isAuthenticated) {
        updateAuthUI();
        loadCategories();
        loadEmails();
        switchTab('dashboard');
    } else {
        updateAuthUI();
        switchTab('signin');
    }
});
