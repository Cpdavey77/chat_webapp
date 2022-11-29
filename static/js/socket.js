document.addEventListener("DOMContentLoaded", () => {
    var socket = io();
    let room = document.querySelector(".current_room").innerHTML
    joinRoom(room);

    //get message from backend
    socket.on("message", data => {
        const p = document.createElement("p");
        const span_username = document.createElement('span');
        const br = document.createElement("br");

        if (data.username) {
            span_username.innerText = data.username;
            p.innerHTML += span_username.outerHTML + " " + data.timestamp + br.outerHTML + data.msg
            document.querySelector("#display_message_section").append(p);
        } else {
            printSysMsg(data.msg);
        }
    }); 

    //send message to backend
    document.querySelector("#send_message").onclick = () => {
        user_message = document.querySelector("#user_message").value
        if (user_message != "") {
            socket.send({"msg": user_message, "username": username, "room": room});
            socket.emit("send_msg", {"username": username, "room": room})
            document.querySelector('#user_message').value = "";
        }
        
    };
    //join a room
    function joinRoom(room) {
        socket.emit("join", {"username": username, "room": room});
    }
    //prints message from backend
    function printSysMsg(msg) {
        const p = document.createElement("p");
        p.innerHTML = msg;
        document.querySelector('#display_message_section').append(p);
    }
});
