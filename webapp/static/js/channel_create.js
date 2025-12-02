        // Section navigation
        function switchSection(section) {
            // Update nav items
            document.querySelectorAll('.create-nav-item').forEach(item => {
                item.classList.remove('active');
            });
            document.querySelector(`[onclick="switchSection('${section}')"]`).classList.add('active');

            // Update sections
            document.querySelectorAll('.create-section').forEach(s => {
                s.classList.remove('active');
            });
            document.getElementById(`section-${section}`).classList.add('active');

            // Update summary when going to preview
            if (section === 'preview') {
                updateSummary();
            }

            // Scroll to top
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }

        // Live preview updates
        const nameInput = document.getElementById('name');
        const descInput = document.getElementById('description');
        const previewName = document.getElementById('previewName');
        const previewDesc = document.getElementById('previewDesc');
        const previewAvatar = document.getElementById('previewAvatar');
        const previewBadge = document.getElementById('previewBadge');

        nameInput.addEventListener('input', () => {
            previewName.textContent = nameInput.value || 'Your Channel';
        });

        descInput.addEventListener('input', () => {
            previewDesc.textContent = descInput.value || 'Channel description...';
        });

        // Icon type tabs (Emoji vs Upload)
        const iconTypeTabs = document.querySelectorAll('.icon-type-tab');
        const emojiContent = document.getElementById('emojiContent');
        const uploadContent = document.getElementById('uploadContent');
        const avatarTypeInput = document.getElementById('avatarType');
        
        iconTypeTabs.forEach(tab => {
            tab.addEventListener('click', () => {
                iconTypeTabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                
                const type = tab.dataset.type;
                if (type === 'emoji') {
                    emojiContent.classList.add('active');
                    uploadContent.classList.remove('active');
                    avatarTypeInput.value = 'emoji';
                    // Reset to emoji preview
                    const selectedEmoji = document.querySelector('.emoji-option.selected');
                    if (selectedEmoji) {
                        previewAvatar.innerHTML = selectedEmoji.textContent.trim();
                        previewAvatar.style.backgroundImage = '';
                    }
                } else {
                    emojiContent.classList.remove('active');
                    uploadContent.classList.add('active');
                    avatarTypeInput.value = 'image';
                }
            });
        });

        // Emoji selection
        document.querySelectorAll('.emoji-option').forEach(option => {
            option.addEventListener('click', () => {
                document.querySelectorAll('.emoji-option').forEach(o => o.classList.remove('selected'));
                option.classList.add('selected');
                previewAvatar.innerHTML = option.textContent.trim();
                previewAvatar.style.backgroundImage = '';
            });
        });

        // Image Upload functionality
        const uploadArea = document.getElementById('uploadArea');
        const channelImageInput = document.getElementById('channelImageInput');
        const uploadPreview = document.getElementById('uploadPreview');
        const previewImage = document.getElementById('previewImage');
        const previewNameEl = document.getElementById('previewName');
        const previewSize = document.getElementById('previewSize');
        const removeImageBtn = document.getElementById('removeImage');
        const avatarImageData = document.getElementById('avatarImageData');

        uploadArea.addEventListener('click', () => {
            channelImageInput.click();
        });

        // Drag and drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleImageFile(files[0]);
            }
        });

        channelImageInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleImageFile(e.target.files[0]);
            }
        });

        function handleImageFile(file) {
            // Validate file type
            const validTypes = ['image/png', 'image/jpeg', 'image/gif', 'image/webp'];
            if (!validTypes.includes(file.type)) {
                alert('Please upload a valid image file (PNG, JPG, GIF, or WebP)');
                return;
            }

            // Validate file size (5MB max)
            if (file.size > 5 * 1024 * 1024) {
                alert('Image must be less than 5MB');
                return;
            }

            const reader = new FileReader();
            reader.onload = (e) => {
                const imageData = e.target.result;
                
                // Update preview
                previewImage.src = imageData;
                previewNameEl.textContent = file.name;
                previewSize.textContent = formatFileSize(file.size);
                
                // Show preview, hide upload area
                uploadArea.style.display = 'none';
                uploadPreview.classList.add('active');
                
                // Store base64 data
                avatarImageData.value = imageData;
                
                // Update channel preview avatar
                previewAvatar.innerHTML = '';
                previewAvatar.style.backgroundImage = `url(${imageData})`;
                previewAvatar.style.backgroundSize = 'cover';
                previewAvatar.style.backgroundPosition = 'center';
            };
            reader.readAsDataURL(file);
        }

        function formatFileSize(bytes) {
            if (bytes < 1024) return bytes + ' B';
            if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
            return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
        }

        removeImageBtn.addEventListener('click', () => {
            // Reset
            channelImageInput.value = '';
            avatarImageData.value = '';
            uploadArea.style.display = 'block';
            uploadPreview.classList.remove('active');
            
            // Reset preview avatar to emoji
            const selectedEmoji = document.querySelector('.emoji-option.selected');
            if (selectedEmoji) {
                previewAvatar.innerHTML = selectedEmoji.textContent.trim();
            } else {
                previewAvatar.innerHTML = '📢';
            }
            previewAvatar.style.backgroundImage = '';
        });

        // Color selection
        document.querySelectorAll('.color-option').forEach(option => {
            option.addEventListener('click', () => {
                document.querySelectorAll('.color-option').forEach(o => o.classList.remove('selected'));
                option.classList.add('selected');
                const color = option.querySelector('input').value;
                previewAvatar.style.background = color + '20';
                previewAvatar.style.color = color;
            });
        });

        // Visibility toggle
        const discoverableToggle = document.getElementById('discoverableToggle');
        const visibilityNote = document.getElementById('visibilityNote');

        function updateVisibilityNote() {
            if (discoverableToggle.checked) {
                visibilityNote.className = 'visibility-note';
                visibilityNote.innerHTML = `
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                    </svg>
                    <span>Your channel will appear in search results and the discovery section. High engagement channels get featured in trending.</span>
                `;
                previewBadge.textContent = 'Public';
                previewBadge.className = 'preview-badge public';
            } else {
                visibilityNote.className = 'visibility-note private';
                visibilityNote.innerHTML = `
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                        <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                    </svg>
                    <span>Your channel is private. Only people with a direct link can find and subscribe to it. It won't appear in search or discovery.</span>
                `;
                previewBadge.textContent = 'Private';
                previewBadge.className = 'preview-badge private';
            }
        }

        discoverableToggle.addEventListener('change', updateVisibilityNote);

        // Member management
        const membersList = document.getElementById('membersList');
        const memberInput = document.getElementById('memberInput');
        const roleSelect = document.getElementById('roleSelect');
        const addMemberBtn = document.getElementById('addMemberBtn');
        const invitedMembersInput = document.getElementById('invitedMembersInput');

        let invitedMembers = [];

        function getRoleLabel(role) {
            const labels = {
                'admin': 'Admin',
                'mod': 'Moderator',
                'viewer': 'Viewer'
            };
            return labels[role] || role;
        }

        function renderMembersList() {
            if (invitedMembers.length === 0) {
                membersList.innerHTML = '';
                return;
            }

            membersList.innerHTML = invitedMembers.map((member, index) => `
                <div class="member-item">
                    <div class="member-avatar">${member.username[0].toUpperCase()}</div>
                    <div class="member-info">
                        <div class="member-name">@${member.username}</div>
                    </div>
                    <span class="member-role-badge ${member.role}">${getRoleLabel(member.role)}</span>
                    <button type="button" class="member-remove" onclick="removeMember(${index})">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="18" y1="6" x2="6" y2="18"/>
                            <line x1="6" y1="6" x2="18" y2="18"/>
                        </svg>
                    </button>
                </div>
            `).join('');

            invitedMembersInput.value = JSON.stringify(invitedMembers);
        }

        function removeMember(index) {
            invitedMembers.splice(index, 1);
            renderMembersList();
        }

        addMemberBtn.addEventListener('click', () => {
            const username = memberInput.value.trim().replace('@', '');
            const role = roleSelect.value;

            if (!username) {
                memberInput.focus();
                return;
            }

            if (invitedMembers.some(m => m.username.toLowerCase() === username.toLowerCase())) {
                alert('This user is already in the list');
                return;
            }

            invitedMembers.push({ username, role });
            renderMembersList();
            memberInput.value = '';
            memberInput.focus();
        });

        memberInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                addMemberBtn.click();
            }
        });

        // Update summary
        function updateSummary() {
            document.getElementById('summaryName').textContent = nameInput.value || '-';
            document.getElementById('summaryVisibility').textContent = discoverableToggle.checked ? 'Public' : 'Private';
            document.getElementById('summaryMembers').textContent = `${invitedMembers.length} invited`;
        }
