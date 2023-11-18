var connection = new WebSocket("ws://localhost:8080/ws/");

if (window.location.href == 'http://127.0.0.1:8080/'){
    var senser_state = 0;
} else if (window.location.href == 'http://127.0.0.1:8080/voice'){
    var senser_state = 1;
}
connection.onmessage = function (e) {
    const data = JSON.parse(e.data);
    console.log(data);
    if (senser_state == 0 && data[0].exist == 1) {
        senser_state = 1;
        window.location.href = 'http://127.0.0.1:8080/voice';
        connection.close();
    } else if (senser_state == 1 && data[0].exist == 0) {
        senser_state = 0;
        window.location.href = 'http://127.0.0.1:8080/';
    }
};

connection.onclose = function(e) {
    console.error('Chat socket closed unexpectedly');
};