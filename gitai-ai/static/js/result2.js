var connection = new WebSocket("ws://localhost:8080/ws4/");

connection.onmessage = function (e) {
    const data = JSON.parse(e.data);
    var text = data[0].text

    if (data[0].is_finished) {
        window.location.href = 'http://127.0.0.1:8080/graph';
        connection.close();
    } else {
        window.location.href = 'http://127.0.0.1:8080/voice2';
        connection.close();
    }
};

connection.onclose = function (e) {
    console.error('Chat socket closed unexpectedly');
};