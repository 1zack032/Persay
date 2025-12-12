        // ============================================
        // PANEL & MODAL FUNCTIONS
        // ============================================
        
        let activePanel = null;
        let searchType = 'all';
        let selectedGroupMembers = [];
        let activeMainTab = 'chats';
        
        function switchMainTab(tab) {
            activeMainTab = tab;
            
            // Update tab buttons
            document.getElementById('chatsTabBtn').classList.toggle('active', tab === 'chats');
            document.getElementById('channelsTabBtn').classList.toggle('active', tab === 'channels');
            
            // Update content panels
            document.getElementById('chatsTabContent').classList.toggle('active', tab === 'chats');
            document.getElementById('channelsTabContent').classList.toggle('active', tab === 'channels');
        }
        
        function togglePanel(panel, event) {
            // Stop propagation to prevent document click handler from firing
            if (event) {
                event.stopPropagation();
            }
            
            const writePanel = document.getElementById('writePanel');
            
            if (panel === 'search') {
                // Close write panel first
                if (writePanel) {
                    writePanel.classList.remove('show');
                    activePanel = null;
                }
                // Open search modal
                openSearchModal();
                return;
            }
            
            if (panel === 'write') {
                // Toggle the write panel
                if (writePanel.classList.contains('show')) {
                    writePanel.classList.remove('show');
                    activePanel = null;
                } else {
                    writePanel.classList.add('show');
                    activePanel = 'write';
                }
            }
        }
        
        // Close write panel when clicking outside
        document.addEventListener('click', function(e) {
            const writePanel = document.getElementById('writePanel');
            if (!writePanel) return;
            
            // Check if click is inside the panel or on the write button
            const isInsidePanel = writePanel.contains(e.target);
            const isWriteButton = e.target.closest('[data-panel="write"]');
            
            if (writePanel.classList.contains('show') && !isInsidePanel && !isWriteButton) {
                writePanel.classList.remove('show');
                activePanel = null;
            }
        });
        
        // Search Modal Functions
        let searchCategory = 'all';
        
        function openSearchModal() {
            document.getElementById('searchModal').classList.add('show');
            setTimeout(() => {
                document.getElementById('globalSearchInput').focus();
            }, 100);
        }
        
        function setSearchCategory(category) {
            searchCategory = category;
            document.querySelectorAll('.search-cat-tab').forEach(tab => {
                tab.classList.toggle('active', tab.dataset.category === category);
            });
            // Re-run search with new category
            handleGlobalSearch(document.getElementById('globalSearchInput').value);
        }
        
        function handleGlobalSearch(query) {
            const resultsContainer = document.getElementById('searchResultsContainer');
            
            if (!query.trim()) {
                resultsContainer.innerHTML = `
                    <div class="search-placeholder">
                        <div class="search-placeholder-icon">
                            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="opacity: 0.5;"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
                        </div>
                        <p>Start typing to search...</p>
                        <span class="search-placeholder-hint">Search for users, groups, channels, or synced contacts</span>
                    </div>
                `;
                return;
            }
            
            const lowerQuery = query.toLowerCase();
            let html = '';
            let hasResults = false;
            
            // Get users already in contacts (added)
            const addedUsers = Array.from(document.querySelectorAll('.contact')).map(c => c.dataset.username);
            
            // Search Users - Show ADDED first, then DISCOVER
            if (searchCategory === 'all' || searchCategory === 'users') {
                // First: Added users matching query
                const matchedAddedUsers = addedUsers.filter(u => u.toLowerCase().includes(lowerQuery));
                
                if (matchedAddedUsers.length > 0) {
                    hasResults = true;
                    html += `<div class="search-result-section">
                        <div class="search-section-title"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align: middle; margin-right: 4px;"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg> Your Contacts</div>`;
                    matchedAddedUsers.forEach(user => {
                        html += `
                            <div class="search-result-item" onclick="selectContactFromSearch('${user}')">
                                <div class="search-result-avatar user">${user[0].toUpperCase()}</div>
                                <div class="search-result-info">
                                    <div class="search-result-name">${user}</div>
                                    <div class="search-result-meta">Added contact</div>
                                </div>
                                <span class="search-result-badge" style="background: rgba(16, 185, 129, 0.15); color: #34d399;">Added</span>
                            </div>`;
                    });
                    html += '</div>';
                }
                
                // Then: Fetch other users not in contacts (discover)
                fetch(`/api/users/search?q=${encodeURIComponent(query)}`)
                    .then(res => res.json())
                    .then(data => {
                        if (data.users && data.users.length > 0) {
                            // Filter out already added users
                            const discoverUsers = data.users.filter(u => !addedUsers.includes(u.username));
                            
                            if (discoverUsers.length > 0) {
                                let discoverHtml = `<div class="search-result-section">
                                    <div class="search-section-title"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align: middle; margin-right: 4px;"><circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/></svg> Discover Users</div>`;
                                discoverUsers.forEach(user => {
                                    discoverHtml += `
                                        <div class="search-result-item" onclick="selectContactFromSearch('${user.username}')">
                                            <div class="search-result-avatar user" style="opacity: 0.7;">${user.username[0].toUpperCase()}</div>
                                            <div class="search-result-info">
                                                <div class="search-result-name">${user.username}</div>
                                                <div class="search-result-meta">Menza user</div>
                                            </div>
                                            <span class="search-result-badge">New</span>
                                        </div>`;
                                });
                                discoverHtml += '</div>';
                                
                                // Append to existing results
                                const container = document.getElementById('searchResultsContainer');
                                container.innerHTML = container.innerHTML.replace('<!-- USERS_END -->', discoverHtml + '<!-- USERS_END -->');
                            }
                        }
                    })
                    .catch(() => {});
                
                html += '<!-- USERS_END -->';
            }
            
            // Search Groups - Show JOINED first, then DISCOVER
            if (searchCategory === 'all' || searchCategory === 'groups') {
                // TODO: Implement groups when group feature is complete
                if (searchCategory === 'groups' && lowerQuery.length >= 2) {
                    html += `<div class="search-result-section">
                        <div class="search-section-title"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align: middle; margin-right: 4px;"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg> Groups</div>
                        <div class="search-no-results">
                            <p style="color: var(--text-muted); font-size: 0.875rem;">No groups found matching "${query}"</p>
                        </div>
                    </div>`;
                }
            }
            
            // Search Channels - Show SUBSCRIBED first, then DISCOVER
            if (searchCategory === 'all' || searchCategory === 'channels') {
                fetch(`/api/channels/search?q=${encodeURIComponent(query)}&include_subscription=true`)
                    .then(res => res.json())
                    .then(data => {
                        if (data.channels && data.channels.length > 0) {
                            // Separate subscribed vs discoverable
                            const subscribedChannels = data.channels.filter(c => c.is_subscribed);
                            const discoverChannels = data.channels.filter(c => !c.is_subscribed);
                            
                            let channelHtml = '';
                            
                            // First: Subscribed channels
                            if (subscribedChannels.length > 0) {
                                channelHtml += `<div class="search-result-section">
                                    <div class="search-section-title"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align: middle; margin-right: 4px;"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg> Your Channels</div>`;
                                subscribedChannels.forEach(channel => {
                                    channelHtml += `
                                        <div class="search-result-item" onclick="window.location.href='/channel/${channel.id}'">
                                            <div class="search-result-avatar channel">${channel.branding?.avatar_emoji || '📺'}</div>
                                            <div class="search-result-info">
                                                <div class="search-result-name">${channel.name}</div>
                                                <div class="search-result-meta">${channel.subscribers?.length || 0} members</div>
                                            </div>
                                            <span class="search-result-badge" style="background: rgba(16, 185, 129, 0.15); color: #34d399;">Joined</span>
                                        </div>`;
                                });
                                channelHtml += '</div>';
                            }
                            
                            // Then: Discoverable channels
                            if (discoverChannels.length > 0) {
                                channelHtml += `<div class="search-result-section">
                                    <div class="search-section-title"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align: middle; margin-right: 4px;"><circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/></svg> Discover Channels</div>`;
                                discoverChannels.forEach(channel => {
                                    channelHtml += `
                                        <div class="search-result-item" onclick="window.location.href='/channel/${channel.id}'">
                                            <div class="search-result-avatar channel" style="opacity: 0.7;">${channel.branding?.avatar_emoji || '📺'}</div>
                                            <div class="search-result-info">
                                                <div class="search-result-name">${channel.name}</div>
                                                <div class="search-result-meta">${channel.subscribers?.length || 0} members</div>
                                            </div>
                                            ${channel.discoverable ? '<span class="search-result-badge">Public</span>' : ''}
                                        </div>`;
                                });
                                channelHtml += '</div>';
                            }
                            
                            if (channelHtml) {
                                const container = document.getElementById('searchResultsContainer');
                                container.innerHTML = container.innerHTML.replace('<!-- CHANNELS_END -->', channelHtml + '<!-- CHANNELS_END -->');
                            }
                        }
                    })
                    .catch(() => {});
                
                html += '<!-- CHANNELS_END -->';
            }
            
            // Search Contacts (synced from phone)
            if (searchCategory === 'all' || searchCategory === 'contacts') {
                const syncedContacts = window.syncedContacts || [];
                
                // Separate: On Menza vs Not on Menza
                const matchedContacts = syncedContacts.filter(c => 
                    c.name.toLowerCase().includes(lowerQuery) || 
                    (c.phone && c.phone.includes(lowerQuery))
                );
                
                const onMenzaContacts = matchedContacts.filter(c => c.onMenza);
                const notOnMenzaContacts = matchedContacts.filter(c => !c.onMenza);
                
                if (onMenzaContacts.length > 0) {
                    hasResults = true;
                    html += `<div class="search-result-section">
                        <div class="search-section-title"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align: middle; margin-right: 4px;"><rect x="5" y="2" width="14" height="20" rx="2" ry="2"/><line x1="12" y1="18" x2="12.01" y2="18"/></svg> Contacts on Menza</div>`;
                    onMenzaContacts.forEach(contact => {
                        html += `
                            <div class="search-result-item" onclick="selectContactFromSearch('${contact.menzaUsername}')">
                                <div class="search-result-avatar contact">${contact.name[0].toUpperCase()}</div>
                                <div class="search-result-info">
                                    <div class="search-result-name">${contact.name}</div>
                                    <div class="search-result-meta">@${contact.menzaUsername}</div>
                                </div>
                                <span class="search-result-badge" style="background: rgba(16, 185, 129, 0.15); color: #34d399;">On Menza</span>
                            </div>`;
                    });
                    html += '</div>';
                }
                
                if (notOnMenzaContacts.length > 0) {
                    hasResults = true;
                    html += `<div class="search-result-section">
                        <div class="search-section-title"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align: middle; margin-right: 4px;"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="8.5" cy="7" r="4"/><line x1="20" y1="8" x2="20" y2="14"/><line x1="23" y1="11" x2="17" y2="11"/></svg> Invite to Menza</div>`;
                    notOnMenzaContacts.forEach(contact => {
                        html += `
                            <div class="search-result-item" onclick="inviteContact('${contact.phone}')">
                                <div class="search-result-avatar contact" style="opacity: 0.6;">${contact.name[0].toUpperCase()}</div>
                                <div class="search-result-info">
                                    <div class="search-result-name">${contact.name}</div>
                                    <div class="search-result-meta">${contact.phone || 'No phone'}</div>
                                </div>
                                <span class="search-result-badge">Invite</span>
                            </div>`;
                    });
                    html += '</div>';
                }
                
                if (matchedContacts.length === 0 && searchCategory === 'contacts' && lowerQuery.length >= 2) {
                    html += `<div class="search-result-section">
                        <div class="search-section-title"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align: middle; margin-right: 4px;"><rect x="5" y="2" width="14" height="20" rx="2" ry="2"/><line x1="12" y1="18" x2="12.01" y2="18"/></svg> Contacts</div>
                        <div class="search-no-results">
                            <p style="color: var(--text-muted); font-size: 0.875rem;">No synced contacts found</p>
                            <p style="font-size: 0.75rem; margin-top: 0.5rem; color: var(--text-muted);">Enable Contact Sync in Settings → Privacy</p>
                        </div>
                    </div>`;
                }
            }
            
            if (!hasResults && html.replace(/<!-- [A-Z_]+ -->/g, '').trim() === '') {
                html = `
                    <div class="search-no-results">
                        <div class="search-no-results-icon">
                            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="opacity: 0.5;"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
                        </div>
                        <p>No results found for "${query}"</p>
                    </div>
                `;
            }
            
            resultsContainer.innerHTML = html;
        }
        
        function selectContactFromSearch(username) {
            closeModal('searchModal');
            selectContact(username);
        }
        
        function inviteContact(phone) {
            // Show invite option
            alert(`Invite ${phone} to Menza!\nShare link: https://menza.app/invite`);
        }
        
        // Initialize synced contacts array
        window.syncedContacts = [];
        
        function setSearchType(type) {
            searchType = type;
            document.querySelectorAll('.search-tab').forEach(tab => {
                tab.classList.toggle('active', tab.dataset.type === type);
            });
            handleSearch(document.getElementById('globalSearch').value);
        }
        
        function handleSearch(query) {
            const resultsDiv = document.getElementById('searchResults');
            
            if (!query.trim()) {
                resultsDiv.innerHTML = '';
                return;
            }
            
            // Search through users
            const allUsers = Array.from(document.querySelectorAll('.contact')).map(c => c.dataset.username);
            const matchedUsers = allUsers.filter(u => u.toLowerCase().includes(query.toLowerCase()));
            
            let html = '';
            
            if (searchType === 'all' || searchType === 'users') {
                matchedUsers.forEach(user => {
                    html += `
                        <div class="search-result-item" onclick="selectContact('${user}'); togglePanel('search');">
                            <div class="search-result-avatar">${user[0].toUpperCase()}</div>
                            <div>
                                <div class="search-result-name">${user}</div>
                                <div class="search-result-type">User</div>
                            </div>
                        </div>
                    `;
                });
            }
            
            if (!html && query.length > 0) {
                html = '<div style="padding: 1rem; text-align: center; color: var(--text-muted); font-size: 0.875rem;">No results found</div>';
            }
            
            resultsDiv.innerHTML = html;
        }
        
        // Selected recipients for new message
        let selectedMessageRecipients = [];
        
        function startNewMessage() {
            // Close the write dropdown
            document.getElementById('writePanel').classList.remove('show');
            activePanel = null;
            
            // Reset selected recipients
            selectedMessageRecipients = [];
            updateSelectedRecipientsUI();
            
            // Clear search
            const searchInput = document.getElementById('newMessageSearchInput');
            if (searchInput) searchInput.value = '';
            
            // Load initial user list (known users first)
            loadMessageUserList('');
            
            // Open the new message modal
            document.getElementById('newMessageModal').classList.add('show');
            
            // Focus search input
            setTimeout(() => searchInput && searchInput.focus(), 100);
        }
        
        function loadMessageUserList(query) {
            const listDiv = document.getElementById('messageUserList');
            listDiv.innerHTML = `
                <div class="loading-placeholder" style="text-align: center; padding: 2rem; color: var(--text-muted);">
                    <div class="spinner" style="width: 24px; height: 24px; border: 2px solid var(--border); border-top-color: var(--accent-primary); border-radius: 50%; animation: spin 0.8s linear infinite; margin: 0 auto 0.5rem;"></div>
                    Loading...
                </div>`;
            
            // Use smart search endpoint that prioritizes known users
            fetch(`/api/users/smart-search?q=${encodeURIComponent(query)}`)
                .then(res => res.json())
                .then(data => {
                    let html = '';
                    
                    // Show known users section if any
                    if (data.known_users && data.known_users.length > 0) {
                        html += `<div style="font-size: 0.6875rem; color: var(--accent-primary); font-weight: 600; padding: 0.5rem 0.75rem; background: rgba(168, 85, 247, 0.08); border-radius: var(--radius-sm); margin-bottom: 0.5rem;">👥 CONTACTS</div>`;
                        data.known_users.forEach(user => {
                            html += renderMessageUserItem(user, true);
                        });
                    }
                    
                    // Show other users section if any
                    if (data.other_users && data.other_users.length > 0) {
                        if (data.known_users && data.known_users.length > 0) {
                            html += `<div style="font-size: 0.6875rem; color: var(--text-muted); font-weight: 600; padding: 0.5rem 0.75rem; margin-top: 0.75rem; margin-bottom: 0.5rem;">🔍 OTHER USERS</div>`;
                        }
                        data.other_users.forEach(user => {
                            html += renderMessageUserItem(user, false);
                        });
                    }
                    
                    if (!html) {
                        html = `
                            <div style="text-align: center; padding: 2rem; color: var(--text-muted);">
                                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="opacity: 0.5; margin-bottom: 0.5rem;">
                                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
                                </svg>
                                <p style="font-size: 0.8125rem;">${query ? `No users found for "${query}"` : 'No users available'}</p>
                            </div>`;
                    }
                    
                    listDiv.innerHTML = html;
                    
                    // Update selected state visually
                    updateUserListSelectedState();
                })
                .catch(err => {
                    listDiv.innerHTML = `
                        <div style="text-align: center; padding: 2rem; color: var(--error);">
                            Failed to load users
                        </div>`;
                });
        }
        
        function renderMessageUserItem(user, isKnown) {
            const initial = user.display_name ? user.display_name[0].toUpperCase() : user.username[0].toUpperCase();
            const displayName = user.display_name || user.username;
            const isSelected = selectedMessageRecipients.includes(user.username);
            
            return `
                <div class="user-select-item ${isSelected ? 'selected' : ''}" data-username="${user.username}" onclick="toggleMessageRecipient('${user.username}')">
                    <div class="user-select-avatar" style="${isKnown ? 'border: 2px solid var(--accent-primary);' : ''}">${initial}</div>
                    <div class="user-select-info" style="flex: 1;">
                        <div class="user-select-name">${displayName}</div>
                        ${user.display_name && user.display_name !== user.username ? `<div style="font-size: 0.75rem; color: var(--text-muted);">@${user.username}</div>` : ''}
                    </div>
                    ${user.message_count ? `<span style="font-size: 0.6875rem; color: var(--text-muted); margin-right: 0.5rem;">${user.message_count} msgs</span>` : ''}
                    <div class="user-select-check" style="${isSelected ? 'opacity: 1;' : ''}">✓</div>
                </div>`;
        }
        
        function toggleMessageRecipient(username) {
            const index = selectedMessageRecipients.indexOf(username);
            if (index === -1) {
                selectedMessageRecipients.push(username);
            } else {
                selectedMessageRecipients.splice(index, 1);
            }
            updateSelectedRecipientsUI();
            updateUserListSelectedState();
        }
        
        function removeMessageRecipient(username) {
            const index = selectedMessageRecipients.indexOf(username);
            if (index !== -1) {
                selectedMessageRecipients.splice(index, 1);
            }
            updateSelectedRecipientsUI();
            updateUserListSelectedState();
        }
        
        function updateUserListSelectedState() {
            document.querySelectorAll('#messageUserList .user-select-item').forEach(item => {
                const username = item.getAttribute('data-username');
                if (selectedMessageRecipients.includes(username)) {
                    item.classList.add('selected');
                    item.querySelector('.user-select-check').style.opacity = '1';
                } else {
                    item.classList.remove('selected');
                    item.querySelector('.user-select-check').style.opacity = '';
                }
            });
        }
        
        function updateSelectedRecipientsUI() {
            const preview = document.getElementById('selectedRecipientsPreview');
            const list = document.getElementById('selectedRecipientsList');
            const countSpan = document.getElementById('selectedRecipientsCount');
            const btn = document.getElementById('startConversationBtn');
            const btnText = document.getElementById('startConversationBtnText');
            
            if (selectedMessageRecipients.length === 0) {
                preview.style.display = 'none';
                btn.disabled = true;
                btnText.textContent = 'Select Recipients';
            } else {
                preview.style.display = 'block';
                countSpan.textContent = selectedMessageRecipients.length;
                
                // Render selected recipient chips
                list.innerHTML = selectedMessageRecipients.map(username => `
                    <div style="display: inline-flex; align-items: center; gap: 0.25rem; background: var(--accent-primary); color: white; padding: 0.25rem 0.5rem; border-radius: 999px; font-size: 0.75rem;">
                        <span>${username}</span>
                        <button onclick="removeMessageRecipient('${username}')" style="background: none; border: none; color: white; cursor: pointer; padding: 0; font-size: 1rem; line-height: 1; opacity: 0.8;">×</button>
                    </div>
                `).join('');
                
                btn.disabled = false;
                if (selectedMessageRecipients.length === 1) {
                    btnText.textContent = 'Start Chat';
                } else {
                    btnText.textContent = `Create Group (${selectedMessageRecipients.length})`;
                }
            }
        }
        
        function searchUsersForMessage(query) {
            // Debounce the search
            clearTimeout(window.messageSearchTimeout);
            window.messageSearchTimeout = setTimeout(() => {
                loadMessageUserList(query);
            }, 300);
        }
        
        function startConversation() {
            if (selectedMessageRecipients.length === 0) return;
            
            if (selectedMessageRecipients.length === 1) {
                // Start DM with single user
                closeModal('newMessageModal');
                selectContact(selectedMessageRecipients[0]);
            } else {
                // Create a group with multiple users
                const groupName = selectedMessageRecipients.slice(0, 3).join(', ') + (selectedMessageRecipients.length > 3 ? ` +${selectedMessageRecipients.length - 3}` : '');
                
                // Use socket to create group
                if (typeof socket !== 'undefined') {
                    socket.emit('create_group', {
                        name: groupName,
                        members: selectedMessageRecipients
                    });
                    
                    closeModal('newMessageModal');
                    
                    // Show feedback
                    showToast(`Creating group with ${selectedMessageRecipients.length} members...`);
                }
            }
        }
        
        // Toast notification helper
        function showToast(message) {
            const toast = document.createElement('div');
            toast.style.cssText = 'position: fixed; bottom: 2rem; left: 50%; transform: translateX(-50%); background: var(--bg-card); border: 1px solid var(--border); padding: 0.75rem 1.5rem; border-radius: var(--radius-md); box-shadow: 0 4px 12px rgba(0,0,0,0.3); z-index: 10000; font-size: 0.875rem;';
            toast.textContent = message;
            document.body.appendChild(toast);
            setTimeout(() => toast.remove(), 3000);
        }
        
        function startNewGroup() {
            // Close the write dropdown
            document.getElementById('writePanel').classList.remove('show');
            activePanel = null;
            
            selectedGroupMembers = [];
            currentGroupInviteCode = null;
            
            // Reset all selections
            document.querySelectorAll('#groupUserList .user-select-item').forEach(item => {
                item.classList.remove('selected');
            });
            document.getElementById('groupName').value = '';
            document.getElementById('groupSearchInput').value = '';
            document.getElementById('groupSearchResults').innerHTML = `
                <div class="search-placeholder">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="opacity: 0.5;"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
                    <p style="color: var(--text-muted); font-size: 0.8125rem;">Type a username to search</p>
                </div>`;
            
            // Reset invite link
            document.getElementById('groupInviteLinkBox').style.display = 'none';
            document.getElementById('generateGroupLinkBtn').innerHTML = `
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
                Generate Invite Link`;
            
            // Reset tabs to first tab
            switchGroupTab('contacts');
            
            // Hide selected members preview
            document.getElementById('selectedMembersPreview').style.display = 'none';
            
            // Open the new group modal
            document.getElementById('newGroupModal').classList.add('show');
        }
        
        function closeModal(modalId) {
            document.getElementById(modalId).classList.remove('show');
        }
        
        function selectUserForMessage(username) {
            closeModal('newMessageModal');
            selectContact(username);
        }
        
        function filterUsers(query) {
            const items = document.querySelectorAll('#userSelectList .user-select-item');
            items.forEach(item => {
                const name = item.querySelector('.user-select-name').textContent.toLowerCase();
                item.style.display = name.includes(query.toLowerCase()) ? 'flex' : 'none';
            });
        }
        
        function toggleGroupMember(element, username) {
            element.classList.toggle('selected');
            const index = selectedGroupMembers.indexOf(username);
            if (index > -1) {
                selectedGroupMembers.splice(index, 1);
            } else {
                selectedGroupMembers.push(username);
            }
            updateSelectedMembersPreview();
            
            // Also sync selection in search results if visible
            syncMemberSelection(username, element.classList.contains('selected'));
        }
        
        function updateSelectedMembersPreview() {
            const preview = document.getElementById('selectedMembersPreview');
            const list = document.getElementById('selectedMembersList');
            
            if (selectedGroupMembers.length === 0) {
                preview.style.display = 'none';
                return;
            }
            
            preview.style.display = 'block';
            list.innerHTML = selectedGroupMembers.map(member => `
                <div class="selected-member-chip">
                    <span>${member}</span>
                    <button class="remove" onclick="removeMemberFromGroup('${member}')" title="Remove">×</button>
                </div>
            `).join('');
        }
        
        function removeMemberFromGroup(username) {
            const index = selectedGroupMembers.indexOf(username);
            if (index > -1) {
                selectedGroupMembers.splice(index, 1);
            }
            
            // Update UI
            document.querySelectorAll(`.user-select-item[data-username="${username}"]`).forEach(el => {
                el.classList.remove('selected');
            });
            
            updateSelectedMembersPreview();
        }
        
        function syncMemberSelection(username, isSelected) {
            // Sync selection across contacts and search results
            document.querySelectorAll(`.user-select-item[data-username="${username}"]`).forEach(el => {
                if (isSelected) {
                    el.classList.add('selected');
                } else {
                    el.classList.remove('selected');
                }
            });
        }
        
        function switchGroupTab(tab) {
            // Update tab buttons
            document.querySelectorAll('.group-tab').forEach(t => t.classList.remove('active'));
            document.querySelector(`.group-tab[onclick*="${tab}"]`).classList.add('active');
            
            // Update tab content
            document.querySelectorAll('.group-tab-content').forEach(c => c.classList.remove('active'));
            document.getElementById(`group${tab.charAt(0).toUpperCase() + tab.slice(1)}Tab`).classList.add('active');
        }
        
        function searchUsersForGroup(query) {
            const resultsContainer = document.getElementById('groupSearchResults');
            
            if (!query.trim()) {
                resultsContainer.innerHTML = `
                    <div class="search-placeholder">
                        <span style="font-size: 1.5rem; opacity: 0.5;">🔍</span>
                        <p style="color: var(--text-muted); font-size: 0.8125rem;">Type a username to search</p>
                    </div>`;
                return;
            }
            
            // Filter users based on query (fetch from API)
            // Use empty array as fallback - real search uses API
            const filtered = [];
            
            if (filtered.length === 0) {
                resultsContainer.innerHTML = `
                    <div class="search-placeholder">
                        <span style="font-size: 1.5rem; opacity: 0.5;">😕</span>
                        <p style="color: var(--text-muted); font-size: 0.8125rem;">No users found matching "${query}"</p>
                    </div>`;
                return;
            }
            
            resultsContainer.innerHTML = filtered.map(user => {
                const isSelected = selectedGroupMembers.includes(user);
                return `
                    <div class="user-select-item ${isSelected ? 'selected' : ''}" data-username="${user}" onclick="toggleGroupMember(this, '${user}')">
                        <div class="user-select-avatar">${user[0].toUpperCase()}</div>
                        <div class="user-select-name">${user}</div>
                        <div class="user-select-check">✓</div>
                    </div>
                `;
            }).join('');
        }
        
        let currentGroupInviteCode = null;
        
        function generateGroupInviteLink() {
            // Generate a random invite code
            currentGroupInviteCode = 'grp_' + Math.random().toString(36).substring(2, 10) + Math.random().toString(36).substring(2, 6);
            const inviteLink = `${window.location.origin}/join/${currentGroupInviteCode}`;
            
            document.getElementById('groupInviteLink').value = inviteLink;
            document.getElementById('groupInviteLinkBox').style.display = 'flex';
            document.getElementById('generateGroupLinkBtn').innerHTML = '🔄 Regenerate Link';
            
            showToast('✨ Invite link generated!', 'success');
        }
        
        function copyGroupInviteLink() {
            const linkInput = document.getElementById('groupInviteLink');
            linkInput.select();
            document.execCommand('copy');
            showToast('📋 Invite link copied to clipboard!', 'success');
        }
        
        function createGroup() {
            const groupName = document.getElementById('groupName').value.trim();
            if (!groupName) {
                alert('Please enter a group name');
                return;
            }
            if (selectedGroupMembers.length === 0) {
                alert('Please select at least one member');
                return;
            }
            
            const inviteCode = currentGroupInviteCode || null;
            
            // Emit socket event to create group
            socket.emit('create_group', {
                name: groupName,
                members: selectedGroupMembers,
                invite_code: inviteCode
            });
            
            closeModal('newGroupModal');
        }
        
        // Close panels when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.action-bar') && activePanel) {
                togglePanel(activePanel);
            }
        });
        
        // ============================================
        // ENCRYPTION FUNCTIONS
        // ============================================
        
        // Username set from HTML template via window.MENZA_USERNAME
        const myUsername = window.MENZA_USERNAME || '';
        let currentFriend = null;
        let socket = null;
        let onlineUsers = new Set();
        
        async function deriveKey(password) {
            const encoder = new TextEncoder();
            const keyMaterial = await crypto.subtle.importKey(
                "raw",
                encoder.encode(password),
                "PBKDF2",
                false,
                ["deriveKey"]
            );
            
            return crypto.subtle.deriveKey(
                {
                    name: "PBKDF2",
                    salt: encoder.encode("persay-salt"),
                    iterations: 100000,
                    hash: "SHA-256"
                },
                keyMaterial,
                { name: "AES-GCM", length: 256 },
                false,
                ["encrypt", "decrypt"]
            );
        }
        
        async function encryptMessage(message, sharedSecret) {
            const key = await deriveKey(sharedSecret);
            const encoder = new TextEncoder();
            const iv = crypto.getRandomValues(new Uint8Array(12));
            
            const encrypted = await crypto.subtle.encrypt(
                { name: "AES-GCM", iv: iv },
                key,
                encoder.encode(message)
            );
            
            const combined = new Uint8Array(iv.length + encrypted.byteLength);
            combined.set(iv);
            combined.set(new Uint8Array(encrypted), iv.length);
            
            return btoa(String.fromCharCode(...combined));
        }
        
        async function decryptMessage(encryptedBase64, sharedSecret) {
            try {
                const key = await deriveKey(sharedSecret);
                const combined = Uint8Array.from(atob(encryptedBase64), c => c.charCodeAt(0));
                
                const iv = combined.slice(0, 12);
                const encrypted = combined.slice(12);
                
                const decrypted = await crypto.subtle.decrypt(
                    { name: "AES-GCM", iv: iv },
                    key,
                    encrypted
                );
                
                return new TextDecoder().decode(decrypted);
            } catch (e) {
                console.error("Decryption failed:", e);
                return "[Unable to decrypt]";
            }
        }
        
        function getSharedSecret(user1, user2) {
            const sorted = [user1, user2].sort();
            return `persay-shared-${sorted[0]}-${sorted[1]}-secret`;
        }
        
        // ============================================
        // SOCKET.IO CONNECTION
        // ============================================
        
        function initSocket() {
            socket = io();
            
            socket.on('connect', () => {
                console.log('Connected to server');
                // Load user's bots when connected
                loadUserBots();
            });
            
            socket.on('online_list', (data) => {
                onlineUsers = new Set(data.users);
                updateOnlineStatus();
            });
            
            socket.on('user_online', (data) => {
                onlineUsers.add(data.username);
                updateOnlineStatus();
            });
            
            socket.on('user_offline', (data) => {
                onlineUsers.delete(data.username);
                updateOnlineStatus();
            });
            
            socket.on('chat_history', async (data) => {
                const messagesDiv = document.getElementById('messages');
                messagesDiv.innerHTML = '';
                
                // Update settings if provided
                if (data.settings) {
                    currentChatSettings = data.settings;
                    updateAutoDeleteUI(data.settings.auto_delete);
                }
                
                for (const msg of data.messages) {
                    await displayMessage(msg);
                }
                
                // If there are messages, this is an active conversation
                if (data.messages.length > 0 && currentFriend) {
                    const lastMsg = data.messages[data.messages.length - 1];
                    trackDMConversation(currentFriend, lastMsg.from === myUsername ? 'You: ...' : '...');
                }
                
                scrollToBottom();
            });
            
            socket.on('new_message', async (data) => {
                await displayMessage(data);
                
                // Update the conversation preview
                if (currentFriend) {
                    const preview = data.from === myUsername ? 'You: Sent a message' : 'New message';
                    trackDMConversation(currentFriend, preview);
                }
                
                scrollToBottom();
            });
            
            // Message deletion events
            socket.on('message_deleted', (data) => {
                const msgEl = document.getElementById(`msg-${data.message_id}`);
                if (msgEl) {
                    msgEl.remove();
                }
            });
            
            socket.on('chat_cleared', (data) => {
                const messagesDiv = document.getElementById('messages');
                messagesDiv.innerHTML = '';
                
                // Clear shared notes as well
                unlockedNotes = {};
                const notesList = document.getElementById('sharedNotesList');
                if (notesList) {
                    notesList.innerHTML = '<div class="empty-notes">No shared notes yet. Create one to securely share with this conversation.</div>';
                }
                
                // Show system message about new chat
                showSystemMessage(`🔄 Chat cleared by ${data.cleared_by}. A fresh conversation has started.`);
                
                closeModal('clearChatModal');
                closeModal('chatSettingsModal');
            });
            
            socket.on('settings_updated', (data) => {
                currentChatSettings = data.settings;
                updateAutoDeleteUI(data.settings.auto_delete);
            });
            
            // Shared Notes Events
            socket.on('shared_note_created', (data) => {
                console.log('Note created:', data);
                // Refresh the notes list silently (don't force panel open)
                if (sharedNotesVisible) {
                    setTimeout(() => loadSharedNotes(), 100);
                }
            });
            
            socket.on('prompt_set_phrase', (data) => {
                // Only show prompt if we didn't create the note
                if (data.created_by !== myUsername) {
                    showSetPhrasePrompt(data);
                }
            });
            
            socket.on('phrase_set_success', (data) => {
                closeModal('setPhraseModal');
                loadSharedNotes();
                // Show success toast
                showToast('✓ Your secret phrase has been set!', 'success');
            });
            
            socket.on('note_unlocked', (data) => {
                closeModal('unlockNoteModal');
                // Store unlocked content temporarily
                unlockedNotes[data.note_id] = data;
                showUnlockedNote(data);
            });
            
            socket.on('note_unlock_failed', (data) => {
                document.getElementById('unlockError').style.display = 'block';
                document.getElementById('unlockPhrase').select();
            });
            
            socket.on('shared_notes_list', (data) => {
                console.log('📝 Received shared_notes_list:', data.notes);
                renderSharedNotes(data.notes);
                updateNotesBadge(data.notes);
            });
            
            socket.on('note_error', (data) => {
                showToast(data.error, 'error');
            });
            
            // Note deletion events
            socket.on('note_deleted', (data) => {
                showToast('📝 Shared note deleted by mutual agreement', 'success');
                delete unlockedNotes[data.note_id];
                loadSharedNotes();
            });
            
            socket.on('note_delete_requested', (data) => {
                if (data.requested_by !== myUsername) {
                    showToast(`${data.requested_by} wants to delete a shared note. Agree in the notes panel.`, 'info');
                }
                loadSharedNotes();
            });
            
            socket.on('note_delete_cancelled', (data) => {
                loadSharedNotes();
            });
            
            // Note editing events
            socket.on('note_edit_success', (data) => {
                closeModal('editNoteModal');
                showToast('✏️ Note updated successfully!', 'success');
                
                // Update the unlocked note cache with new values
                if (unlockedNotes[data.note_id]) {
                    const editTitle = document.getElementById('editNoteTitle').value.trim();
                    const editContent = document.getElementById('editNoteContent').value.trim();
                    if (editTitle) unlockedNotes[data.note_id].title = editTitle;
                    if (editContent) unlockedNotes[data.note_id].content = editContent;
                }
                
                loadSharedNotes();
            });
            
            socket.on('note_edited', (data) => {
                // Another user edited a note
                if (data.edited_by !== myUsername) {
                    showToast(`✏️ ${data.edited_by} edited a shared note`, 'info');
                }
                
                // Clear the unlocked cache for this note so user has to re-unlock to see changes
                delete unlockedNotes[data.note_id];
                
                loadSharedNotes();
            });
            
            // ==========================================
            // GROUP CHAT EVENTS
            // ==========================================
            
            socket.on('group_created', (data) => {
                showToast(`👥 Group "${data.group.name}" created!`, 'success');
                renderGroups([data.group], true); // Prepend to list
                loadUserGroups(); // Refresh full list
            });
            
            socket.on('group_invite', (data) => {
                showToast(`👥 You've been added to "${data.group.name}"`, 'info');
                renderGroups([data.group], true);
                loadUserGroups();
            });
            
            socket.on('user_groups', (data) => {
                renderGroups(data.groups);
            });
            
            socket.on('group_history', async (data) => {
                // Only render if this is the currently selected group
                if (currentGroup && currentGroup.id === data.group_id) {
                    const messagesDiv = document.getElementById('messages');
                    messagesDiv.innerHTML = '';
                    
                    for (const msg of data.messages) {
                        await displayGroupMessage(msg);
                    }
                    
                    scrollToBottom();
                }
            });
            
            socket.on('new_group_message', async (data) => {
                // Only display if we're in this group
                if (currentGroup && currentGroup.id === data.group_id) {
                    await displayGroupMessage(data.message);
                    scrollToBottom();
                }
                
                // Update conversation preview
                const group = userGroups.find(g => g.id === data.group_id);
                if (group) {
                    group.last_message = `${data.message.sender}: Message`;
                    group.last_message_time = data.message.timestamp;
                    renderActiveConversations();
                }
            });
            
            socket.on('group_notes_list', (data) => {
                if (currentGroup && currentGroup.id === data.group_id) {
                    renderSharedNotes(data.notes);
                    updateNotesBadge(data.notes);
                }
            });
            
            socket.on('group_error', (data) => {
                showToast(data.error, 'error');
            });
            
            // Register call-related socket events
            registerCallSocketEvents();
            
            // Load user's groups on connect
            socket.emit('get_user_groups');
        }
        
        // ==========================================
        // MESSAGES & CONVERSATIONS FUNCTIONS
        // ==========================================
        
        let activeConversations = []; // Stores both groups and DMs
        let userGroups = [];
        let userBots = []; // Bots added by user
        
        function loadUserGroups() {
            if (socket && socket.connected) {
                socket.emit('get_user_groups');
            }
        }
        
        async function loadUserBots() {
            try {
                const response = await fetch('/api/bots/my');
                const data = await response.json();
                if (data.bots) {
                    userBots = data.bots;
                    renderActiveConversations();
                }
            } catch (error) {
                console.error('Error loading bots:', error);
            }
        }
        
        function addActiveConversation(type, data) {
            // Check if already exists
            const existingIndex = activeConversations.findIndex(conv => 
                conv.type === type && conv.id === data.id
            );
            
            if (existingIndex === -1) {
                activeConversations.unshift({
                    type: type, // 'group' or 'dm'
                    ...data,
                    lastActivity: data.lastActivity || new Date().toISOString()
                });
            } else {
                // Update existing
                activeConversations[existingIndex] = {
                    ...activeConversations[existingIndex],
                    ...data,
                    lastActivity: new Date().toISOString()
                };
                // Move to top
                const item = activeConversations.splice(existingIndex, 1)[0];
                activeConversations.unshift(item);
            }
            
            renderActiveConversations();
        }
        
        function renderActiveConversations() {
            const container = document.getElementById('messagesList');
            const emptyState = document.getElementById('emptyMessagesState');
            if (!container) return;
            
            // Combine groups and active DMs, sort by last activity
            const allConversations = [...activeConversations];
            
            // Add groups to conversations
            userGroups.forEach(group => {
                const exists = allConversations.find(c => c.type === 'group' && c.id === group.id);
                if (!exists) {
                    allConversations.push({
                        type: 'group',
                        id: group.id,
                        name: group.name,
                        avatar: group.avatar_emoji || '👥',
                        members: group.members,
                        lastMessage: group.last_message,
                        lastActivity: group.last_message_time || group.created_at
                    });
                }
            });
            
            // Add bots to conversations
            userBots.forEach(bot => {
                const exists = allConversations.find(c => c.type === 'bot' && c.id === bot.id);
                if (!exists) {
                    allConversations.push({
                        type: 'bot',
                        id: bot.id,
                        name: bot.name,
                        avatar: bot.avatar,
                        description: bot.description,
                        commands: bot.commands,
                        lastMessage: 'Type a command to get started',
                        lastActivity: new Date().toISOString() // Keep bots near top
                    });
                }
            });
            
            // Sort by last activity (most recent first)
            allConversations.sort((a, b) => {
                const timeA = new Date(a.lastActivity || 0);
                const timeB = new Date(b.lastActivity || 0);
                return timeB - timeA;
            });
            
            if (allConversations.length === 0) {
                if (emptyState) emptyState.style.display = 'block';
                container.innerHTML = '';
                container.appendChild(emptyState);
                return;
            }
            
            if (emptyState) emptyState.style.display = 'none';
            
            const html = allConversations.map(conv => {
                if (conv.type === 'group') {
                    return `
                        <div class="contact group-item" data-group-id="${conv.id}" onclick="selectGroup('${conv.id}')">
                            <div class="contact-avatar" style="background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));">
                                ${conv.avatar || '👥'}
                            </div>
                            <div class="contact-info">
                                <div class="contact-name">${conv.name}</div>
                                <div class="contact-status">${conv.lastMessage || `${conv.members?.length || 0} members`}</div>
                            </div>
                            <span class="conv-badge group-badge">Group</span>
                        </div>`;
                } else if (conv.type === 'bot') {
                    return `
                        <div class="contact bot-item" data-bot-id="${conv.id}" onclick="selectBot('${conv.id}')">
                            <div class="contact-avatar" style="background: linear-gradient(135deg, #10b981, #059669); font-size: 1.25rem;">
                                ${conv.avatar || '🤖'}
                            </div>
                            <div class="contact-info">
                                <div class="contact-name">${conv.name}</div>
                                <div class="contact-status">${conv.lastMessage || conv.description}</div>
                            </div>
                            <span class="conv-badge bot-badge" style="background: #10b981;">Bot</span>
                        </div>`;
                } else {
                    // Direct message
                    return `
                        <div class="contact dm-item" data-username="${conv.id}" onclick="selectContact('${conv.id}')">
                            <div class="contact-avatar">
                                ${conv.id[0].toUpperCase()}
                                <div class="status-indicator ${onlineUsers.has(conv.id) ? 'online' : ''}" id="status-${conv.id}"></div>
                            </div>
                            <div class="contact-info">
                                <div class="contact-name">${conv.name || conv.id}</div>
                                <div class="contact-status">${conv.lastMessage || 'Click to continue chatting'}</div>
                            </div>
                        </div>`;
                }
            }).join('');
            
            container.innerHTML = html;
        }
        
        function renderGroups(groups, prepend = false) {
            userGroups = groups;
            renderActiveConversations();
        }
        
        let currentGroup = null; // Currently selected group
        let currentBot = null; // Currently selected bot
        let currentChatType = 'dm'; // 'dm', 'group', or 'bot'
        let botMessages = {}; // Store messages per bot
        
        function selectBot(botId) {
            const bot = userBots.find(b => b.id === botId);
            if (!bot) {
                showToast('Bot not found', 'error');
                return;
            }
            
            // Clear other states
            currentFriend = null;
            currentGroup = null;
            currentBot = bot;
            currentChatType = 'bot';
            
            // Update UI
            document.querySelectorAll('.contact').forEach(c => c.classList.remove('active'));
            const botEl = document.querySelector(`[data-bot-id="${botId}"]`);
            if (botEl) botEl.classList.add('active');
            
            document.getElementById('empty-state').style.display = 'none';
            document.getElementById('active-chat').classList.add('visible');
            document.getElementById('active-chat').style.display = 'flex';
            
            // Hide shared notes panel
            const notesPanel = document.getElementById('sharedNotesPanel');
            if (notesPanel) {
                notesPanel.style.display = 'none';
                sharedNotesVisible = false;
            }
            
            // Update header
            const chatUsername = document.getElementById('chat-username');
            const chatAvatar = document.getElementById('chat-avatar');
            const chatStatusText = document.getElementById('chat-status-text');
            
            if (chatUsername) chatUsername.textContent = bot.name;
            if (chatAvatar) {
                chatAvatar.textContent = bot.avatar || '🤖';
                chatAvatar.style.background = 'linear-gradient(135deg, #10b981, #059669)';
            }
            if (chatStatusText) {
                chatStatusText.innerHTML = `<span style="color: #10b981;">● Online</span> • Bot • ${bot.commands?.length || 0} commands`;
            }
            
            // Show bot commands help
            renderBotChat(bot);
        }
        
        function renderBotChat(bot) {
            const chatContainer = document.getElementById('messages');
            if (!chatContainer) return;
            
            // Get saved messages for this bot, or create welcome message
            if (!botMessages[bot.id]) {
                botMessages[bot.id] = [{
                    type: 'bot',
                    content: `👋 **Welcome to ${bot.name}!**\n\n${bot.description}\n\n**Available Commands:**\n${bot.commands.map(cmd => `• \`${cmd.command}\` - ${cmd.description}`).join('\n')}\n\nType a command to get started!`,
                    timestamp: new Date().toISOString()
                }];
            }
            
            const messages = botMessages[bot.id];
            
            chatContainer.innerHTML = messages.map(msg => {
                if (msg.type === 'bot') {
                    return `
                        <div class="message-wrapper received">
                            <div class="message-bubble received" style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(5, 150, 105, 0.1)); border: 1px solid rgba(16, 185, 129, 0.3);">
                                <div class="message-content" style="white-space: pre-wrap;">${formatBotMessage(msg.content)}</div>
                                <div class="message-time">${formatTime(msg.timestamp)}</div>
                            </div>
                        </div>`;
                } else {
                    return `
                        <div class="message-wrapper sent">
                            <div class="message-bubble sent">
                                <div class="message-content">${msg.content}</div>
                                <div class="message-time">${formatTime(msg.timestamp)}</div>
                            </div>
                        </div>`;
                }
            }).join('');
            
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        function formatBotMessage(content) {
            // Simple markdown-like formatting
            return content
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/`(.*?)`/g, '<code style="background: rgba(255,255,255,0.1); padding: 2px 6px; border-radius: 4px;">$1</code>')
                .replace(/\n/g, '<br>');
        }
        
        async function sendBotCommand(command) {
            if (!currentBot) return;
            
            // Add user message
            const userMsg = {
                type: 'user',
                content: command,
                timestamp: new Date().toISOString()
            };
            
            if (!botMessages[currentBot.id]) {
                botMessages[currentBot.id] = [];
            }
            botMessages[currentBot.id].push(userMsg);
            renderBotChat(currentBot);
            
            // Parse command
            const parts = command.trim().split(' ');
            const cmd = parts[0];
            const args = parts.slice(1);
            
            try {
                const response = await fetch(`/api/bots/${currentBot.id}/command`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ command: cmd, args: args })
                });
                
                const data = await response.json();
                
                // Add bot response
                const botMsg = {
                    type: 'bot',
                    content: data.response || 'No response from bot',
                    timestamp: new Date().toISOString()
                };
                botMessages[currentBot.id].push(botMsg);
                renderBotChat(currentBot);
                
            } catch (error) {
                console.error('Bot command error:', error);
                const errorMsg = {
                    type: 'bot',
                    content: '❌ Error processing command. Please try again.',
                    timestamp: new Date().toISOString()
                };
                botMessages[currentBot.id].push(errorMsg);
                renderBotChat(currentBot);
            }
        }
        
        function selectGroup(groupId) {
            const group = userGroups.find(g => g.id === groupId);
            if (!group) {
                showToast('Group not found', 'error');
                return;
            }
            
            // Clear DM state
            currentFriend = null;
            currentGroup = group;
            currentChatType = 'group';
            
            // Update UI
            document.querySelectorAll('.contact').forEach(c => c.classList.remove('active'));
            const groupEl = document.querySelector(`[data-group-id="${groupId}"]`);
            if (groupEl) groupEl.classList.add('active');
            
            document.getElementById('empty-state').style.display = 'none';
            document.getElementById('active-chat').classList.add('visible');
            document.getElementById('active-chat').style.display = 'flex';
            
            // Hide shared notes panel when switching chats
            const notesPanel = document.getElementById('sharedNotesPanel');
            if (notesPanel) {
                notesPanel.style.display = 'none';
                sharedNotesVisible = false;
            }
            
            // Clear unlocked notes cache
            unlockedNotes = {};
            
            // Update header for group
            document.getElementById('chat-avatar').textContent = group.avatar_emoji || '👥';
            document.getElementById('chat-avatar').style.background = 'linear-gradient(135deg, var(--accent-primary), var(--accent-secondary))';
            document.getElementById('chat-avatar').style.fontSize = '1.25rem';
            document.getElementById('chat-username').textContent = group.name;
            document.getElementById('chat-status-dot').style.display = 'none';
            document.getElementById('chat-status-text').textContent = `${group.members.length} members`;
            
            // Join group room via socket
            socket.emit('join_group', { group_id: groupId });
            
            // Load shared notes for this group
            loadGroupSharedNotes(groupId);
            
            document.getElementById('message-input').focus();
        }
        
        function loadGroupSharedNotes(groupId) {
            socket.emit('get_group_notes', { group_id: groupId });
        }
        
        // Track when a DM conversation becomes active
        function trackDMConversation(username, lastMessage = null) {
            addActiveConversation('dm', {
                id: username,
                name: username,
                lastMessage: lastMessage
            });
        }
        
        // Toggle All Users section visibility
        function toggleAllUsers() {
            const section = document.getElementById('allUsersSection');
            const list = document.getElementById('allUsersList');
            const label = section.querySelector('.section-label');
            
            if (list.style.display === 'none') {
                list.style.display = 'block';
                label.classList.add('expanded');
            } else {
                list.style.display = 'none';
                label.classList.remove('expanded');
            }
        }
        
        function updateOnlineStatus() {
            document.querySelectorAll('.contact').forEach(contact => {
                const username = contact.dataset.username;
                const statusDot = document.getElementById(`status-${username}`);
                if (statusDot) {
                    statusDot.classList.toggle('online', onlineUsers.has(username));
                }
            });
            
            if (currentFriend) {
                const isOnline = onlineUsers.has(currentFriend);
                document.getElementById('chat-status-dot').style.display = isOnline ? 'block' : 'none';
                document.getElementById('chat-status-text').textContent = isOnline ? 'Online' : 'Offline';
            }
        }
        
        // ============================================
        // CHAT FUNCTIONS
        // ============================================
        
        function selectContact(username) {
            // Clear group state
            currentGroup = null;
            currentChatType = 'dm';
            currentFriend = username;
            
            document.querySelectorAll('.contact').forEach(c => c.classList.remove('active'));
            const contactEl = document.querySelector(`[data-username="${username}"]`);
            if (contactEl) contactEl.classList.add('active');
            
            document.getElementById('empty-state').style.display = 'none';
            document.getElementById('active-chat').classList.add('visible');
            document.getElementById('active-chat').style.display = 'flex';
            
            // Hide shared notes panel when switching chats
            const notesPanel = document.getElementById('sharedNotesPanel');
            if (notesPanel) {
                notesPanel.style.display = 'none';
                sharedNotesVisible = false;
            }
            
            // Clear unlocked notes cache for new chat
            unlockedNotes = {};
            
            // Reset avatar styling for DM
            document.getElementById('chat-avatar').textContent = username[0].toUpperCase();
            document.getElementById('chat-avatar').style.background = '';
            document.getElementById('chat-avatar').style.fontSize = '';
            document.getElementById('chat-username').textContent = username;
            updateOnlineStatus();
            
            socket.emit('join_chat', { friend: username });
            
            // Track this as an active conversation
            trackDMConversation(username);
            
            document.getElementById('message-input').focus();
        }
        
        async function displayMessage(msg) {
            const messagesDiv = document.getElementById('messages');
            const sharedSecret = getSharedSecret(myUsername, currentFriend);
            
            const decryptedText = await decryptMessage(msg.encrypted, sharedSecret);
            
            const isSent = msg.from === myUsername;
            const time = new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            const messageId = msg.id || '';
            
            // Check if message has expiry
            let expiryHtml = '';
            if (msg.expires_at) {
                const expiryDate = new Date(msg.expires_at);
                const expiryText = formatExpiryTime(expiryDate);
                expiryHtml = `<span class="message-expiry">⏱️ ${expiryText}</span>`;
            }
            
            // Delete button (only for sent messages)
            const deleteBtn = isSent ? `
                <div class="message-actions">
                    <button class="message-action-btn delete" onclick="deleteMessage('${messageId}')" title="Delete message">
                        🗑️
                    </button>
                </div>
            ` : '';
            
            const messageEl = document.createElement('div');
            messageEl.className = `message ${isSent ? 'sent' : 'received'}`;
            messageEl.id = `msg-${messageId}`;
            messageEl.innerHTML = `
                <div class="message-wrapper">
                    <div class="message-bubble">${escapeHtml(decryptedText)}</div>
                    ${deleteBtn}
                </div>
                <div class="message-meta">
                    <span class="message-encrypted">
                        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                            <path d="M7 11V7a5 5 0 0110 0v4"/>
                        </svg>
                        encrypted
                    </span>
                    ${expiryHtml}
                    <span class="message-time">${time}</span>
                </div>
            `;
            
            messagesDiv.appendChild(messageEl);
        }
        
        function formatExpiryTime(date) {
            const now = new Date();
            const diff = date - now;
            
            if (diff <= 0) return 'expiring';
            
            const days = Math.floor(diff / (1000 * 60 * 60 * 24));
            const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            
            if (days > 30) return `${Math.floor(days / 30)}mo`;
            if (days > 0) return `${days}d`;
            if (hours > 0) return `${hours}h`;
            return 'soon';
        }
        
        function showSystemMessage(text, type = 'fresh-start') {
            const messagesDiv = document.getElementById('messages');
            
            const systemMsg = document.createElement('div');
            systemMsg.className = 'system-message';
            systemMsg.innerHTML = `
                <div class="system-message-content ${type}">
                    ${text}
                </div>
            `;
            
            messagesDiv.appendChild(systemMsg);
            scrollToBottom();
        }
        
        async function sendMessage() {
            const input = document.getElementById('message-input');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Haptic feedback on send (iOS native)
            if (window.NativeBridge?.hapticFeedback) {
                window.NativeBridge.hapticFeedback('light');
            }
            
            // Handle bot commands
            if (currentChatType === 'bot' && currentBot) {
                input.value = '';
                input.style.height = 'auto';
                input.focus();
                sendBotCommand(message);
                return;
            }
            
            // Handle group messages
            if (currentChatType === 'group' && currentGroup) {
                socket.emit('group_message', {
                    group_id: currentGroup.id,
                    content: message,
                    encrypted: false // Group messages stored as plaintext for now
                });
                
                input.value = '';
                input.style.height = 'auto';
                input.focus();
                return;
            }
            
            // Handle DM messages
            if (!currentFriend) return;
            
            const sharedSecret = getSharedSecret(myUsername, currentFriend);
            const encrypted = await encryptMessage(message, sharedSecret);
            
            socket.emit('send_message', {
                to: currentFriend,
                encrypted_message: encrypted
            });
            
            input.value = '';
            input.style.height = 'auto';
            input.focus();
        }
        
        // Display a group message
        async function displayGroupMessage(msg) {
            const messagesDiv = document.getElementById('messages');
            
            const isSent = msg.sender === myUsername;
            const time = new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            const messageId = msg.id || '';
            
            const messageEl = document.createElement('div');
            messageEl.className = `message ${isSent ? 'sent' : 'received'}`;
            messageEl.id = `msg-${messageId}`;
            
            // Show sender name for received messages in groups
            const senderHtml = !isSent ? `<div class="message-sender" style="font-size: 0.75rem; color: var(--accent-primary); margin-bottom: 0.25rem; font-weight: 500;">${msg.sender}</div>` : '';
            
            messageEl.innerHTML = `
                <div class="message-bubble">
                    ${senderHtml}
                    <div class="message-text">${escapeHtml(msg.content)}</div>
                    <div class="message-info">
                        <span class="message-time">${time}</span>
                    </div>
                </div>
                ${isSent ? `
                <div class="message-actions">
                    <button class="msg-action-btn" onclick="deleteMessage('${messageId}', true)" title="Delete for everyone">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
                        </svg>
                    </button>
                </div>` : ''}
            `;
            
            messagesDiv.appendChild(messageEl);
        }
        
        function handleKeyDown(event) {
            const calcPreview = document.getElementById('calcPreview');
            const isCalcVisible = calcPreview && calcPreview.classList.contains('show');
            
            // Enter key
            if (event.key === 'Enter') {
                // Shift+Enter: Add new line
                if (event.shiftKey) {
                    return; // Allow default behavior
                }
                
                // If calculator is showing, insert results
                if (isCalcVisible && lastCalculations.length > 0) {
                    event.preventDefault();
                    insertCalculatedText();
                    return;
                }
                
                // Plain Enter: Send message
                event.preventDefault();
                sendMessage();
            }
        }
        
        function autoResize(textarea) {
            textarea.style.height = 'auto';
            textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
        }
        
        function scrollToBottom() {
            const messagesDiv = document.getElementById('messages');
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        // ============================================
        // CHAT SETTINGS & MESSAGE DELETION
        // ============================================
        
        let currentChatSettings = { auto_delete: 'never' };
        
        function openChatSettings() {
            if (!currentFriend) return;
            
            // Set current setting in modal
            const currentValue = currentChatSettings.auto_delete || 'never';
            document.querySelector(`input[name="auto_delete"][value="${currentValue}"]`).checked = true;
            
            document.getElementById('chatSettingsModal').classList.add('show');
        }
        
        function saveChatSettings() {
            const selectedOption = document.querySelector('input[name="auto_delete"]:checked');
            if (!selectedOption) return;
            
            const period = selectedOption.value;
            
            socket.emit('set_auto_delete', {
                friend: currentFriend,
                period: period
            });
            
            closeModal('chatSettingsModal');
        }
        
        function updateAutoDeleteUI(period) {
            // Update the badge in chat header if needed
            const existingBadge = document.querySelector('.auto-delete-badge');
            if (existingBadge) {
                existingBadge.remove();
            }
            
            if (period && period !== 'never') {
                const label = {
                    '1_day': '1 day',
                    '1_week': '1 week',
                    '1_month': '1 month',
                    '1_year': '1 year'
                }[period] || period;
                
                const badge = document.createElement('div');
                badge.className = 'auto-delete-badge';
                badge.innerHTML = `⏱️ Auto-delete: ${label}`;
                
                const encBadge = document.querySelector('.encryption-badge');
                if (encBadge) {
                    encBadge.insertAdjacentElement('afterend', badge);
                }
            }
        }
        
        function confirmClearChat() {
            document.getElementById('clearChatFriend').textContent = currentFriend;
            document.getElementById('clearChatModal').classList.add('show');
        }
        
        function clearChat() {
            if (!currentFriend) return;
            
            socket.emit('clear_chat', {
                friend: currentFriend
            });
        }
        
        function deleteMessage(messageId) {
            if (!messageId || !currentFriend) return;
            
            socket.emit('delete_message', {
                friend: currentFriend,
                message_id: messageId
            });
        }
        
        // ============================================
        // SHARED NOTES FUNCTIONS
        // ============================================
        
        let sharedNotesVisible = false;
        let unlockedNotes = {};  // Cache of unlocked notes
        
        function toggleSharedNotes() {
            const panel = document.getElementById('sharedNotesPanel');
            sharedNotesVisible = !sharedNotesVisible;
            panel.style.display = sharedNotesVisible ? 'block' : 'none';
            
            // Load notes for both DM and group chats
            if (sharedNotesVisible) {
                if (currentChatType === 'group' && currentGroup) {
                    loadSharedNotes();
                } else if (currentFriend) {
                    loadSharedNotes();
                }
            }
        }
        
        function updateNotesBadge(notes) {
            const badge = document.getElementById('notesBadge');
            if (badge) {
                badge.style.display = (notes && notes.length > 0) ? 'block' : 'none';
            }
        }
        
        function loadSharedNotes() {
            // Handle group notes
            if (currentChatType === 'group' && currentGroup) {
                socket.emit('get_group_notes', {
                    group_id: currentGroup.id
                });
                return;
            }
            
            // Handle DM notes
            if (!currentFriend) return;
            
            socket.emit('get_shared_notes', {
                friend: currentFriend
            });
        }
        
        function renderSharedNotes(notes) {
            const container = document.getElementById('sharedNotesList');
            console.log('📝 Rendering notes:', notes, 'Container:', container);
            
            if (!notes || notes.length === 0) {
                container.innerHTML = `
                    <div class="empty-notes">
                        <div class="empty-notes-icon">📝</div>
                        No shared notes yet.<br>
                        <span style="opacity: 0.7;">Create one to securely share with this conversation.</span>
                    </div>`;
                return;
            }
            
            container.innerHTML = notes.map(note => {
                let iconClass = 'locked';
                let iconEmoji = '🔒';
                let primaryBtn = '';
                let editBtn = '';
                let deleteBtn = '';
                let statusBadge = '';
                
                // Check if there's a pending delete request
                const deleteRequests = note.delete_requested_by || [];
                const iRequestedDelete = deleteRequests.includes(myUsername);
                const otherRequestedDelete = deleteRequests.length > 0 && !iRequestedDelete;
                
                // Check if note was edited
                const editedBadge = note.last_edited_by ? 
                    `<span class="note-badge edited">Edited</span>` : '';
                
                if (unlockedNotes[note.id]) {
                    iconClass = 'unlocked';
                    iconEmoji = '🔓';
                    primaryBtn = `<button class="note-action-btn view" onclick="viewUnlockedNote('${note.id}')">👁️ View</button>`;
                    editBtn = `<button class="note-action-btn edit" onclick="openEditNoteModal('${note.id}')" title="Edit note">✏️ Edit</button>`;
                } else if (!note.has_phrase) {
                    iconClass = 'pending';
                    iconEmoji = '⏳';
                    primaryBtn = `<button class="note-action-btn set-phrase" onclick="openSetPhraseModal('${note.id}', '${escapeHtml(note.title)}', '${note.created_by}')">🔑 Set Phrase</button>`;
                    statusBadge = `<div class="note-status needs-phrase">⚠️ Phrase required to access</div>`;
                } else {
                    primaryBtn = `<button class="note-action-btn unlock" onclick="openUnlockModal('${note.id}', '${escapeHtml(note.title)}')">🔓 Unlock</button>`;
                }
                
                // Delete button logic
                if (otherRequestedDelete && !iRequestedDelete) {
                    iconClass = 'delete-pending';
                    iconEmoji = '⚠️';
                    statusBadge = `<div class="note-status delete-requested">🗑️ ${currentFriend} wants to delete</div>`;
                    deleteBtn = `<button class="note-action-btn confirm-delete" onclick="confirmDeleteNote('${note.id}')" title="Agree to delete">✓ Agree</button>`;
                } else if (iRequestedDelete) {
                    statusBadge = `<div class="note-status delete-requested">⏳ Waiting for ${currentFriend}</div>`;
                    deleteBtn = `<button class="note-action-btn delete" onclick="cancelDeleteNote('${note.id}')" title="Cancel">↩️</button>`;
                } else {
                    deleteBtn = `<button class="note-action-btn delete" onclick="requestDeleteNote('${note.id}')" title="Request to delete">🗑️</button>`;
                }
                
                const date = new Date(note.created_at);
                const timeStr = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) + 
                               ' at ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                
                // Build meta text
                let metaText = `Created by ${note.created_by} <span class="note-meta-divider">•</span> ${timeStr}`;
                if (note.last_edited_by) {
                    const editDate = new Date(note.last_edited_at);
                    const editTimeStr = editDate.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                    metaText += ` <span class="note-meta-divider">•</span> Edited by ${note.last_edited_by}`;
                }
                
                return `
                    <div class="shared-note-item">
                        <div class="note-icon ${iconClass}">${iconEmoji}</div>
                        <div class="note-info">
                            <div class="note-title">
                                <span class="note-title-text">${escapeHtml(note.title)}</span>
                                ${editedBadge}
                            </div>
                            <div class="note-meta">${metaText}</div>
                            ${statusBadge}
                        </div>
                        <div class="note-actions">
                            <div class="note-actions-row">
                                ${primaryBtn}
                                ${editBtn}
                            </div>
                            <div class="note-actions-row">
                                ${deleteBtn}
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        function openCreateNoteModal() {
            // Handle group chats
            if (currentChatType === 'group' && currentGroup) {
                document.getElementById('noteRecipientName').textContent = currentGroup.name + ' (Group)';
                document.getElementById('noteTitle').value = '';
                document.getElementById('noteContent').value = '';
                document.getElementById('creatorPhrase').value = '';
                document.getElementById('createNoteModal').classList.add('show');
                return;
            }
            
            // Handle DM chats
            if (!currentFriend) return;
            
            document.getElementById('noteRecipientName').textContent = currentFriend;
            document.getElementById('noteTitle').value = '';
            document.getElementById('noteContent').value = '';
            document.getElementById('creatorPhrase').value = '';
            document.getElementById('createNoteModal').classList.add('show');
        }
        
        function createSharedNote() {
            const title = document.getElementById('noteTitle').value.trim();
            const content = document.getElementById('noteContent').value.trim();
            const phrase = document.getElementById('creatorPhrase').value.trim();
            
            if (!title || !content || !phrase) {
                showToast('Please fill in all fields', 'error');
                return;
            }
            
            if (phrase.length < 4) {
                showToast('Phrase must be at least 4 characters', 'error');
                return;
            }
            
            // Handle group notes
            if (currentChatType === 'group' && currentGroup) {
                console.log('Creating group note:', { group: currentGroup.name, title, content });
                
                socket.emit('create_group_note', {
                    group_id: currentGroup.id,
                    title: title,
                    content: content,
                    phrase: phrase
                });
            } else if (currentFriend) {
                // Handle DM notes
                console.log('Creating shared note:', { friend: currentFriend, title, content });
                
                socket.emit('create_shared_note', {
                    friend: currentFriend,
                    title: title,
                    content: content,
                    phrase: phrase
                });
            } else {
                showToast('No active chat selected', 'error');
                return;
            }
            
            closeModal('createNoteModal');
            showToast('📝 Shared note created!', 'success');
        }
        
        function showSetPhrasePrompt(data) {
            // Show a toast notification prompting user to set their phrase
            document.getElementById('phraseNoteCreator').textContent = data.created_by;
            document.getElementById('phraseNoteTitle').textContent = data.title;
            document.getElementById('setPhraseNoteId').value = data.note_id;
            document.getElementById('userPhrase').value = '';
            document.getElementById('setPhraseModal').classList.add('show');
        }
        
        function openSetPhraseModal(noteId, title, creator) {
            document.getElementById('phraseNoteCreator').textContent = creator;
            document.getElementById('phraseNoteTitle').textContent = title;
            document.getElementById('setPhraseNoteId').value = noteId;
            document.getElementById('userPhrase').value = '';
            document.getElementById('setPhraseModal').classList.add('show');
        }
        
        function setNotePhrase() {
            const noteId = document.getElementById('setPhraseNoteId').value;
            const phrase = document.getElementById('userPhrase').value.trim();
            
            if (!phrase) {
                showToast('Please enter a phrase', 'error');
                return;
            }
            
            if (phrase.length < 4) {
                showToast('Phrase must be at least 4 characters', 'error');
                return;
            }
            
            socket.emit('set_note_phrase', {
                note_id: noteId,
                phrase: phrase
            });
        }
        
        function openUnlockModal(noteId, title) {
            document.getElementById('unlockNoteTitle').textContent = title;
            document.getElementById('unlockNoteId').value = noteId;
            document.getElementById('unlockPhrase').value = '';
            document.getElementById('unlockError').style.display = 'none';
            document.getElementById('unlockNoteModal').classList.add('show');
            
            setTimeout(() => {
                document.getElementById('unlockPhrase').focus();
            }, 100);
        }
        
        function unlockNote() {
            const noteId = document.getElementById('unlockNoteId').value;
            const phrase = document.getElementById('unlockPhrase').value.trim();
            
            if (!phrase) {
                document.getElementById('unlockError').textContent = 'Please enter your phrase';
                document.getElementById('unlockError').style.display = 'block';
                return;
            }
            
            document.getElementById('unlockError').style.display = 'none';
            
            socket.emit('unlock_note', {
                note_id: noteId,
                phrase: phrase
            });
        }
        
        function showUnlockedNote(data) {
            document.getElementById('viewNoteTitle').textContent = data.title;
            document.getElementById('viewNoteContent').textContent = data.content;
            document.getElementById('viewNoteCreator').textContent = data.created_by;
            document.getElementById('viewNoteId').value = data.note_id;
            
            // Show edit info if available
            const editInfoEl = document.getElementById('viewNoteEditInfo');
            if (data.last_edited_by) {
                const editDate = new Date(data.last_edited_at);
                editInfoEl.textContent = `Last edited by ${data.last_edited_by}`;
            } else {
                editInfoEl.textContent = '';
            }
            
            document.getElementById('viewNoteModal').classList.add('show');
            
            // Refresh the notes list to show unlocked status
            loadSharedNotes();
        }
        
        function viewUnlockedNote(noteId) {
            const note = unlockedNotes[noteId];
            if (note) {
                showUnlockedNote(note);
            }
        }
        
        // ============================================
        // NOTE EDITING FUNCTIONS
        // ============================================
        
        function openEditNoteModal(noteId) {
            const note = unlockedNotes[noteId];
            if (!note) {
                showToast('Please unlock the note first to edit it', 'error');
                return;
            }
            
            document.getElementById('editNoteId').value = noteId;
            document.getElementById('editNoteTitle').value = note.title;
            document.getElementById('editNoteContent').value = note.content;
            document.getElementById('editNotePhrase').value = '';
            
            document.getElementById('editNoteModal').classList.add('show');
        }
        
        function editFromViewModal() {
            const noteId = document.getElementById('viewNoteId').value;
            closeModal('viewNoteModal');
            openEditNoteModal(noteId);
        }
        
        function saveNoteEdit() {
            const noteId = document.getElementById('editNoteId').value;
            const newTitle = document.getElementById('editNoteTitle').value.trim();
            const newContent = document.getElementById('editNoteContent').value.trim();
            const phrase = document.getElementById('editNotePhrase').value.trim();
            
            if (!newTitle && !newContent) {
                showToast('Please enter a title or content', 'error');
                return;
            }
            
            if (!phrase) {
                showToast('Please enter your phrase to save changes', 'error');
                return;
            }
            
            socket.emit('edit_shared_note', {
                note_id: noteId,
                title: newTitle,
                content: newContent,
                phrase: phrase,
                friend: currentFriend
            });
        }
        
        // ============================================
        // NOTE DELETION FUNCTIONS
        // ============================================
        
        function requestDeleteNote(noteId) {
            if (!currentFriend) return;
            
            socket.emit('request_delete_note', {
                note_id: noteId,
                friend: currentFriend
            });
            
            showToast('Delete request sent. Waiting for ' + currentFriend + ' to agree.', 'info');
        }
        
        function confirmDeleteNote(noteId) {
            if (!currentFriend) return;
            
            socket.emit('request_delete_note', {
                note_id: noteId,
                friend: currentFriend
            });
        }
        
        function cancelDeleteNote(noteId) {
            if (!currentFriend) return;
            
            socket.emit('cancel_delete_request', {
                note_id: noteId,
                friend: currentFriend
            });
            
            showToast('Delete request cancelled', 'info');
        }
        
        // ============================================
        // CALCULATOR FUNCTIONS
        // ============================================
        
        let lastCalculations = [];
        let lastTotal = 0;
        
        function detectCalculations(text) {
            const preview = document.getElementById('calcPreview');
            const suggestionsContainer = document.getElementById('calcSuggestions');
            
            // Pattern to match math expressions: number operator number
            // Supports: x, *, ×, +, -, /, ÷
            const mathPattern = /(\d+(?:\.\d+)?)\s*([x×*+\-\/÷])\s*(\d+(?:\.\d+)?)/gi;
            
            const lines = text.split('\n');
            const calculations = [];
            
            lines.forEach(line => {
                const matches = line.matchAll(mathPattern);
                for (const match of matches) {
                    const num1 = parseFloat(match[1]);
                    const operator = match[2].toLowerCase();
                    const num2 = parseFloat(match[3]);
                    
                    let result;
                    let displayOperator = operator;
                    
                    switch(operator) {
                        case 'x':
                        case '×':
                        case '*':
                            result = num1 * num2;
                            displayOperator = '×';
                            break;
                        case '+':
                            result = num1 + num2;
                            break;
                        case '-':
                            result = num1 - num2;
                            break;
                        case '/':
                        case '÷':
                            result = num2 !== 0 ? num1 / num2 : 0;
                            displayOperator = '÷';
                            break;
                        default:
                            continue;
                    }
                    
                    calculations.push({
                        expression: `${num1}${displayOperator}${num2}`,
                        original: match[0],
                        result: result
                    });
                }
            });
            
            if (calculations.length > 0) {
                // Build iOS-style suggestion chips
                let html = '';
                
                if (calculations.length === 1) {
                    // Single calculation - show 3 options like iOS
                    const calc = calculations[0];
                    const resultStr = formatNumber(calc.result);
                    
                    html = `
                        <button class="calc-chip expression" onclick="insertCalcText('"${calc.expression}="')">"${calc.expression}="</button>
                        <button class="calc-chip full" onclick="insertCalcText('${calc.expression}=${resultStr}')">${calc.expression}=${resultStr}</button>
                        <button class="calc-chip result" onclick="insertCalcText('${resultStr}')">${resultStr}</button>
                    `;
                } else {
                    // Multiple calculations - show each result + total
                    calculations.forEach(calc => {
                        const resultStr = formatNumber(calc.result);
                        html += `<button class="calc-chip full" onclick="insertCalcText('${calc.expression}=${resultStr}')">${calc.expression}=${resultStr}</button>`;
                    });
                    
                    // Add total chip
                    const total = calculations.reduce((sum, calc) => sum + calc.result, 0);
                    const totalStr = formatNumber(total);
                    html += `<button class="calc-total-chip" onclick="insertCalcText('Total: ${totalStr}')"><span class="calc-total-label">Total</span> ${totalStr}</button>`;
                    lastTotal = total;
                }
                
                suggestionsContainer.innerHTML = html;
                lastCalculations = calculations;
                preview.classList.add('show');
            } else {
                lastCalculations = [];
                lastTotal = 0;
                preview.classList.remove('show');
            }
        }
        
        function insertCalcText(text) {
            const input = document.getElementById('message-input');
            if (input) {
                // Replace the current expression with the selected text
                const currentText = input.value;
                const mathPattern = /(\d+(?:\.\d+)?)\s*([x×*+\-\/÷])\s*(\d+(?:\.\d+)?)/gi;
                
                // Find and replace the last expression
                const newText = currentText.replace(mathPattern, text);
                input.value = newText;
                input.focus();
                
                // Hide calculator
                document.getElementById('calcPreview').classList.remove('show');
                lastCalculations = [];
            }
        }
        
        function formatNumber(num) {
            // Format number with commas for thousands and limit decimal places
            if (Number.isInteger(num)) {
                return num.toLocaleString();
            }
            return num.toLocaleString(undefined, { maximumFractionDigits: 2 });
        }
        
        function insertCalculatedText() {
            if (lastCalculations.length === 0) return;
            
            const textarea = document.getElementById('message-input');
            let text = textarea.value;
            
            // Build the result text
            let resultLines = lastCalculations.map(calc => 
                `${calc.expression}=${formatNumber(calc.result)}`
            );
            
            // Add total if multiple calculations
            if (lastCalculations.length > 1) {
                resultLines.push(`Total=${formatNumber(lastTotal)}`);
            }
            
            // Replace the original text with the calculated results
            textarea.value = resultLines.join('\n');
            
            // Hide the preview
            document.getElementById('calcPreview').classList.remove('show');
            
            // Resize textarea
            autoResize(textarea);
            
            // Focus back on textarea
            textarea.focus();
        }
        
        function showToast(message, type = 'info') {
            // Remove existing toasts
            const existing = document.querySelector('.simple-toast');
            if (existing) existing.remove();
            
            const toast = document.createElement('div');
            toast.className = 'simple-toast';
            toast.style.cssText = `
                position: fixed;
                top: 1rem;
                right: 1rem;
                padding: 0.75rem 1.25rem;
                background: ${type === 'error' ? '#ef4444' : type === 'success' ? '#10b981' : 'var(--bg-card)'};
                color: white;
                border-radius: var(--radius-md);
                font-size: 0.875rem;
                font-weight: 500;
                z-index: 3000;
                animation: slideIn 0.3s ease;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
            `;
            toast.textContent = message;
            document.body.appendChild(toast);
            
            setTimeout(() => {
                toast.style.animation = 'fadeOut 0.3s ease forwards';
                setTimeout(() => toast.remove(), 300);
            }, 3000);
        }
        
        // Override selectContact to also load shared notes
        const originalSelectContact = selectContact;
        selectContact = function(username) {
            originalSelectContact(username);
            
            // Reset shared notes state
            unlockedNotes = {};
            if (sharedNotesVisible) {
                loadSharedNotes();
            }
        };
        
        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            initSocket();
            
            // Check for navigation from channels page
            if (localStorage.getItem('openNewMessage')) {
                localStorage.removeItem('openNewMessage');
                setTimeout(() => startNewMessage(), 300);
            }
            if (localStorage.getItem('openNewGroup')) {
                localStorage.removeItem('openNewGroup');
                setTimeout(() => startNewGroup(), 300);
            }
            if (localStorage.getItem('selectUser')) {
                const user = localStorage.getItem('selectUser');
                localStorage.removeItem('selectUser');
                setTimeout(() => selectContact(user), 300);
            }
        });
        
        // ============================================
        // PWA Service Worker Registration
        // ============================================
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/static/sw.js')
                    .then((registration) => {
                        console.log('✅ Menza PWA ready:', registration.scope);
                    })
                    .catch((error) => {
                        console.log('⚠️ SW registration failed:', error);
                    });
            });
        }
        
        // ============================================
        // VOICE & VIDEO CALL FUNCTIONS
        // ============================================
        
        // Call State
        let currentCall = null;
        let localStream = null;
        let screenStream = null;
        let peerConnections = {}; // username -> RTCPeerConnection
        let callDurationInterval = null;
        let callStartTime = null;
        let incomingCallData = null;
        let isMuted = false;
        let isVideoOff = false;
        let isScreenSharing = false;
        let canSpeak = true; // For channel calls
        
        // ICE Servers (STUN/TURN)
        const iceConfig = {
            iceServers: [
                { urls: 'stun:stun.l.google.com:19302' },
                { urls: 'stun:stun1.l.google.com:19302' },
                { urls: 'stun:stun2.l.google.com:19302' }
            ]
        };
        
        // Start a call
        async function startCall(withVideo = false) {
            if (!currentFriend && !currentGroup) {
                showToast('Select a chat first', 'error');
                return;
            }
            
            try {
                // Get media stream
                const constraints = {
                    audio: true,
                    video: withVideo
                };
                
                localStream = await navigator.mediaDevices.getUserMedia(constraints);
                
                // Determine call type and target
                let callType, targetId, targetName;
                
                if (currentChatType === 'group' && currentGroup) {
                    callType = 'group';
                    targetId = currentGroup.id;
                    targetName = currentGroup.name;
                } else if (currentFriend) {
                    callType = 'dm';
                    targetId = currentFriend;
                    targetName = currentFriend;
                }
                
                // Emit start call event
                socket.emit('start_call', {
                    type: callType,
                    target_id: targetId,
                    video: withVideo
                });
                
                showToast(`📞 Starting ${withVideo ? 'video' : 'voice'} call...`, 'info');
                
            } catch (err) {
                console.error('Failed to start call:', err);
                showToast('Failed to access microphone/camera. Please check permissions.', 'error');
            }
        }
        
        // Register all call-related socket events (called from initSocket)
        function registerCallSocketEvents() {
            if (!socket) return; // Guard: socket must exist
            
            // Socket event: Call started
            socket.on('call_started', (data) => {
                currentCall = data;
            canSpeak = data.can_speak !== false;
            showCallUI(data);
            startCallTimer();
            
            console.log('📞 Call started:', data);
        });
        
        // Socket event: Incoming call
        socket.on('incoming_call', (data) => {
            incomingCallData = data;
            showIncomingCallModal(data);
            
            // Play ringtone sound (if you have one)
            console.log('📞 Incoming call from:', data.caller);
        });
        
        // Show incoming call modal
        function showIncomingCallModal(data) {
            const modal = document.getElementById('incomingCallModal');
            const avatar = document.getElementById('incomingCallAvatar');
            const name = document.getElementById('incomingCallName');
            const type = document.getElementById('incomingCallType');
            
            avatar.textContent = data.caller[0].toUpperCase();
            
            if (data.type === 'group') {
                name.textContent = data.group_name;
                type.textContent = `Group ${data.with_video ? 'Video' : 'Voice'} Call from ${data.caller}`;
            } else if (data.type === 'channel') {
                name.textContent = data.channel_name;
                type.textContent = `Channel ${data.with_video ? 'Video' : 'Voice'} Call`;
                if (!data.can_speak) {
                    type.textContent += ' (Listener Mode)';
                }
            } else {
                name.textContent = data.caller;
                type.textContent = data.with_video ? 'Video Call' : 'Voice Call';
            }
            
            modal.classList.add('show');
        }
        
        // Accept incoming call
        async function acceptIncomingCall() {
            if (!incomingCallData) return;
            
            const data = incomingCallData;
            
            try {
                // Get media stream (if allowed to speak)
                canSpeak = data.can_speak !== false;
                
                if (canSpeak) {
                    const constraints = {
                        audio: true,
                        video: data.with_video
                    };
                    localStream = await navigator.mediaDevices.getUserMedia(constraints);
                }
                
                // Join the call
                socket.emit('join_call', {
                    call_id: data.call_id,
                    video: data.with_video && canSpeak
                });
                
                // Hide modal
                document.getElementById('incomingCallModal').classList.remove('show');
                
            } catch (err) {
                console.error('Failed to join call:', err);
                showToast('Failed to access microphone/camera', 'error');
            }
        }
        
        // Decline incoming call
        function declineIncomingCall() {
            if (!incomingCallData) return;
            
            socket.emit('decline_call', { call_id: incomingCallData.call_id });
            document.getElementById('incomingCallModal').classList.remove('show');
            incomingCallData = null;
        }
        
        // Socket event: Call joined
        socket.on('call_joined', (data) => {
            currentCall = data;
            canSpeak = data.can_speak !== false;
            showCallUI(data);
            startCallTimer();
            
            // Set up peer connections for existing participants
            data.participants.forEach(participant => {
                if (participant.username !== myUsername) {
                    createPeerConnection(participant.username, true);
                }
            });
            
            console.log('📞 Joined call:', data);
        });
        
        // Socket event: New participant joined
        socket.on('participant_joined', (data) => {
            console.log('👤 Participant joined:', data.participant.username);
            showToast(`${data.participant.username} joined the call`, 'info');
            
            // Create peer connection for new participant
            createPeerConnection(data.participant.username, false);
            
            // Add video tile
            addVideoTile(data.participant);
        });
        
        // Socket event: Participant left
        socket.on('participant_left', (data) => {
            console.log('👤 Participant left:', data.username);
            showToast(`${data.username} left the call`, 'info');
            
            // Remove peer connection
            if (peerConnections[data.username]) {
                peerConnections[data.username].close();
                delete peerConnections[data.username];
            }
            
            // Remove participant tile
            const tile = document.getElementById(`participant-tile-${data.username}`);
            if (tile) tile.remove();
            
            // Update count and layout
            updateParticipantCount();
            updateGridLayout();
        });
        
        // Socket event: Call signal (WebRTC)
        socket.on('call_signal', async (data) => {
            const pc = peerConnections[data.from_user];
            if (!pc) {
                createPeerConnection(data.from_user, false);
            }
            
            try {
                if (data.signal_type === 'offer') {
                    await peerConnections[data.from_user].setRemoteDescription(
                        new RTCSessionDescription(data.signal_data)
                    );
                    const answer = await peerConnections[data.from_user].createAnswer();
                    await peerConnections[data.from_user].setLocalDescription(answer);
                    
                    socket.emit('call_signal', {
                        call_id: currentCall.call_id,
                        to_user: data.from_user,
                        signal_type: 'answer',
                        signal_data: answer
                    });
                    
                } else if (data.signal_type === 'answer') {
                    await peerConnections[data.from_user].setRemoteDescription(
                        new RTCSessionDescription(data.signal_data)
                    );
                    
                } else if (data.signal_type === 'ice-candidate') {
                    await peerConnections[data.from_user].addIceCandidate(
                        new RTCIceCandidate(data.signal_data)
                    );
                }
            } catch (err) {
                console.error('Signal handling error:', err);
            }
        });
        
        // Create peer connection
        function createPeerConnection(username, initiator) {
            if (peerConnections[username]) {
                return peerConnections[username];
            }
            
            const pc = new RTCPeerConnection(iceConfig);
            peerConnections[username] = pc;
            
            // Add local stream tracks
            if (localStream && canSpeak) {
                localStream.getTracks().forEach(track => {
                    pc.addTrack(track, localStream);
                });
            }
            
            // Handle ICE candidates
            pc.onicecandidate = (event) => {
                if (event.candidate) {
                    socket.emit('call_signal', {
                        call_id: currentCall.call_id,
                        to_user: username,
                        signal_type: 'ice-candidate',
                        signal_data: event.candidate
                    });
                }
            };
            
            // Handle incoming tracks
            pc.ontrack = (event) => {
                console.log('📹 Received track from:', username);
                const tile = document.getElementById(`video-tile-${username}`);
                if (tile) {
                    const video = tile.querySelector('video') || document.createElement('video');
                    video.srcObject = event.streams[0];
                    video.autoplay = true;
                    video.playsinline = true;
                    if (!tile.querySelector('video')) {
                        tile.insertBefore(video, tile.firstChild);
                    }
                    // Remove audio-only styling
                    tile.classList.remove('audio-only');
                }
            };
            
            // If initiator, create and send offer
            if (initiator) {
                pc.createOffer()
                    .then(offer => pc.setLocalDescription(offer))
                    .then(() => {
                        socket.emit('call_signal', {
                            call_id: currentCall.call_id,
                            to_user: username,
                            signal_type: 'offer',
                            signal_data: pc.localDescription
                        });
                    })
                    .catch(err => console.error('Create offer error:', err));
            }
            
            return pc;
        }
        
        // Show call UI (Full Page)
        function showCallUI(data) {
            const callPage = document.getElementById('callPage');
            const title = document.getElementById('callPageTitle');
            const typeText = document.getElementById('callTypeText');
            const typeIndicator = document.getElementById('callTypeIndicator');
            const listenerBanner = document.getElementById('listenerBanner');
            const videoBtn = document.getElementById('toggleVideoBtn');
            const localTile = document.getElementById('localParticipantTile');
            const localAvatar = document.getElementById('localAvatarFallback');
            const participantsGrid = document.getElementById('participantsGrid');
            
            // Set call info
            if (data.type === 'group') {
                title.textContent = data.group_name || 'Group Call';
            } else if (data.type === 'channel') {
                title.textContent = data.channel_name || 'Channel Call';
            } else {
                title.textContent = data.target || 'Call';
            }
            
            // Set call type
            typeText.textContent = data.with_video ? 'Video Call' : 'Voice Call';
            typeIndicator.style.color = data.with_video ? '#a855f7' : '#22c55e';
            
            // Update type indicator icon
            if (data.with_video) {
                typeIndicator.innerHTML = `
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polygon points="23 7 16 12 23 17 23 7"/>
                        <rect x="1" y="5" width="15" height="14" rx="2" ry="2"/>
                    </svg>
                    <span id="callTypeText">Video Call</span>
                `;
            }
            
            // Show/hide video button based on call type
            videoBtn.style.display = 'flex';
            
            // Show listener banner if needed
            listenerBanner.style.display = !canSpeak ? 'flex' : 'none';
            
            // Disable controls if listener
            if (!canSpeak) {
                document.getElementById('toggleMicBtn').disabled = true;
                document.getElementById('toggleMicBtn').classList.add('muted');
                document.getElementById('screenShareBtn').disabled = true;
                videoBtn.disabled = true;
            }
            
            // Show local video if we have a stream
            if (localStream && canSpeak) {
                const localVideo = document.getElementById('localVideo');
                localVideo.srcObject = localStream;
                
                // Hide avatar fallback if video is enabled
                if (data.with_video) {
                    localAvatar.style.display = 'none';
                    localVideo.style.display = 'block';
                } else {
                    localAvatar.style.display = 'flex';
                    localVideo.style.display = 'none';
                }
            }
            
            // Update participant count
            updateParticipantCount();
            
            // Show the call page
            callPage.classList.add('active');
            
            // Show mini indicator
            document.getElementById('activeCallIndicator').classList.add('show');
        }
        
        // Add participant tile to grid
        function addParticipantTile(participant) {
            const grid = document.getElementById('participantsGrid');
            
            // Check if tile already exists
            if (document.getElementById(`participant-tile-${participant.username}`)) {
                return;
            }
            
            const tile = document.createElement('div');
            tile.className = 'participant-tile';
            tile.id = `participant-tile-${participant.username}`;
            
            const avatarLetter = participant.username[0].toUpperCase();
            const statusIcons = [];
            
            if (!participant.audio) {
                statusIcons.push(`<div class="status-icon-badge muted" title="Muted"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="1" y1="1" x2="23" y2="23"/><path d="M9 9v3a3 3 0 005.12 2.12M15 9.34V4a3 3 0 00-5.94-.6"/></svg></div>`);
            }
            if (!participant.video && currentCall?.with_video) {
                statusIcons.push(`<div class="status-icon-badge video-off" title="Camera Off"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 16v1a2 2 0 01-2 2H3a2 2 0 01-2-2V7a2 2 0 012-2h2"/><line x1="1" y1="1" x2="23" y2="23"/></svg></div>`);
            }
            
            tile.innerHTML = `
                <div class="participant-video-container">
                    <video autoplay playsinline></video>
                    <div class="participant-avatar-large">
                        <span>${avatarLetter}</span>
                    </div>
                </div>
                <div class="participant-info-bar">
                    <span class="participant-name-label">${participant.username}</span>
                    <div class="participant-status-icons">
                        ${statusIcons.join('')}
                    </div>
                </div>
                <div class="speaking-ring"></div>
            `;
            
            // Hide video, show avatar by default
            const video = tile.querySelector('video');
            const avatar = tile.querySelector('.participant-avatar-large');
            video.style.display = 'none';
            avatar.style.display = 'flex';
            
            grid.appendChild(tile);
            updateParticipantCount();
            updateGridLayout();
        }
        
        // Update participant count display
        function updateParticipantCount() {
            const count = document.querySelectorAll('.participant-tile').length;
            document.getElementById('participantCountNum').textContent = count;
        }
        
        // Update grid layout based on participant count
        function updateGridLayout() {
            const grid = document.getElementById('participantsGrid');
            const count = document.querySelectorAll('.participant-tile').length;
            
            grid.classList.remove('single-participant', 'two-participants');
            
            if (count === 1) {
                grid.classList.add('single-participant');
            } else if (count === 2) {
                grid.classList.add('two-participants');
            }
        }
        
        // Minimize call (go back to chat but keep call active)
        function minimizeCall() {
            document.getElementById('callPage').classList.remove('active');
            // Mini indicator stays visible
        }
        
        // Legacy function for compatibility
        function addVideoTile(participant) {
            addParticipantTile(participant);
        }
        
        // Toggle microphone
        function toggleMic() {
            if (!canSpeak || !localStream) return;
            
            isMuted = !isMuted;
            localStream.getAudioTracks().forEach(track => {
                track.enabled = !isMuted;
            });
            
            const btn = document.getElementById('toggleMicBtn');
            btn.classList.toggle('muted', isMuted);
            
            // Update local status icons
            const localStatusIcons = document.getElementById('localStatusIcons');
            if (isMuted) {
                if (!localStatusIcons.querySelector('.muted')) {
                    const icon = document.createElement('div');
                    icon.className = 'status-icon-badge muted';
                    icon.title = 'Muted';
                    icon.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="1" y1="1" x2="23" y2="23"/><path d="M9 9v3a3 3 0 005.12 2.12M15 9.34V4a3 3 0 00-5.94-.6"/></svg>';
                    localStatusIcons.appendChild(icon);
                }
            } else {
                const mutedIcon = localStatusIcons.querySelector('.muted');
                if (mutedIcon) mutedIcon.remove();
            }
            
            // Notify others
            socket.emit('toggle_audio', {
                call_id: currentCall.call_id,
                enabled: !isMuted
            });
        }
        
        // Toggle video
        function toggleVideo() {
            if (!canSpeak) return;
            
            isVideoOff = !isVideoOff;
            
            if (localStream) {
                localStream.getVideoTracks().forEach(track => {
                    track.enabled = !isVideoOff;
                });
            }
            
            const btn = document.getElementById('toggleVideoBtn');
            btn.classList.toggle('muted', isVideoOff);
            
            // Update local video display
            const localVideo = document.getElementById('localVideo');
            const localAvatar = document.getElementById('localAvatarFallback');
            const localStatusIcons = document.getElementById('localStatusIcons');
            
            if (isVideoOff) {
                localVideo.style.display = 'none';
                localAvatar.style.display = 'flex';
                if (!localStatusIcons.querySelector('.video-off')) {
                    const icon = document.createElement('div');
                    icon.className = 'status-icon-badge video-off';
                    icon.title = 'Camera Off';
                    icon.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 16v1a2 2 0 01-2 2H3a2 2 0 01-2-2V7a2 2 0 012-2h2"/><line x1="1" y1="1" x2="23" y2="23"/></svg>';
                    localStatusIcons.appendChild(icon);
                }
            } else {
                localVideo.style.display = 'block';
                localAvatar.style.display = 'none';
                const videoOffIcon = localStatusIcons.querySelector('.video-off');
                if (videoOffIcon) videoOffIcon.remove();
            }
            
            // Notify others
            socket.emit('toggle_video', {
                call_id: currentCall.call_id,
                enabled: !isVideoOff
            });
        }
        
        // Toggle screen share
        async function toggleScreenShare() {
            if (!canSpeak) return;
            
            if (isScreenSharing) {
                // Stop screen share
                if (screenStream) {
                    screenStream.getTracks().forEach(track => track.stop());
                    screenStream = null;
                }
                isScreenSharing = false;
                document.getElementById('screenShareBtn').classList.remove('active');
                
                socket.emit('stop_screen_share', { call_id: currentCall.call_id });
                
            } else {
                // Start screen share
                try {
                    screenStream = await navigator.mediaDevices.getDisplayMedia({ video: true });
                    isScreenSharing = true;
                    document.getElementById('screenShareBtn').classList.add('active');
                    
                    // Replace video track in peer connections
                    const videoTrack = screenStream.getVideoTracks()[0];
                    for (const pc of Object.values(peerConnections)) {
                        const sender = pc.getSenders().find(s => s.track?.kind === 'video');
                        if (sender) {
                            sender.replaceTrack(videoTrack);
                        }
                    }
                    
                    socket.emit('start_screen_share', { call_id: currentCall.call_id });
                    
                    // Handle when user stops sharing via browser
                    videoTrack.onended = () => {
                        toggleScreenShare();
                    };
                    
                } catch (err) {
                    console.error('Screen share error:', err);
                    showToast('Failed to share screen', 'error');
                }
            }
        }
        
        // End call
        function endCall() {
            if (!currentCall) return;
            
            socket.emit('leave_call', { call_id: currentCall.call_id });
            cleanupCall();
        }
        
        // Socket event: Call ended
        socket.on('call_ended', (data) => {
            console.log('📞 Call ended:', data.reason);
            showToast(`Call ended: ${data.reason}`, 'info');
            cleanupCall();
        });
        
        // Socket event: Call declined
        socket.on('call_declined', (data) => {
            console.log('📞 Call declined by:', data.declined_by);
            showToast(`${data.declined_by} declined the call`, 'info');
            cleanupCall();
        });
        
        // Socket event: Call error
        socket.on('call_error', (data) => {
            console.error('📞 Call error:', data.error);
            showToast(data.error, 'error');
        });
        
        // Cleanup call resources
        function cleanupCall() {
            // Stop local stream
            if (localStream) {
                localStream.getTracks().forEach(track => track.stop());
                localStream = null;
            }
            
            // Stop screen share
            if (screenStream) {
                screenStream.getTracks().forEach(track => track.stop());
                screenStream = null;
            }
            
            // Close all peer connections
            for (const pc of Object.values(peerConnections)) {
                pc.close();
            }
            peerConnections = {};
            
            // Clear timer
            if (callDurationInterval) {
                clearInterval(callDurationInterval);
                callDurationInterval = null;
            }
            
            // Reset state
            currentCall = null;
            callStartTime = null;
            isMuted = false;
            isVideoOff = false;
            isScreenSharing = false;
            canSpeak = true;
            
            // Hide UI
            document.getElementById('callPage').classList.remove('active');
            document.getElementById('activeCallIndicator').classList.remove('show');
            document.getElementById('incomingCallModal').classList.remove('show');
            
            // Clear participants grid (keep local tile template)
            const grid = document.getElementById('participantsGrid');
            const localTile = document.getElementById('localParticipantTile');
            grid.innerHTML = '';
            grid.appendChild(localTile);
            
            // Reset local video
            const localVideo = document.getElementById('localVideo');
            const localAvatar = document.getElementById('localAvatarFallback');
            localVideo.srcObject = null;
            localVideo.style.display = 'none';
            localAvatar.style.display = 'flex';
            
            // Reset buttons
            document.getElementById('toggleMicBtn').classList.remove('muted');
            document.getElementById('toggleMicBtn').disabled = false;
            document.getElementById('toggleVideoBtn').classList.remove('muted');
            document.getElementById('toggleVideoBtn').disabled = false;
            document.getElementById('screenShareBtn').classList.remove('active');
            document.getElementById('screenShareBtn').disabled = false;
            
            // Reset local status icons
            document.getElementById('localStatusIcons').innerHTML = '';
        }
        
        // Start call duration timer
        function startCallTimer() {
            callStartTime = Date.now();
            const durationEl = document.getElementById('callDuration');
            const miniDurationEl = document.getElementById('miniCallDuration');
            const statusEl = document.getElementById('callStatusText');
            
            durationEl.style.display = 'inline';
            statusEl.textContent = 'Connected';
            
            callDurationInterval = setInterval(() => {
                const elapsed = Math.floor((Date.now() - callStartTime) / 1000);
                const minutes = Math.floor(elapsed / 60).toString().padStart(2, '0');
                const seconds = (elapsed % 60).toString().padStart(2, '0');
                const timeStr = `${minutes}:${seconds}`;
                
                durationEl.textContent = timeStr;
                miniDurationEl.textContent = timeStr;
            }, 1000);
        }
        
        // Return to call from mini indicator
        function returnToCall() {
            if (currentCall) {
                document.getElementById('callPage').classList.add('active');
            }
        }
        
        // Participant audio changed
        socket.on('participant_audio_changed', (data) => {
            const tile = document.getElementById(`participant-tile-${data.username}`);
            if (tile) {
                const statusDiv = tile.querySelector('.participant-status-icons');
                if (!data.audio) {
                    if (!statusDiv.querySelector('.muted')) {
                        const icon = document.createElement('div');
                        icon.className = 'status-icon-badge muted';
                        icon.title = 'Muted';
                        icon.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="1" y1="1" x2="23" y2="23"/><path d="M9 9v3a3 3 0 005.12 2.12M15 9.34V4a3 3 0 00-5.94-.6"/></svg>';
                        statusDiv.appendChild(icon);
                    }
                } else {
                    const mutedIcon = statusDiv.querySelector('.muted');
                    if (mutedIcon) mutedIcon.remove();
                }
            }
        });
        
        // Participant video changed
        socket.on('participant_video_changed', (data) => {
            const tile = document.getElementById(`participant-tile-${data.username}`);
            if (tile) {
                const video = tile.querySelector('video');
                const avatar = tile.querySelector('.participant-avatar-large');
                const statusDiv = tile.querySelector('.participant-status-icons');
                
                if (data.video) {
                    video.style.display = 'block';
                    avatar.style.display = 'none';
                    const videoOffIcon = statusDiv.querySelector('.video-off');
                    if (videoOffIcon) videoOffIcon.remove();
                } else {
                    video.style.display = 'none';
                    avatar.style.display = 'flex';
                    if (!statusDiv.querySelector('.video-off')) {
                        const icon = document.createElement('div');
                        icon.className = 'status-icon-badge video-off';
                        icon.title = 'Camera Off';
                        icon.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 16v1a2 2 0 01-2 2H3a2 2 0 01-2-2V7a2 2 0 012-2h2"/><line x1="1" y1="1" x2="23" y2="23"/></svg>';
                        statusDiv.appendChild(icon);
                    }
                }
            }
        });
        
        // Screen share notifications
        socket.on('screen_share_started', (data) => {
            showToast(`${data.username} started sharing their screen`, 'info');
        });
        
            socket.on('screen_share_stopped', (data) => {
                showToast(`${data.username} stopped sharing their screen`, 'info');
            });
        } // End of registerCallSocketEvents
        
        // PWA Install Prompt
        let deferredPrompt;
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
            // Show install button if you want
            console.log('📱 Menza can be installed as an app!');
        });
        
