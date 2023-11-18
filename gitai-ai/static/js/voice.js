var connection = new WebSocket("ws://localhost:8080/ws2/");

connection.onmessage = function (e) {
    const data = JSON.parse(e.data);
    var redirect_page = data[0].redirect_page
    console.log(data);
    if (redirect_page == 1) {
        window.location.href = 'http://127.0.0.1:8080';
    } else {
        window.location.href = 'http://127.0.0.1:8080/voice2';
    }
};

connection.onclose = function (e) {
    console.error('Chat socket closed unexpectedly');
};