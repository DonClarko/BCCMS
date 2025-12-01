// messaging.js
// Handles messaging and notifications for both resident and official dashboards

const IS_OFFICIAL_DASHBOARD = !!document.getElementById('status-update-modal');

// Load list of residents for official's compose message modal
function loadResidentsForMessaging() {
    console.log('Loading residents for messaging...');
    fetch('/residents/list', {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin'
    })
    .then(response => {
        console.log('Residents response status:', response.status);
        return response.json();
    })
    .then(residents => {
        console.log('Residents received:', residents);
        const select = document.getElementById('message-recipient-official');
        if (!select) {
            console.error('message-recipient-official select not found!');
            return;
        }

        // Clear existing options except the first one
        while (select.options.length > 1) {
            select.remove(1);
        }

        // Add resident options
        residents.forEach(resident => {
            const option = document.createElement('option');
            option.value = resident.email;
            option.textContent = `${resident.name} (${resident.email})`;
            select.appendChild(option);
        });
        console.log(`Added ${residents.length} residents to dropdown`);
    })
    .catch(error => console.error('Error loading residents:', error));
}

// Load list of officials for resident's compose message modal
function loadOfficialsForMessaging() {
    console.log('Loading officials for messaging...');
    fetch('/officials/list', {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin'
    })
    .then(response => {
        console.log('Officials response status:', response.status);
        return response.json();
    })
    .then(officials => {
        console.log('Officials received:', officials);
        const select = document.getElementById('message-recipient');
        if (!select) {
            console.error('message-recipient select not found!');
            return;
        }

        // Clear existing options except the first one
        while (select.options.length > 1) {
            select.remove(1);
        }

        // Add official options
        officials.forEach(official => {
            const option = document.createElement('option');
            option.value = official.email;
            option.textContent = `${official.name} (${official.email})`;
            select.appendChild(option);
        });
        console.log(`Added ${officials.length} officials to dropdown`);
    })
    .catch(error => console.error('Error loading officials:', error));
}

// Load list of complaints for message modal
function loadComplaintsForMessaging(isOfficial = false) {
    fetch('/complaint/all', {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(complaints => {
        const selectId = isOfficial ? 'message-complaint-official' : 'message-complaint';
        const select = document.getElementById(selectId);
        if (!select) return;

        // Clear existing options except the first one
        while (select.options.length > 1) {
            select.remove(1);
        }

        // Add complaint options
        complaints.forEach(complaint => {
            const option = document.createElement('option');
            option.value = complaint.id;
            option.textContent = `${complaint.id} - ${complaint.title || complaint.category}`;
            select.appendChild(option);
        });
    })
    .catch(error => console.error('Error loading complaints:', error));
}

// Load and display notifications for the current user
function loadNotifications() {
    fetch('/notifications', {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin'
    })
    .then(response => {
        if (response.redirected) {
            window.location.href = response.url;
            return;
        }
        return response.json();
    })
    .then(notifications => {
        // Find the correct notifications list container
        const notificationsList = document.querySelector('#notifications-modal .notifications-list') || 
                                  document.querySelector('.notifications-list');
        if (!notificationsList) return;

        // Clear existing static notifications
        notificationsList.innerHTML = '';

        if (notifications.length === 0) {
            notificationsList.innerHTML = '<p class="no-notifications">No notifications yet.</p>';
            return;
        }

        // Display all notifications
        notifications.forEach(notif => {
            const card = document.createElement('div');
            card.className = `notification-card ${notif.read ? '' : 'unread'}`;
            card.dataset.notifId = notif.id;

            const timestamp = new Date(notif.timestamp).toLocaleString();
            card.innerHTML = `
                <div class="notification-icon">
                    <i class="fas fa-bell"></i>
                </div>
                <div class="notification-content">
                    <h3>${notif.title || 'Notification'}</h3>
                    <p>${notif.message || ''}</p>
                    <span class="notification-time">${timestamp}</span>
                </div>
                <button class="btn-mark-read" data-notif-id="${notif.id}">
                    <i class="far fa-check-circle"></i>
                </button>
            `;

            notificationsList.appendChild(card);

            // Add event listener to mark as read
            card.querySelector('.btn-mark-read').addEventListener('click', function(e) {
                e.preventDefault();
                markNotificationRead(notif.id, card);
            });
        });

        // Update notification count badge
        const unreadCount = notifications.filter(n => !n.read).length;
        updateNotificationCount(unreadCount);
    })
    .catch(error => console.error('Error loading notifications:', error));
}

// Mark a notification as read
function markNotificationRead(notifId, cardElement) {
    fetch('/notifications/mark_read', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin',
        body: JSON.stringify({ id: notifId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            cardElement.classList.remove('unread');
            // Reload to update count
            loadNotifications();
        }
    })
    .catch(error => console.error('Error marking notification read:', error));
}

// Update the notification count badge
function updateNotificationCount(count) {
    const badges = document.querySelectorAll('.notification-count');
    badges.forEach(badge => {
        if (badge.closest('#notifications')) {
            badge.textContent = count;
        }
    });
}

// Load and display messages for the current user
function loadMessages() {
    fetch('/messages', {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin'
    })
    .then(response => {
        if (response.redirected) {
            window.location.href = response.url;
            return;
        }
        return response.json();
    })
    .then(messages => {
        // Find the correct messages list container
        const messagesList = document.querySelector('#messages-modal .messages-list') || 
                             document.querySelector('.messages-list');
        if (!messagesList) return;

        // Clear existing static messages
        messagesList.innerHTML = '';

        if (messages.length === 0) {
            messagesList.innerHTML = '<p class="no-messages">No messages yet. Send one to an official!</p>';
            return;
        }

        // Group messages by conversation partner
        // A conversation partner is: who sent the message if I received it, or who I sent it to if I sent it
        const conversations = {};
        
        messages.forEach(msg => {
            // Determine the conversation partner email and name
            let partnerEmail, partnerName;
            
            if (msg.isSent) {
                // I sent this message, so partner is the recipient
                partnerEmail = msg.to_email;
                partnerName = msg.to_name || msg.to_email;
            } else {
                // I received this message, so partner is the sender
                partnerEmail = msg.from_email;
                partnerName = msg.from_name || msg.from_email;
            }
            
            if (!conversations[partnerEmail]) {
                conversations[partnerEmail] = {
                    name: partnerName,
                    email: partnerEmail,
                    messages: [],
                    latestTimestamp: msg.timestamp
                };
            }
            
            conversations[partnerEmail].messages.push({
                ...msg,
                isFromMe: msg.isSent === true
            });
            conversations[partnerEmail].latestTimestamp = msg.timestamp;
        });

        // Sort conversations by latest message
        const sortedConversations = Object.values(conversations).sort((a, b) => {
            return new Date(b.latestTimestamp) - new Date(a.latestTimestamp);
        });

        // Display conversations
        sortedConversations.forEach(convo => {
            const card = document.createElement('div');
            card.className = `message-card`;
            card.dataset.partner = convo.email;

            const latestMsg = convo.messages[convo.messages.length - 1];
            const timestamp = new Date(latestMsg.timestamp).toLocaleString();
            const unreadCount = convo.messages.filter(m => !m.read).length;
            
            card.innerHTML = `
                <div class="message-sender">
                    <div class="sender-avatar">
                        <i class="fas fa-user-circle"></i>
                    </div>
                    <div class="sender-info">
                        <h3>${convo.name}</h3>
                        <p class="message-preview">${latestMsg.subject || latestMsg.content.substring(0, 50)}</p>
                        <span style="font-size: 12px; color: #999;">${convo.messages.length} message(s)</span>
                    </div>
                </div>
                <div class="message-meta">
                    <span class="message-time">${timestamp}</span>
                    ${unreadCount > 0 ? `<span style="background: #ff6b6b; color: white; border-radius: 50%; width: 20px; height: 20px; display: flex; align-items: center; justify-content: center; font-size: 12px;">${unreadCount}</span>` : ''}
                </div>
            `;

            messagesList.appendChild(card);

            // Add click to view conversation
            card.addEventListener('click', function(e) {
                showConversation(convo);
            });
        });

        // Update message count badge
        const totalUnread = messages.filter(m => !m.read).length;
        updateMessageCount(totalUnread);
    })
    .catch(error => console.error('Error loading messages:', error));
}

// Get current logged-in user info from the page
async function getCurrentUser() {
    // Try to get from DOM or make API call
    try {
        const response = await fetch('/api/current-user', {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'
        });
        if (response.ok) {
            return await response.json();
        }
    } catch (e) {
        console.error('Error getting current user:', e);
    }
    return null;
}

// Show a conversation with a specific person
function showConversation(conversation) {
    const modal = document.createElement('div');
    modal.id = 'conversation-modal';
    modal.className = 'modal';
    modal.style.display = 'block';
    
    let messagesHTML = '';
    
    // Sort messages by timestamp (oldest first for conversation view)
    const sortedMessages = [...conversation.messages].sort((a, b) => {
        return new Date(a.timestamp) - new Date(b.timestamp);
    });
    
    sortedMessages.forEach(msg => {
        const timestamp = new Date(msg.timestamp).toLocaleString();
        const isFromMe = msg.isSent === true;
        const senderName = isFromMe ? 'You' : (msg.from_name || msg.from_email);
        
        if (isFromMe) {
            // Sent message - right aligned, blue bubble
            messagesHTML += `
                <div style="display: flex; justify-content: flex-end; margin: 10px 0;">
                    <div style="max-width: 70%; background: #007bff; color: white; border-radius: 12px; padding: 12px 15px;">
                        <p style="margin: 0 0 5px 0; font-size: 13px; opacity: 0.9;"><strong>${senderName}</strong></p>
                        <p style="margin: 0 0 5px 0; white-space: pre-wrap; font-size: 14px;">${msg.content}</p>
                        <p style="margin: 0; font-size: 12px; opacity: 0.8; text-align: right;">${timestamp}</p>
                        <p style="margin: 5px 0 0 0; font-size: 12px; opacity: 0.8;">Subject: ${msg.subject}</p>
                    </div>
                </div>
            `;
        } else {
            // Received message - left aligned, gray bubble
            messagesHTML += `
                <div style="display: flex; justify-content: flex-start; margin: 10px 0;">
                    <div style="max-width: 70%; background: #f0f0f0; color: #333; border-radius: 12px; padding: 12px 15px;">
                        <p style="margin: 0 0 5px 0; font-size: 13px; font-weight: 600;"><strong>${senderName}</strong></p>
                        <p style="margin: 0 0 5px 0; white-space: pre-wrap; font-size: 14px;">${msg.content}</p>
                        <p style="margin: 0; font-size: 12px; color: #666; text-align: left;">${timestamp}</p>
                        <p style="margin: 5px 0 0 0; font-size: 12px; color: #666;">Subject: ${msg.subject}</p>
                    </div>
                </div>
            `;
        }
    });
    
    modal.innerHTML = `
        <div class="modal-content" style="max-width: 750px; max-height: 85vh; display: flex; flex-direction: column; overflow: hidden;">
            <div class="modal-header" style="border-bottom: 1px solid #ddd; padding-bottom: 10px;">
                <h2 style="margin: 0; display: flex; align-items: center; justify-content: space-between;">
                    <span><i class="fas fa-user-circle"></i> ${conversation.name}</span>
                    <button class="close-btn" onclick="this.closest('.modal').remove(); document.body.style.overflow = 'auto';" style="background: none; border: none; font-size: 24px; cursor: pointer;">&times;</button>
                </h2>
            </div>
            
            <div style="flex: 1; overflow-y: auto; padding: 15px; background: #fff;">
                ${messagesHTML}
            </div>
            
            <div style="border-top: 1px solid #ddd; padding: 15px; background: #f9f9f9;">
                <h4 style="margin: 0 0 10px 0; font-size: 14px;">Send Reply</h4>
                <form id="reply-form" style="display: flex; flex-direction: column; gap: 10px;">
                    <input type="text" id="reply-subject" placeholder="Subject" style="padding: 10px; border: 1px solid #ddd; border-radius: 6px; font-family: Arial; font-size: 14px;" required>
                    <textarea id="reply-content" placeholder="Type your reply..." style="padding: 10px; border: 1px solid #ddd; border-radius: 6px; font-family: Arial; font-size: 14px; resize: vertical; min-height: 80px;" required></textarea>
                    <div style="display: flex; gap: 10px; justify-content: flex-end;">
                        <button type="button" class="btn-secondary" onclick="this.closest('.modal').remove(); document.body.style.overflow = 'auto';" style="padding: 8px 16px; border: 1px solid #ddd; background: white; border-radius: 6px; cursor: pointer;">Cancel</button>
                        <button type="submit" class="btn-primary" style="padding: 8px 20px; background: #007bff; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 500;">Send</button>
                    </div>
                </form>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    document.body.style.overflow = 'hidden';
    
    // Handle form submission
    modal.querySelector('#reply-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const subject = modal.querySelector('#reply-subject').value;
        const content = modal.querySelector('#reply-content').value;
        
        if (!subject || !content) {
            alert('Please fill in all fields');
            return;
        }
        
        try {
            const response = await fetch('/message/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin',
                body: JSON.stringify({
                    to_email: conversation.email,
                    subject: subject,
                    content: content,
                    complaint_id: null
                })
            });
            
            const result = await response.json();
            if (result.success) {
                alert('Reply sent successfully!');
                modal.remove();
                document.body.style.overflow = 'auto';
                loadMessages();
            } else {
                alert('Error: ' + (result.error || 'Failed to send reply'));
            }
        } catch (error) {
            console.error('Error sending reply:', error);
            alert('Failed to send reply');
        }
    });
    
    modal.addEventListener('click', function(e) {
        if (e.target === this) {
            this.remove();
            document.body.style.overflow = 'auto';
        }
    });
}

// Mark a message as read
function markMessageRead(msgId, cardElement) {
    // For now, we'll just update the UI
    cardElement.classList.remove('unread');
    updateMessageCount(document.querySelectorAll('.message-card.unread').length);
}

// Update the message count badge
function updateMessageCount(count) {
    const badge = document.querySelector('#messages .notification-count');
    if (badge) {
        badge.textContent = count;
    }
}

// Show message details in a modal
function showMessageDetails(msg) {
    const modal = document.getElementById('complaint-details-modal') || document.getElementById('message-details-modal');
    if (!modal) return;

    const content = document.getElementById('complaint-details-content') || document.getElementById('message-details-content');
    if (!content) return;

    const timestamp = new Date(msg.timestamp).toLocaleString();
    content.innerHTML = `
        <h2>Message</h2>
        <div class="message-details-card">
            <div class="message-header">
                <h3>From: ${msg.from_name || msg.from_email}</h3>
                <p class="message-time">${timestamp}</p>
            </div>
            <div class="message-body">
                <p><strong>Subject:</strong> ${msg.subject || '(No subject)'}</p>
                <div class="message-content">
                    ${msg.content}
                </div>
                ${msg.complaint_id ? `<p><strong>Complaint ID:</strong> ${msg.complaint_id}</p>` : ''}
            </div>
            <div class="message-actions">
                <button class="btn-primary reply-btn" data-msg-id="${msg.id}">
                    <i class="fas fa-reply"></i> Reply
                </button>
                <button class="btn-secondary close-details">Close</button>
            </div>
        </div>
    `;

    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';

    // Close button
    content.querySelector('.close-details')?.addEventListener('click', () => {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    });

    // Reply button
    content.querySelector('.reply-btn')?.addEventListener('click', function() {
        showReplyForm(msg);
    });
}

// Show reply form for a message
function showReplyForm(originalMsg) {
    const modal = document.getElementById('complaint-details-modal') || document.getElementById('message-details-modal');
    const content = document.getElementById('complaint-details-content') || document.getElementById('message-details-content');
    if (!content) return;

    content.innerHTML = `
        <h2>Reply to Message</h2>
        <div class="reply-form-container">
            <p><strong>To:</strong> ${originalMsg.from_name || originalMsg.from_email}</p>
            <form id="reply-form">
                <div class="form-group">
                    <label for="reply-subject">Subject</label>
                    <input type="text" id="reply-subject" name="subject" 
                           value="Re: ${originalMsg.subject || ''}" required>
                </div>
                <div class="form-group">
                    <label for="reply-content">Message</label>
                    <textarea id="reply-content" name="content" required placeholder="Type your message..."></textarea>
                </div>
                <div class="form-actions">
                    <button type="submit" class="btn-primary">
                        <i class="fas fa-paper-plane"></i> Send Reply
                    </button>
                    <button type="button" class="btn-secondary close-details">Cancel</button>
                </div>
            </form>
        </div>
    `;

    content.querySelector('#reply-form')?.addEventListener('submit', async function(e) {
        e.preventDefault();
        const subject = document.getElementById('reply-subject').value;
        const content_text = document.getElementById('reply-content').value;

        try {
            const response = await fetch('/message/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin',
                body: JSON.stringify({
                    to_email: originalMsg.from_email,
                    subject: subject,
                    content: content_text,
                    complaint_id: originalMsg.complaint_id
                })
            });

            const result = await response.json();
            if (result.success) {
                alert('Reply sent successfully!');
                modal.style.display = 'none';
                document.body.style.overflow = 'auto';
                loadMessages();
            } else {
                alert('Error sending reply: ' + result.error);
            }
        } catch (error) {
            console.error('Error sending reply:', error);
            alert('Failed to send reply');
        }
    });

    content.querySelector('.close-details')?.addEventListener('click', () => {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    });
}

// Send a message to a resident or official
function sendMessage(toEmail, subject, content, complaintId) {
    fetch('/message/send', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin',
        body: JSON.stringify({
            to_email: toEmail,
            subject: subject,
            content: content,
            complaint_id: complaintId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Message sent successfully!');
            loadMessages();
            loadNotifications();
        } else {
            alert('Error sending message: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error sending message:', error);
        alert('Failed to send message');
    });
}

// Poll for new messages and notifications every 30 seconds
function startMessagingPoller() {
    // Initial load
    loadMessages();
    loadNotifications();
    
    // Load list based on role
    if (IS_OFFICIAL_DASHBOARD) {
        loadResidentsForMessaging();
        loadComplaintsForMessaging(true);
    } else {
        loadOfficialsForMessaging();
        loadComplaintsForMessaging(false);
    }

    // Poll every 30 seconds
    setInterval(() => {
        loadMessages();
        loadNotifications();
    }, 30000);

    // Also reload when window regains focus
    window.addEventListener('focus', () => {
        loadMessages();
        loadNotifications();
    });
}

// Setup compose message form
function setupComposeMessageForm() {
    if (IS_OFFICIAL_DASHBOARD) {
        setupOfficialComposeForm();
    } else {
        setupResidentComposeForm();
    }
}

// Setup for resident compose message form
function setupResidentComposeForm() {
    const composeBtn = document.getElementById('compose-message-btn');
    const composeModal = document.getElementById('compose-message-modal');
    const messagesModal = document.getElementById('messages-modal');
    const composeForm = document.getElementById('compose-message-form');
    const cancelBtn = composeModal?.querySelector('.cancel-btn');
    const closeBtn = composeModal?.querySelector('.close-btn');

    if (composeBtn) {
        composeBtn.addEventListener('click', (e) => {
            e.preventDefault();
            if (messagesModal) {
                messagesModal.style.display = 'none';
            }
            if (composeModal) {
                composeModal.style.display = 'block';
                document.body.style.overflow = 'hidden';
            }
            loadOfficialsForMessaging();
            loadComplaintsForMessaging(false);
        });
    }

    if (cancelBtn) {
        cancelBtn.addEventListener('click', (e) => {
            e.preventDefault();
            if (composeModal) {
                composeModal.style.display = 'none';
                document.body.style.overflow = 'auto';
            }
            if (messagesModal) {
                messagesModal.style.display = 'block';
            }
        });
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', (e) => {
            e.preventDefault();
            if (composeModal) {
                composeModal.style.display = 'none';
                document.body.style.overflow = 'auto';
            }
            if (messagesModal) {
                messagesModal.style.display = 'block';
            }
        });
    }

    if (composeForm) {
        composeForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const toEmail = document.getElementById('message-recipient').value;
            const subject = document.getElementById('message-subject').value;
            const content = document.getElementById('message-content').value;
            const complaintId = document.getElementById('message-complaint').value;

            if (!toEmail) {
                alert('Please select an official');
                return;
            }

            if (!subject || !content) {
                alert('Please fill in all required fields');
                return;
            }

            try {
                const response = await fetch('/message/send', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    credentials: 'same-origin',
                    body: JSON.stringify({
                        to_email: toEmail,
                        subject: subject,
                        content: content,
                        complaint_id: complaintId || null
                    })
                });

                const result = await response.json();
                if (result.success) {
                    alert('Message sent successfully!');
                    composeForm.reset();
                    if (composeModal) {
                        composeModal.style.display = 'none';
                        document.body.style.overflow = 'auto';
                    }
                    if (messagesModal) {
                        messagesModal.style.display = 'block';
                    }
                    loadMessages();
                    loadNotifications();
                } else {
                    alert('Error: ' + (result.error || 'Failed to send message'));
                }
            } catch (error) {
                console.error('Error sending message:', error);
                alert('Failed to send message');
            }
        });
    }
}

// Setup for official compose message form
function setupOfficialComposeForm() {
    const composeBtn = document.getElementById('compose-message-btn-official');
    const composeModal = document.getElementById('compose-message-modal-official');
    const messagesModal = document.getElementById('messages-modal');
    const composeForm = document.getElementById('compose-message-form-official');
    const cancelBtn = composeModal?.querySelector('.cancel-btn');
    const closeBtn = composeModal?.querySelector('.close-btn');

    if (composeBtn) {
        composeBtn.addEventListener('click', (e) => {
            e.preventDefault();
            if (messagesModal) {
                messagesModal.style.display = 'none';
            }
            if (composeModal) {
                composeModal.style.display = 'block';
                document.body.style.overflow = 'hidden';
            }
            loadResidentsForMessaging();
            loadComplaintsForMessaging(true);
        });
    }

    if (cancelBtn) {
        cancelBtn.addEventListener('click', (e) => {
            e.preventDefault();
            if (composeModal) {
                composeModal.style.display = 'none';
                document.body.style.overflow = 'auto';
            }
            if (messagesModal) {
                messagesModal.style.display = 'block';
            }
        });
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', (e) => {
            e.preventDefault();
            if (composeModal) {
                composeModal.style.display = 'none';
                document.body.style.overflow = 'auto';
            }
            if (messagesModal) {
                messagesModal.style.display = 'block';
            }
        });
    }

    if (composeForm) {
        composeForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const toEmail = document.getElementById('message-recipient-official').value;
            const subject = document.getElementById('message-subject-official').value;
            const content = document.getElementById('message-content-official').value;
            const complaintId = document.getElementById('message-complaint-official').value;

            if (!toEmail) {
                alert('Please select a resident');
                return;
            }

            if (!subject || !content) {
                alert('Please fill in all required fields');
                return;
            }

            try {
                const response = await fetch('/message/send', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    credentials: 'same-origin',
                    body: JSON.stringify({
                        to_email: toEmail,
                        subject: subject,
                        content: content,
                        complaint_id: complaintId || null
                    })
                });

                const result = await response.json();
                if (result.success) {
                    alert('Message sent successfully!');
                    composeForm.reset();
                    if (composeModal) {
                        composeModal.style.display = 'none';
                        document.body.style.overflow = 'auto';
                    }
                    if (messagesModal) {
                        messagesModal.style.display = 'block';
                    }
                    loadMessages();
                    loadNotifications();
                } else {
                    alert('Error: ' + (result.error || 'Failed to send message'));
                }
            } catch (error) {
                console.error('Error sending message:', error);
                alert('Failed to send message');
            }
        });
    }
}

// Initialize messaging on page load
document.addEventListener('DOMContentLoaded', function() {
    // Wait a short moment for other scripts to load
    setTimeout(() => {
        startMessagingPoller();
        setupComposeMessageForm();
        setupMessageNotificationNavLinks();
    }, 500);
});

// Setup navigation links for messages and notifications
function setupMessageNotificationNavLinks() {
    // Messages nav link - works for both dashboards
    const messagesNavLink = document.querySelector('a[href="#messages"]');
    
    if (messagesNavLink) {
        messagesNavLink.addEventListener('click', (e) => {
            e.preventDefault();
            const modal = document.getElementById('messages-modal');
            if (modal) {
                modal.style.display = 'block';
                document.body.style.overflow = 'hidden';
                loadMessages();
            }
        });
    }
    
    // Notifications nav link - works for both dashboards
    const notificationsNavLink = document.querySelector('a[href="#notifications"]');
    
    if (notificationsNavLink) {
        notificationsNavLink.addEventListener('click', (e) => {
            e.preventDefault();
            const modal = document.getElementById('notifications-modal');
            if (modal) {
                modal.style.display = 'block';
                document.body.style.overflow = 'hidden';
                loadNotifications();
            }
        });
    }
    
    // Close modals when clicking close button or outside
    document.querySelectorAll('#messages-modal .close-btn, #notifications-modal .close-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const modal = this.closest('.modal');
            if (modal) {
                modal.style.display = 'none';
                document.body.style.overflow = 'auto';
            }
        });
    });
    
    // Close on outside click
    document.getElementById('messages-modal')?.addEventListener('click', function(e) {
        if (e.target === this) {
            this.style.display = 'none';
            document.body.style.overflow = 'auto';
        }
    });
    
    document.getElementById('notifications-modal')?.addEventListener('click', function(e) {
        if (e.target === this) {
            this.style.display = 'none';
            document.body.style.overflow = 'auto';
        }
    });
    
    // Setup compose button inside messages modal for officials
    const openComposeBtn = document.getElementById('open-compose-modal-btn-official');
    const openComposeBtnNav = document.getElementById('compose-message-btn-official-nav');
    
    if (openComposeBtn) {
        openComposeBtn.addEventListener('click', (e) => {
            e.preventDefault();
            const messagesModal = document.getElementById('messages-modal');
            const composeModal = document.getElementById('compose-message-modal-official');
            if (messagesModal) {
                messagesModal.style.display = 'none';
            }
            if (composeModal) {
                composeModal.style.display = 'block';
                document.body.style.overflow = 'hidden';
            }
            loadResidentsForMessaging();
            loadComplaintsForMessaging(true);
        });
    }
    
    if (openComposeBtnNav) {
        openComposeBtnNav.addEventListener('click', (e) => {
            e.preventDefault();
            const messagesModal = document.getElementById('messages-modal');
            const composeModal = document.getElementById('compose-message-modal-official');
            if (messagesModal) {
                messagesModal.style.display = 'none';
            }
            if (composeModal) {
                composeModal.style.display = 'block';
                document.body.style.overflow = 'hidden';
            }
            loadResidentsForMessaging();
            loadComplaintsForMessaging(true);
        });
    }
}
