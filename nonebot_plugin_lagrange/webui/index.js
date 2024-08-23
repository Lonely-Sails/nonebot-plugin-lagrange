var token = null;
var websocket = null;

var log_console = null;
var action_buttons = null;

var mask_element = null;
var current_element = null;

function request(url, data, callback) {
    let request = new XMLHttpRequest();
    request.open("POST", url, true);
    request.setRequestHeader("token", token);
    request.setRequestHeader("Content-Type", "application/json");
    request.onreadystatechange = () => {
        if (request.readyState === 4) {
            if (request.status === 200) {
                let response = JSON.parse(request.responseText);
                if (response["success"]) {
                    callback(response["data"]);
                    return;
                }
                alert(response["message"]);
            } else if (request.status === 403) {
                alert("无权限访问！请检查 token 是否正确！");
            } else {
                alert("错误的状态代码：" + request.status);
                if (!mask_element.className) mask_element.className = "hidden";
            }
        }
    };
    request.send(JSON.stringify(data));
}

function select_name(event) {
    if (current_element.textContent == event.target.textContent) return;
    current_element.className = "";
    event.target.className = "active";
    current_element = event.target;
    request(
        "lagrange/api/status",
        { name: current_element.textContent },
        (response_data) => {
            log_console.innerHTML = "";
            websocket.send(event.target.textContent);
            if (response_data) action_buttons.className = "started";
            else action_buttons.className = "stopped";
        }
    );
}

function action(event) {
    request(
        `lagrange/api/${event.target.id}`,
        { name: current_element.textContent },
        (_) => {
            if (event.target.id === "stop") action_buttons.className = "stopped";
            else if (event.target.id === "logout") {
                action_buttons.className = "stopped";
                alert("已退出登录！");
            } else if (event.target.id === "start") {
                log_console.innerHTML = "";
                action_buttons.className = "started";
            }
        }
    );
}

function show_qrcode() {
    request(
        "lagrange/api/qrcode",
        { name: current_element.textContent },
        (response_data) => {
            let qrcode_img = document.createElement("img");
            qrcode_img.src = `data:image/png;base64,${response_data}`;
            mask_element.appendChild(qrcode_img);
            mask_element.className = "";
        }
    );
}

function hide_qrcode() {
    let qrcode_img = null;
    if (qrcode_img = mask_element.querySelector("img")) {
        mask_element.className = "hidden";
        setTimeout(() => {
            mask_element.removeChild(qrcode_img);
        }, 300);
    }
}

function create_bot(event) {
    let name = prompt("请输入新建机器人的名称：");
    let selections = current_element.parentNode;
    if (name) {
        if (confirm(`确认创建名为「${name}」的机器人？`)) {
            request("lagrange/api/create", { name: name }, (_) => {
                let selection = document.createElement("span");
                selection.textContent = name;
                selection.addEventListener("click", select_name);
                selections.appendChild(selection);
                alert("机器人创建成功！");
            });
        }
    }
}

function delete_bot(event) {
    let selections = current_element.parentNode;
    if (selections.children.length === 3) alert("至少需要保留一个机器人！");
    else if (confirm("确认删除当前机器人？")) {
        request(
            "lagrange/api/delete",
            { name: current_element.textContent },
            (_) => {
                selections.removeChild(current_element);
                current_element = selections.children[0];
                selection.className = "active";
                request("lagrange/api/status", { name: current_element.textContent }, (response_data) => {
                    if (response_data) action_buttons.className = "started";
                    else action_buttons.className = "stopped";
                });
            }
        );
    }
}

function update_lagrange(event) {
    if (confirm("确认更新 Lagrange 到最新版本？")) {
        alert("正在更新 Lagrange，请稍候...");
        log_console.innerHTML = "";
        mask_element.className = "";
        request("lagrange/api/update", {}, (_) => {
            alert("Lagrange 更新成功！");
            mask_element.className = "hidden";
        });
    }
}

function init() {
    let params = new URLSearchParams(window.location.search);
    token = params.get("token");

    let append_button = document.querySelector("nav span#append");
    let update_button = document.querySelector("nav span#update");

    let stop_button = document.querySelector("main div#actions span#stop");
    let start_button = document.querySelector("main div#actions span#start");
    let delete_button = document.querySelector("main div#actions span#delete");
    let logout_button = document.querySelector("main div#actions span#logout");
    let qrcode_button = document.querySelector("main div#actions span#qrcode");

    append_button.addEventListener("click", create_bot);
    delete_button.addEventListener("click", delete_bot);
    update_button.addEventListener("click", update_lagrange);

    stop_button.addEventListener("click", action);
    start_button.addEventListener("click", action);
    logout_button.addEventListener("click", action);
    qrcode_button.addEventListener("click", show_qrcode);

    websocket = new WebSocket(
        `ws://${window.location.host}/lagrange/api/logs?token=${token}`
    );
    websocket.onmessage = (event) => {
        let log_line = event.data;
        let log_element = document.createElement("p");
        if (log_line.startsWith("§error§")) {
            log_line = log_line.replace("§error§", "");
            log_element.style.color = "red";
        } else if (log_line.startsWith("dialog")) {
            log_line = log_line.replace("§dialog§", "");
            return alert(log_line);
        } else if (log_line.startsWith("fail")) log_element.style.color = "red";
        else if (log_line.startsWith("warn")) log_element.style.color = "yellow";
        else if (log_line.includes("[FATAL]")) log_element.style.color = 'red';
        else if (log_line.includes("[WARNING]")) log_element.style.color = 'yellow';
        log_element.textContent = log_line;
        log_console.appendChild(log_element);
        log_element.scrollIntoView({ behavior: "smooth" });
    };

    mask_element = document.querySelector("body div#mask");
    log_console = document.querySelector("body main div#log");
    action_buttons = document.querySelector("body main div#actions");
    let selections = document.querySelector("body nav");
    request("lagrange/api/names", {}, (response_data) => {
        for (var index = 0; index < response_data.length; index++) {
            var selection = document.createElement("span");
            selection.textContent = response_data[index];
            selection.addEventListener("click", select_name);
            selections.appendChild(selection);
            if (index === 0) {
                current_element = selection;
                var name = response_data[index];
                selection.className = "active";
                websocket.onopen = () => {
                    websocket.send(name);
                };
                request("lagrange/api/status", { name: name }, (response_data) => {
                    if (response_data) action_buttons.className = "started";
                    else action_buttons.className = "stopped";
                });
            }
        }
    });
}

function exit() {
    websocket.close();
}

window.addEventListener("load", init);
window.addEventListener("close", exit);
window.addEventListener("click", hide_qrcode);
