function doShowHideBtn(divTask) {

    const nTaskId = divTask.getAttribute("id");
    if (nTaskId) {
        
        fetch('/check_task', {
            method: 'POST',
            headers: {
                "accept" : "application/json",
                "Content-Type": "application/json"
            },
            body: JSON.stringify({"id_task": nTaskId})
        })
        .then(response => response.json())
        .then(result => {
        
            if (result["status"] == "В куче") {
                
                $('.btn-warning').show();
                $('.btn-success').hide();
                $('.btn-danger').hide();

            }

            if (result["status"] == "В работе") {
                
                $('.btn-warning').hide();
                $('.btn-success').show();
                if (result["type"] !== 3) {

                    $('.btn-danger').show();

                } else {

                    $('.btn-danger').hide();

                }

            }

            if (result["status"] == "Готово") {
                
                $('.btn-warning').hide();
                $('.btn-success').hide();
                if (result["type"] !== 3) {

                    $('.btn-danger').show();

                } else {

                    $('.btn-danger').hide();

                }

            }

        });

        //скрытие кнопок для подзадач
        fetch('/check_subtask', {
            method: 'POST',
            headers: {
                "accept" : "application/json",
                "Content-Type": "application/json"
            },
            body: JSON.stringify({"id_task": nTaskId})
        })
        .then(response => response.json())
        .then(result => {

            if (result === true) {

                $('.btn-dark').hide();
                $('.btn-success').hide();

            } else {

                $('.btn-dark').show();

            }
        
        });

    }

}

function doSendPushNotify(objParamPush) {

    fetch('/send_push', {
        method: 'POST',
        headers: {
            "accept" : "application/json",
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            "title": "FamilyTask",
            "body":  "По " + objParamPush["title_task"] + " был обновлен статус на " + objParamPush["status_name"],
            "param": sessionStorage.getItem("PushParam")
        })
    })
    .then(response => response.json())
    .then(result => {
    
        console.log(result);
    
    });

}

function updateTask(strUrl) {

    const divTask = document.querySelector('[check=true]');
    if (divTask) {

        const nTaskId = divTask.getAttribute("id");
        if (nTaskId) {
        
            fetch(strUrl, {
                method: 'POST',
                headers: {
                    "accept" : "application/json",
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({"id_task": nTaskId})
            })
            .then(response => response.json())
            .then(result => {
                
                const tableTask = document.querySelector('.table-responsive');
                tableTask.innerHTML = result["html_tasks"];

                const table = document.querySelector('.table-borderless');
                let spanTimeParamByTask = ""; //переменная для временных параметров в задаче
                for (let iRows = 0; iRows < table.rows.length; iRows++) {

                    for (let iCell = 0; iCell < table.rows[iRows].cells.length; iCell++) {
                    
                        spanTimeParamByTask = table.rows[iRows].cells[iCell].getElementsByTagName('span');
                        for (let itemSpan = 0; itemSpan < spanTimeParamByTask.length; itemSpan++) {

                            if (spanTimeParamByTask[itemSpan].classList.contains('flask-moment')) {

                                spanTimeParamByTask[itemSpan].style = "";
                                spanTimeParamByTask[itemSpan].setAttribute("class", "");
                                spanTimeParamByTask[itemSpan].innerText = moment(spanTimeParamByTask[itemSpan].getAttribute("data-timestamp")).format(spanTimeParamByTask[itemSpan].getAttribute("data-format"));

                            }

                        }

                    }

                }
                spanTimeParamByTask = null;
                initClickDivTask(); //добавляем функцию на клик для блока с задачами
                const divMoveTask = document.getElementById(nTaskId);
                divMoveTask.style["border"] = "2px solid #21c1cc";
                divMoveTask.style["box-shadow"] = "5px 5px 5px 5px #ababab";

                doShowHideBtn(divTask); //обновление кнопок по задаче
                divMoveTask.setAttribute("check", true);
                doSendPushNotify(result); //отправка оповещения

                //оповещение на странице с задачами
                const alertMessageDiv = `<div class="alert alert-info" role="alert">Задача ${result["title_task"]} успешно обновлена</div>`;
                document.querySelector('.edit-modal-opener').insertAdjacentHTML('beforebegin', alertMessageDiv);

                setTimeout(function() {

                    document.querySelector('.alert-info').remove();

                }, 3000);

            });
        
        }

    }

}

function doDeleteTask() {

    const divTask = document.querySelector('[check=true]');
    if (divTask) {

        const nTaskId = divTask.getAttribute("id");
        if (nTaskId) {
        
            fetch('/delete_task', {
                method: 'POST',
                headers: {
                    "accept" : "application/json",
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({"id_task": nTaskId})
            })
            .then(response => response.json())
            .then(result => {

                const tableTask = document.querySelector('.table-responsive');
                tableTask.innerHTML = result["html_tasks"];

                const table = document.querySelector('.table-borderless');
                let spanTimeParamByTask = ""; //переменная для временных параметров в задаче
                for (let iRows = 0; iRows < table.rows.length; iRows++) {

                    for (let iCell = 0; iCell < table.rows[iRows].cells.length; iCell++) {
                    
                        spanTimeParamByTask = table.rows[iRows].cells[iCell].getElementsByTagName('span');
                        for (let itemSpan = 0; itemSpan < spanTimeParamByTask.length; itemSpan++) {

                            if (spanTimeParamByTask[itemSpan].classList.contains('flask-moment')) {

                                spanTimeParamByTask[itemSpan].style = "";
                                spanTimeParamByTask[itemSpan].setAttribute("class", "");
                                spanTimeParamByTask[itemSpan].innerText = moment(spanTimeParamByTask[itemSpan].getAttribute("data-timestamp")).format(spanTimeParamByTask[itemSpan].getAttribute("data-format"));

                            }

                        }

                    }

                }
                spanTimeParamByTask = null;
                initClickDivTask(); //добавляем функцию на клик для блока с задачами

                //оповещение на странице с задачами
                const alertMessageDiv = `<div class="alert alert-info" role="alert">Задача ${result["title_task"]} успешно удалена</div>`;
                document.querySelector('.edit-modal-opener').insertAdjacentHTML('beforebegin', alertMessageDiv);

                setTimeout(function() {

                    document.querySelector('.alert-info').remove();

                }, 3000);

            });

        }

    }

}

function initClickDivTask() {

    $('[draggable=true]').click(function() {
        
        doShowHideBtn(this);
        $(this).css("border", "2px solid #21c1cc");
        $(this).css("box-shadow", "5px 5px 5px 5px #ababab");
        
        this.setAttribute("check", true); //заполняем атрибут, чтобы далее в функциях работать с задачей, которую кликнули
        const divCheckTasks = document.querySelectorAll('[check=true]');
        
        for (let iTask = 0; iTask < divCheckTasks.length; iTask++) {

            if (this["id"] !== divCheckTasks[iTask].getAttribute("id")) {

                $(divCheckTasks[iTask]).css("border", "");
                $(divCheckTasks[iTask]).css("box-shadow", "");
                divCheckTasks[iTask].setAttribute("check", false);

            }

        }

    });

}

function initMoveTask() {

    //скрытие кнопок при отображении задач
    $('.btn-warning').hide();
    $('.btn-success').hide();
    $('.btn-danger').hide();
    $('.btn-dark').hide();
    //скрытие кнопок в таблице
    $("#hide_done").show();
    $("#show_done").hide();

    initClickDivTask(); //добавляем функцию на клик для блока с задачами

    const btnMoveWork = document.querySelector(".btn-warning");
    btnMoveWork.addEventListener("click", (e) =>{

        e.preventDefault();
        updateTask('/next_status');

    });

    const btnMoveDone = document.querySelector(".btn-success");
    btnMoveDone.addEventListener("click", (e) =>{

        e.preventDefault();
        updateTask('/next_status');

    });

    const btnMoveReturn = document.querySelector(".btn-danger");
    btnMoveReturn.addEventListener("click", (e) =>{

        e.preventDefault();
        updateTask('/previous_status');

    });

    const btnMoveDelete = document.querySelector(".btn-dark");
    btnMoveDelete.addEventListener("click", (e) =>{

        e.preventDefault();
        doDeleteTask();

    });

}