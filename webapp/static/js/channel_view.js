        const socket = io();
        const channelId = '{{ channel.id }}';
        const currentUser = '{{ username }}';

        // Join channel room for real-time updates
        socket.emit('join_channel', { channel_id: channelId });

        // Format post content
        function formatContent(content) {
            return content
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/__(.*?)__/g, '<u>$1</u>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/`(.*?)`/g, '<code>$1</code>')
                .replace(/==(.*?)==/g, '<span class="highlight">$1</span>');
        }

        // Apply formatting to all posts on load
        document.querySelectorAll('.post-content').forEach(el => {
            el.innerHTML = formatContent(el.textContent);
        });

        // Insert formatting at cursor
        function insertFormat(before, after) {
            const textarea = document.getElementById('postContent');
            if (!textarea) return;
            const start = textarea.selectionStart;
            const end = textarea.selectionEnd;
            const text = textarea.value;
            const selected = text.substring(start, end);
            
            textarea.value = text.substring(0, start) + before + selected + after + text.substring(end);
            textarea.focus();
            textarea.setSelectionRange(start + before.length, end + before.length);
        }

        // Toggle link post selector
        function toggleLinkPost() {
            const select = document.getElementById('linkedPostSelect');
            if (select) {
                select.style.display = select.style.display === 'none' ? 'block' : 'none';
            }
        }

        // Toggle like
        function toggleLike(postId) {
            socket.emit('toggle_like', { post_id: postId });
        }

        // Add reaction
        function addReaction(postId, emoji) {
            socket.emit('add_reaction', { post_id: postId, emoji: emoji });
            document.querySelectorAll('.reaction-dropdown').forEach(el => el.classList.remove('show'));
        }

        // Toggle reaction picker
        function toggleReactionPicker(postId) {
            const picker = document.getElementById(`reaction-picker-${postId}`);
            document.querySelectorAll('.reaction-dropdown').forEach(el => {
                if (el !== picker) el.classList.remove('show');
            });
            picker.classList.toggle('show');
        }

        // Toggle comments
        function toggleComments(postId) {
            const comments = document.getElementById(`comments-${postId}`);
            comments.classList.toggle('show');
        }

        // Handle comment key
        function handleCommentKey(event, postId) {
            if (event.key === 'Enter') {
                event.preventDefault();
                submitComment(postId);
            }
        }

        // Submit comment
        function submitComment(postId) {
            const input = document.getElementById(`comment-input-${postId}`);
            const content = input.value.trim();
            
            if (content) {
                socket.emit('add_comment', { post_id: postId, content: content });
                input.value = '';
            }
        }

        // Toggle members panel
        function toggleMembers() {
            const panel = document.getElementById('membersPanel');
            panel.classList.toggle('show');
        }

        // Socket event handlers
        socket.on('like_updated', (data) => {
            const btn = document.getElementById(`like-btn-${data.post_id}`);
            const count = document.getElementById(`like-count-${data.post_id}`);
            if (btn && count) {
                count.textContent = data.like_count;
                if (data.liked_by.includes(currentUser)) {
                    btn.classList.add('liked');
                } else {
                    btn.classList.remove('liked');
                }
            }
        });

        socket.on('reaction_added', (data) => {
            // Reload page to show updated reactions (simple approach)
            location.reload();
        });

        socket.on('comment_added', (data) => {
            const commentsList = document.getElementById(`comments-${data.post_id}`);
            const countEl = document.getElementById(`comment-count-${data.post_id}`);
            
            if (commentsList) {
                const commentHtml = `
                    <div class="comment">
                        <div class="comment-avatar">${data.author[0].toUpperCase()}</div>
                        <div class="comment-content">
                            <div class="comment-header">
                                <span class="comment-author">${data.author}</span>
                                <span class="comment-time">Just now</span>
                            </div>
                            <div class="comment-text">${data.content}</div>
                        </div>
                    </div>
                `;
                const inputWrapper = commentsList.querySelector('.comment-input-wrapper');
                inputWrapper.insertAdjacentHTML('beforebegin', commentHtml);
                commentsList.classList.add('show');
            }
            
            if (countEl) {
                countEl.textContent = parseInt(countEl.textContent) + 1;
            }
        });

        // Close dropdowns when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.reaction-picker')) {
                document.querySelectorAll('.reaction-dropdown').forEach(el => el.classList.remove('show'));
            }
        });

        // ============================================
        // CALCULATOR FUNCTIONS
        // ============================================
        
        let lastCalculations = [];
        let lastTotal = 0;
        
        function detectCalculations(text) {
            const preview = document.getElementById('calcPreview');
            const suggestionsContainer = document.getElementById('calcSuggestions');
            
            if (!preview || !suggestionsContainer) return;
            
            // Pattern to match math expressions: number operator number
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
                        <button type="button" class="calc-chip expression" onclick="insertCalcText('"${calc.expression}="')">"${calc.expression}="</button>
                        <button type="button" class="calc-chip full" onclick="insertCalcText('${calc.expression}=${resultStr}')">${calc.expression}=${resultStr}</button>
                        <button type="button" class="calc-chip result" onclick="insertCalcText('${resultStr}')">${resultStr}</button>
                    `;
                } else {
                    // Multiple calculations - show each result + total
                    calculations.forEach(calc => {
                        const resultStr = formatNumber(calc.result);
                        html += `<button type="button" class="calc-chip full" onclick="insertCalcText('${calc.expression}=${resultStr}')">${calc.expression}=${resultStr}</button>`;
                    });
                    
                    // Add total chip
                    const total = calculations.reduce((sum, calc) => sum + calc.result, 0);
                    const totalStr = formatNumber(total);
                    html += `<button type="button" class="calc-total-chip" onclick="insertCalcText('Total: ${totalStr}')"><span class="calc-total-label">Total</span> ${totalStr}</button>`;
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
            const input = document.getElementById('postContent');
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
            if (Number.isInteger(num)) {
                return num.toLocaleString();
            }
            return num.toLocaleString(undefined, { maximumFractionDigits: 2 });
        }
        
        function insertCalculatedText() {
            if (lastCalculations.length === 0) return;
            
            const textarea = document.getElementById('postContent');
            
            let resultLines = lastCalculations.map(calc => 
                `${calc.expression}=${formatNumber(calc.result)}`
            );
            
            if (lastCalculations.length > 1) {
                resultLines.push(`Total=${formatNumber(lastTotal)}`);
            }
            
            textarea.value = resultLines.join('\n');
            document.getElementById('calcPreview').classList.remove('show');
            textarea.focus();
        }
