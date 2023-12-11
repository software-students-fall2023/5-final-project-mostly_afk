$(document).ready(function() {
    let sessionCleared = false;
    let selectedPersonality = "helpful";

    function scrollToBottom() {
        $('.chat-box').scrollTop($('.chat-box')[0].scrollHeight);
    }

    function clearSession() {
        if (!sessionCleared) {
            fetch('/clear_session', {
                method: 'POST'
            })
            .then(response => {
                if (response.ok) {
                    sessionCleared = true;
                } else {
                    console.error('Failed to clear the session.');
                }
            })
            .catch(error => {
                console.error('Error clearing the session:', error);
            });
        }
    }

    window.addEventListener('beforeunload', clearSession);
    window.addEventListener('unload', clearSession);
    
    $('.sidebar-item').click(function() {
        selectedPersonality = $(this).data('personality');
        $('.sidebar-item').removeClass('active');
        $(this).addClass('active');
        $('.chat-box').empty();
        $('.chat-title').text(selectedPersonality);
        scrollToBottom();
    });

    $('.message-form').on('submit', function(e) {
        e.preventDefault();
        let userInput = $('#user_input').val();
        $('#user_input').val('');
        if (userInput.trim() !== '') {
            $('.chat-box').append('<div class="message user">' + userInput + '</div>');
            scrollToBottom();
            $.post('/get_response', { user_input: userInput, personality: selectedPersonality }, function(response) {
                $('.chat-box').append('<div class="message ai">' + response + '</div>');
                scrollToBottom();
            });
            // $.post('/get_response', { user_input: userInput }, function(response) {
            //     $('.chat-box').append('<div class="message ai">' + response + '</div>');
            // });
        }
    });
});