$( document ).ready(function() {

    init(); // load data
    /*
    * Hide containers and get user chats
    */

    function init() {
        $('.new-chat').hide();
        $("#dmChats").hide();
        $(".send-message").hide();
        get_chats();
    }
    /*
    * Reload user chats
    */
    $(".reload-chats").click(function() {
        $('.student-list').show(); // Show all students
        get_chats();
        let other_username = $('#username-message').val();
        get_messages(other_username);
    });

    /*
    * Show new chat div
    */
    $(".new-chat-btn").click(function() {
        $(this).hide();
        $('.new-chat').show();
        // Scroll div
        $('html,body').animate({
            scrollTop: $(".new-chat").offset().top
        }, 'slow');
    });

    /*
    * Add student to the chat list
    * Open an empty chat
    */
    $("#all_students_list li a").click(function(e) {
        // Get chat attributes
        let a_class = $(this).attr('class');
        let other_username = a_class.replace('list-','');
        let other_name = $(this).text();
        let chat = {
            'sender_user__username' : USER_USERNAME,
            'receiver_user__username' : other_username,
            'receiver_user__profile__name' : other_name,
            'min_viewed' : true
        };
        
        // Remove 'no chats' message when student doesn't have chats
        if ($('#list .recent-messages-list').text() == 'No tienes conversaciones recientes.') {
            $('#list .recent-messages-list').html('');
        }

        // Add user to the chat list
        generate_list_html(chat);

        // Remove from all students list
        $('.student-list.list-' + other_username).hide();

        // Update click handler
        $('.user-list').click(function() {
            other_username = $(this).attr('id');
            get_messages(other_username);
        });

        // Open new empty chat
        get_messages(other_username); 

        // Scroll div
        $('html,body').animate({
            scrollTop: $("#messages-loading").offset().top
        }, 'slow');
    });
    
    /*
    * Submit a new message
    */
    $('#new-message-form').submit(function(e) {
                
        var url = URL_NEW_MESSAGE;
        data = $('#new-message-form').serializeArray();
        params = {
            "message" : data[1].value,
            "other_username" : data[2].value,
            "course_id" : COURSE_ID
        }
        console.log(params);
        $.ajax({
            data:  params,
            url:   url,
            type:  'post',
            beforeSend: function () {
                /*
                * Set submit button disabled
                */
                $('.submit-message').prop("disabled", true);
            },
            success:  function (response) {
                /*
                * Reset input value, and reload chat messages
                */
                $('#new-message').val('');
                get_messages(params.other_username);
            },
            error: function (xhr, ajaxOptions, thrownError) {
                alert("Error, intente nuevamente más tarde");
                console.log(xhr);
                console.log(ajaxOptions);
                console.log(thrownError);
            },
            complete: function() {
                /*
                * Set submit button enabled
                */
                $('.submit-message').prop("disabled", false);
            }
        });
        e.preventDefault();
    });

    /*
    * Get chat lists with info from another users
    */
    function get_chats(){
        var url = URL_GET_STUDENT_CHAT;
        $.ajax({
            url:   url,
            beforeSend: function () {
                // Show loading
                $('#list-loading').show();
            },
            success:  function (response) {
                user_data = response;

                // Reset html div
                $('#list .recent-messages-list').html('');

                // Show message if user doesnt' have chats already
                if (user_data.length == 0){
                    $('#list .recent-messages-list').html('No tienes conversaciones recientes.');
                    $('.new-chat').show();
                    $('.new-chat-btn').hide();
                }

                // Create list for each user
                for(chat of user_data) {
                    generate_list_html(chat);
                }
                // Click handler. Show users messages on click.
                $('.user-list').click(function() {
                    other_username = $(this).attr('id');
                    get_messages(other_username);
                });
                // Set keyup function after all student list is loaded and uptaded  
                $('#search_input').keyup(search);
            },
            error: function (xhr, ajaxOptions, thrownError) {
                alert("Error, intente nuevamente más tarde");
                console.log(xhr);
                console.log(ajaxOptions);
                console.log(thrownError);
            },
            complete: function() {
                // Hide loading
                $('#list-loading').hide();
            }
        });
    }


    /*
    * Get all messages between two users (logged user and another)
    */
    function get_messages(other_username) {
        $('#username-message').val(other_username);
        var url = URL_GET_MESSAGES;
        url = url.replace(DEFAULT_USERNAME, other_username);
        $.ajax({
            url:   url,
            beforeSend: function () {
                // Show loading
                $('#messages-loading').show();
            },
            success:  function (response) {
                data = response;

                // Reset html div
                $('#dmChats').html('');

                // Show each message
                for(message of data) {
                    generate_messages_html(message);
                }
                $("#dmChats").show();

                // Scroll to bottom (end of messages)
                $("#dmChats").scrollTop($("#dmChats").prop("scrollHeight"));

                // Show submit input/button
                $(".send-message").show();
            },
            error: function (xhr, ajaxOptions, thrownError) {
                alert("Error, intente nuevamente más tarde");
                console.log(xhr);
                console.log(ajaxOptions);
                console.log(thrownError);
            },
            complete: function() {
                // Hide loading
                $('#messages-loading').hide();
            }
        });
    }

    /*
    * Generate element on list from each user
    */
    function generate_list_html(chat) {
        username = USER_USERNAME;
        // Define otherusername 
        if (username == chat.sender_user__username) {
            other_username = chat.receiver_user__username;
            profile_name = chat.receiver_user__profile__name;
        } else {
            other_username = chat.sender_user__username; 
            profile_name = chat.sender_user__profile__name;
        }
        // min_viewed boolean: false if the user didn't read all messages
        if (chat.min_viewed || username == chat.sender_user__username)
            status = "";
        else
            status = "<strong>Tienes nuevos mensajes !</strong>";

        // Append <li> element with other user info
        $('#list .recent-messages-list').append(
            '<li class="user-list" id="' + other_username + '">' + 
                '<span class="icon-list"><i class="fa fa-chevron-right"></i></span>'+
                '<div class="info-list">'+
                    '<span class="name-list">' + profile_name + '</span>'+
                    '<br/>'+
                    '<span class="status-list">' + status + '</span>'+
                '</div>'+
              '</li>'
        );
        
        // delete user in the list of all students
        $('.student-list.list-' + other_username).hide();
    }

    /*
    * Generate each message from chat
    */
    function generate_messages_html(message) {
        username = USER_USERNAME;
        date = new Date(message.created_at.$date);
        // Define sender and receiver user and set respective class
        if ( message.receiver_user__username == username ) {
            // Escape html in message.text
            let dm = '<div class="otherDM other chat-message">' + escapeHtml(message.text) + '</div>';
            let detail = '<span class="other">' + message.sender_user__profile__name + ' - ' + date.toLocaleString() + '</span>';
            var dmWrapper = '<div class="dmWrapper">' +
                                '<div class="inlineContainer">' +
                                    dm +
                                '</div>' +
                                detail +
                            '</div>';
        } else {
            let dm = '<div class="DM own chat-message">' + escapeHtml(message.text) + '</div>';
            let detail = '<span class="own">' + message.sender_user__profile__name + ' - ' + date.toLocaleString() + '</span>';
            var dmWrapper = '<div class="dmWrapper">' +
                                '<div class="inlineContainer own">' +
                                    dm +
                                '</div>' +
                                detail +
                            '</div>';
        }
        
        // Append div to the direct messages chat
        $('#dmChats').append(dmWrapper);
    };

    /*
    * Search function used in all student lists
    */
    function search() {
        // Declare variables
        var input, filter, ul, li, a, i, txtValue;
        input = document.getElementById('search_input');
        filter = input.value.toUpperCase();
        ul = document.getElementById("all_students_list");
        li = ul.getElementsByTagName('li');
      
        // Loop through all list items, and hide those who don't match the search query
        for (i = 0; i < li.length; i++) {
          a = li[i].getElementsByTagName("a")[0];
          if (a) {
            txtValue = a.textContent || a.innerText;
            if (txtValue.toUpperCase().indexOf(filter) > -1) {
              li[i].style.display = "";
            } else {
              li[i].style.display = "none";
            }
          }
        }
    }

    /*
    * Escape HTML from string
    */
    var entityMap = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;',
        '/': '&#x2F;',
        '`': '&#x60;',
        '=': '&#x3D;'
    };
    function escapeHtml (string) {
        return String(string).replace(/[&<>"'`=\/]/g, function (s) {
          return entityMap[s];
        });
    }
});