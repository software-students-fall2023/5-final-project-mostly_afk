$(document).ready(function () {
    let selectedPersonality = "Helpful Mom";
    let conversationHistories = {};

    function scrollToBottom() {
        $('.chat-box').scrollTop($('.chat-box')[0].scrollHeight);
    }

    function updateChatBox() {
        const messages = conversationHistories[selectedPersonality] || [];
        $('.chat-box').empty();
        messages.forEach(msg => {
            const messageClass = msg.type === 'user' ? 'message user' : 'message ai';
            $('.chat-box').append('<div class="' + messageClass + '">' + msg.content + '</div>');
        });
        scrollToBottom();
    }

    function loadUserChats() {
        $.get('/load_chats', { user_id: currentUserID }, function (response) {
            if (response.error) {
                console.error(response.error);
                return;
            }
            conversationHistories = response;
            updateChatBox();
        });
    }

    $('.sidebar-item').click(function () {
        selectedPersonality = $(this).data('personality');
        $('.sidebar-item').removeClass('active');
        $(this).addClass('active');
        $('.chat-title').text(selectedPersonality);
        updateChatBox();
    });

    $('.message-form').on('submit', function (e) {
        e.preventDefault();
        let userInput = $('#user_input').val();
        $('#user_input').val('');
        if (userInput.trim() !== '') {
            let userMessage = { type: 'user', content: userInput };
            if (!conversationHistories[selectedPersonality]) {
                conversationHistories[selectedPersonality] = [];
            }
            conversationHistories[selectedPersonality].push(userMessage);
            updateChatBox();
            $.post('/get_response', { user_input: userInput, personality: selectedPersonality }, function (response) {
                let aiMessage = { type: 'ai', content: response };
                conversationHistories[selectedPersonality].push(aiMessage);
                updateChatBox();
            });
        }
    });

    loadUserChats(); // Load chats when the document is ready

    // Function to show the modal
    function showModal() {
        $('#confirmation-modal').show();
    }

    // Function to hide the modal
    function hideModal() {
        $('#confirmation-modal').hide();
    }

    // Click handler for "Clear Chat" button
    $('#clear-chat').click(function () {
        showModal();
    });

    // Click handler for "No" button in modal
    $('#cancel-clear').click(function () {
        hideModal();
    });

    // Click handler for "Yes" button in modal
    $('#confirm-clear').click(function () {
        // Make a POST request to the clear chat route
        $.post('/clear_chats', { user_id: currentUserID }, function (response) {
            if (response.status === "success") {
                // Clear the chat histories from the front end
                conversationHistories = {};
                updateChatBox();
                hideModal();
            } else {
                console.error('Failed to clear chats:', response.error);
            }
        });
    });

    // Click handler for close button in modal
    $('.close').click(function () {
        hideModal();
    });
});
