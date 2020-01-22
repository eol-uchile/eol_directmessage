$( document ).ready(function() {
    get_chats();

    function get_chats(){
        var url = URL_GET_STUDENT_CHAT;
        $.ajax({
            url:   url,
            beforeSend: function () {
                $('#list-loading').show();
            },
            success:  function (response) {
                console.log(response);
                user_data = response;
                $('#list').html('');
                for(chat of user_data) {
                    generate_list_html(chat);
                }
                $('.open_chat').click(get_messages);
            },
            error: function (xhr, ajaxOptions, thrownError) {
                alert("Error, intente nuevamente más tarde");
                console.log(xhr);
                console.log(ajaxOptions);
                console.log(thrownError);
            },
            complete: function() {
                $('#list-loading').hide();
            }
        });
    }

    function get_messages() {
        var other_username = $(this).attr('id');
        var url = URL_GET_MESSAGES;
        url = url.replace(DEFAULT_USERNAME, other_username);
        $.ajax({
            url:   url,
            beforeSend: function () {
                $('#messages-loading').show();
            },
            success:  function (response) {
                console.log(response);
                data = response;
                $('#dmChats').html('');
                for(message of data) {
                    generate_messages_html(message);
                }
            },
            error: function (xhr, ajaxOptions, thrownError) {
                alert("Error, intente nuevamente más tarde");
                console.log(xhr);
                console.log(ajaxOptions);
                console.log(thrownError);
            },
            complete: function() {
                $('#messages-loading').hide();
            }
        });
    }

    function generate_list_html(chat) {
        username = USER_USERNAME;
        if (username == chat.sender_user__profile__name) {
            other_username = chat.receiver_user__username;
            $('#list').append("<span class='open_chat' id='" + other_username + "'> - " + chat.receiver_user__profile__name + "</span>");
        } else {
            other_username = chat.sender_user__username; 
            $('#list').append("<span class='open_chat' id='" + other_username + "'> - " + chat.sender_user__profile__name + "</span>");
        }
        if (chat.min_viewed || username == chat.sender_user__profile__name)
            $('#list').append(" - No tienes nuevos mensajes <br/>");
        else
            $('#list').append(" - <strong>Tienes nuevos mensajes</strong> <br/>");
        
        // delete user in the list of all students
        $('.list-' + other_username).remove();
    }

    function generate_messages_html(message) {
        username = USER_USERNAME;
        date = new Date(message.created_at.$date);
        if ( message.receiver_user__username == username ) {
            let dm = '<div class="otherDM other">' + message.text + '</div>';
            let detail = '<span class="other">' + message.sender_user__profile__name + ' - ' + date.toLocaleString() + '</span>';
            var dmWrapper = '<div class="dmWrapper">' +
                                '<div class="inlineContainer">' +
                                    dm +
                                '</div>' +
                                detail +
                            '</div>';
        } else {
            let dm = '<div class="DM own">' + message.text + '</div>';
            let detail = '<span class="own">' + message.sender_user__profile__name + ' - ' + date.toLocaleString() + '</span>';
            var dmWrapper = '<div class="dmWrapper">' +
                                '<div class="inlineContainer own">' +
                                    dm +
                                '</div>' +
                                detail +
                            '</div>';
        }
        

        $('#dmChats').append(dmWrapper);
        /*
        username = USER_USERNAME;
        date = new Date(message.created_at.$date);
        message_text =  message.sender_user__profile__name + "(" + date + "): " + message.text + "<br/>";
        if ( (message.receiver_user__username == username) && !message.viewed)
        {
            $('#messages').append("<strong>" + message_text + "</strong>");
            // set message.viewed TRUE
        } else {
            $('#messages').append(message_text);
        }
        */
    };
});