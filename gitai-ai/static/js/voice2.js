var connection = new WebSocket("ws://localhost:8080/ws3/");

connection.onmessage = function (e) {
    const data = JSON.parse(e.data);
    var text = data[0].text
    var similar_words = data[0].similar_words

    var redirect_page = data[0].redirect_page
    console.log(data);
    if (redirect_page == 1) {
        window.location.href = 'http://127.0.0.1:8080';
    }

    else if (data[0].q_num == 0) {
        const typewriter = (param) => {
            let el = document.querySelector(param.el);
            let speed = param.speed;
            let string = param.string.split("");
            string.forEach((char, index) => {
                setTimeout(() => {
                    el.textContent += char;
                }, speed * index);
            });
        };
        typewriter({
            el: "#typewriter", //要素
            string: text, //文字列
            speed: 250 //速度
        });
    } else if (data[0].q_num == 1) {
        document.getElementById('typewriter').style.display = "none";
        const typewriter = (param) => {
            let el = document.querySelector(param.el);
            let speed = param.speed;
            let string = param.string.split("");
            string.forEach((char, index) => {
                setTimeout(() => {
                    el.textContent += char;
                }, speed * index);
            });
        };
        typewriter({
            el: "#typewriter2", //要素
            string: similar_words, //文字列
            speed: 250 //速度
        });
    } else {
        window.location.href = 'http://127.0.0.1:8080/result?text=' + text;
    }
};

connection.onclose = function (e) {
    console.error('Chat socket closed unexpectedly');
};