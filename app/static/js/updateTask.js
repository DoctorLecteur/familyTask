"use strict";
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

                const oldTable = document.querySelector('.table-borderless');
                let bIsViewDone = true;
                for (let iRow = 0; iRow < oldTable.rows.length; iRow++) {

                    if (oldTable.rows[iRow].cells[oldTable.rows[0].cells.length - 1].style.display === 'none') {
                        
                        bIsViewDone = false;
                        break;

                    }

                }

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
                initDragAndDropTask(); //добавляем возможность перемещения задачи с помощью мыши
                //показ последнего столбца таблицы
                initBtnHideShowDoneColumn();
                if (bIsViewDone === true) {

                    doShowDoneColumn();
                    
                } else {

                    doHideDoneColumn();

                }
                bIsViewDone = null;

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

                const oldTable = document.querySelector('.table-borderless');
                let bIsViewDone = true;
                for (let iRow = 0; iRow < oldTable.rows.length; iRow++) {

                    if (oldTable.rows[iRow].cells[oldTable.rows[0].cells.length - 1].style.display === 'none') {
                        
                        bIsViewDone = false;
                        break;

                    }

                }

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
                initDragAndDropTask(); //добавляем возможность перемещения задачи с помощью мыши
                //показ последнего столбца таблицы
                initBtnHideShowDoneColumn();
                if (bIsViewDone === true) {

                    doShowDoneColumn();
                    
                } else {

                    doHideDoneColumn();

                }
                bIsViewDone = null;

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

function doDragStart(evt) {

    evt.target.classList.add('selected');

}

function doDragOver(evt, divCurrentTask, taskTable) {

    const activeTask = taskTable.querySelector('.selected');
    //возращает блок с задачей назад, если блок перенесли за таблицу
    const bIsMoveable = activeTask !== divCurrentTask && divCurrentTask.classList.contains('div-hover');
    if (!bIsMoveable) {
        return;
    }

}

function doDragEnd(evt, divCurrentTask) {

    const numIdTaskMove = evt.target.getAttribute("id"); //id задачи, которую двигают
    if (numIdTaskMove) {

        evt.target.classList.remove('selected');
        let cellIndex = null; //id столбца со следующем статусом для задачи
        if (divCurrentTask.parentNode.cellIndex !== undefined) {

            cellIndex = divCurrentTask.parentNode.cellIndex;

        } else {

            cellIndex = divCurrentTask.cellIndex;

        }

        let cellIndexMove = evt.target.parentNode.cellIndex; //id столбца с текущем статусом для задачи
        let sUrl = null; //переменная для перемещения задачи по статусам
        if (cellIndexMove !== cellIndex && cellIndexMove !== undefined && cellIndex !== undefined) {

            if (cellIndexMove < cellIndex) {

                sUrl = '/next_status';

            } else {

                sUrl = '/previous_status';

            }

        }

        if (sUrl) {

            updateTask(sUrl);

        }

    } else {

        evt.target.classList.remove('selected');

    }

}

function initDragAndDropTask() {

    //действие при перетаскивании блока с задачей
    const taskTable = document.querySelector('.table-borderless');
    if (taskTable !== null) {
    
        taskTable.addEventListener('dragstart', (evt) => {

            doDragStart(evt);

        });

        let currentTask = null;//переменная для задачи, над которой перетаскивает другую задачу
        taskTable.addEventListener('dragover', (evt) => {

            evt.preventDefault();
            currentTask = evt.target;
            doDragOver(evt, currentTask, taskTable);

        });
        //обновление статуса по задаче, когда её отпустили после перемещения
        taskTable.addEventListener('dragend', (evt) => {

            doDragEnd(evt, currentTask);

        });
    
    }

}

function doHideDoneColumn() {

    const taskTable = document.querySelector('.table-borderless');
    for (let iRow = 0; iRow < taskTable.rows.length; iRow++) {

        taskTable.rows[iRow].cells[taskTable.rows[0].cells.length - 1].style.display = 'none';

    }
    $("#show_done").show();

}

function doShowDoneColumn() {

    const taskTable = document.querySelector('.table-borderless');
    for (let iRow = 0; iRow < taskTable.rows.length; iRow++) {

        taskTable.rows[iRow].cells[taskTable.rows[0].cells.length - 1].style.display = 'block';

    }
    $("#hide_done").show();
    $("#show_done").hide();

}

function initBtnHideShowDoneColumn() {

    const btnHideDone = document.querySelector(".close"); //скрытие столбца "Готово" в таблице
    btnHideDone.addEventListener("click", (e) =>{

        e.preventDefault();
        doHideDoneColumn();

    });

    const btnShowDone = document.querySelector(".btn-hide-show"); //показ столбца "Готово" в таблице
    btnShowDone.addEventListener("click", (e) =>{

        e.preventDefault();
        doShowDoneColumn();

    });

}

function initMoveTask() {

    //скрытие кнопок при отображении задач
    $('.btn-warning').hide();
    $('.btn-success').hide();
    $('.btn-danger').hide();
    $('.btn-dark').hide();
    $("#hide_done").show();
    $("#show_done").hide();
    

    initClickDivTask(); //добавляем функцию на клик для блока с задачами

    const btnMoveWork = document.querySelector(".btn-warning"); //перевод задачи В работу
    btnMoveWork.addEventListener("click", (e) =>{

        e.preventDefault();
        updateTask('/next_status');

    });

    const btnMoveDone = document.querySelector(".btn-success"); //перевод задачи в Готово
    btnMoveDone.addEventListener("click", (e) =>{

        e.preventDefault();
        updateTask('/next_status');

    });

    const btnMoveReturn = document.querySelector(".btn-danger"); //Возрат задачи на предыдущий статус
    btnMoveReturn.addEventListener("click", (e) =>{

        e.preventDefault();
        updateTask('/previous_status');

    });

    const btnMoveDelete = document.querySelector(".btn-dark"); //удаление задачи
    btnMoveDelete.addEventListener("click", (e) =>{

        e.preventDefault();
        doDeleteTask();

    });

    initDragAndDropTask(); //добавляем возможность перемещения задачи с помощью мыши
    initBtnHideShowDoneColumn(); //скрытие и показ последнего столбца

}