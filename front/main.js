eel.expose(updateData);
eel.expose(updateTableData);
eel.expose(alert_emergency);
window.onload = function() {
    eel.start_data_stream();
    populateSubstationSelector();
};
fetch_saved_devices();
curent_device_list = [];
selected_saved_device = null;
last_data = [];

let selected_substation = ''

let charts = [];
let lables = [];

update_data = true;

num_readings = 20;

starting_datetime = '';
ending_datetime = '';

const fixedMinX = 0; 
const fixedMaxX = 20; 
const fixedMinY = 0; 
const fixedMaxY = 40; 

loadChart();

var checkbox = document.querySelector("input[name=updater_checkbox]");
checkbox.addEventListener('change', function() {
  if (this.checked) {
    update_data = true;
  } else {
    update_data = false;
  }
});

numInput = document.getElementById('num-readings')
numInput.addEventListener('change', function(e) {
    if (e.target.value == '') {
        e.target.value = 1
    }
    // alert("Повышенная температура (121°C) у датчика №103");
    if (e.target.value > 0 && e.target.value < 1000){
        num_readings = parseInt(e.target.value);
        addData();
    }
})

start_data = document.getElementById('reading-time-start')
start_data.addEventListener('change', function(e) {
    starting_datetime = e.target.value;
})

end_data = document.getElementById('reading-time-end')
end_data.addEventListener('change', function(e) {
    ending_datetime = e.target.value;
})

function updateData(data) {
    if (update_data) {
        curent_device_list = data;
        makeUL(data);
        addData();
        updateSubstationSelector();
        filterAvailableDevices();
    }
}

function updateTableData(newData) {
    const table = document.getElementById("data-table");
    const rows = table.querySelectorAll("tbody tr");

    for (let i = 0; i < rows.length; i++) {
        const cells = rows[i].querySelectorAll("td");

        for (let j = 1; j < cells.length; j++) {
            let value = newData[i][j - 1];
            let precision = i === 0 ? 2 : 4; // первая строка — 2 знака, остальные — 4
            cells[j].textContent = Number(value).toFixed(precision);
        }
    }
}

function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-buttons div').forEach(el => el.classList.remove('active'));
    document.getElementById(tabId).classList.add('active');
    document.getElementById(`tab-btn${tabId.charAt(3)}`).classList.add('active');
}

async function addData() {
    if(selected_saved_device == null) return;
    if(!update_data && starting_datetime != '' && ending_datetime != ''){
        full_data = await eel.fetch_data_exact(selected_saved_device, starting_datetime, ending_datetime)();
    }
    else {
        full_data = await eel.fetch_data(selected_saved_device, num_readings)();
    }
    // console.log(full_data);
    last_data = []
    for(t_1 = 0; t_1 < charts.length - 1; t_1++){
        data = [];
        for(t_2 = 0; t_2 < full_data.length; t_2++){
            // console.log(full_data[t_2][t_1]);
            // data.push([full_data[t_2][t_1], t_2]);
            datetime = full_data[t_2][full_data[t_2].length - 1];
            datetime = datetime.split(' ');
            datetime = datetime[datetime.length - 1];
            datetime = datetime.split('.')[0];
            data.push([datetime, full_data[t_2][t_1]]);
        }
        // charts[t_1].data.labels = labels;
        // charts[t_1].data.datasets[1].data = Array(20).fill().map((x,i)=>i);
        charts[t_1].data.datasets[0].data = data;
        charts[t_1].options.scales.x.min = data[0][0];
        charts[t_1].update();
        last_data.push(data)
    }
    console.log(last_data);
    
    data = [];
    for(t = 0; t < full_data.length; t++){
        data.push([full_data[t][0],full_data[t][1]*full_data[t][2]]);
    }
    charts[charts.length-1].type = 'scatter';
    charts[charts.length-1].data.datasets[0].data = data;
    charts[charts.length-1].options.scales.y.max = 500;
    charts[charts.length-1].options.scales.x.min = 0;
    charts[charts.length-1].options.scales.x.max = 50;
    charts[charts.length-1].update();
}

async function loadChart() {
    data = [];
    ["chart1", "chart2", "chart3", "chart4", "chart5"].forEach((chartId, index) => {
        let ctx = document.getElementById(chartId).getContext('2d');
        lable_list = ["T, °C", "I, А", "U, кВ", "Уровень заряда, %", "123"]
        max_val_list = [60, 40, 30, 100, 50]
        type_list = ['line','line','line','line','scatter']
        new_chart = new Chart(ctx, {
            type: type_list[index], // Тип графика (линейный)
            data: {
                datasets: [{
                    label: 'Показатель датчика',
                    data: data,
                    borderColor: 'rgba(75, 192, 192, 1)',
                    fill: false,
                    backgroundColor: 'rgba(75, 192, 192, 1)', // This fills the points
                    pointBackgroundColor: 'rgba(75, 192, 192, 1)', // Explicit point fill color
                }]
            },
            options: {
                plugins: {
                    backgroundColor: 'rgb(255, 255, 255)',
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Время'
                        }
                    },
                    y: {
                        min: fixedMinY,
                        max: max_val_list[index],
                        title: {
                            display: true,
                            text: lable_list[index]
                        }
                    }
                },
                animation: false,
                responsive: true,
                maintainAspectRatio: false,
            },
            plugins: [{
                id: 'customCanvasBackgroundColor',
                beforeDraw: (chart) => {
                    const ctx = chart.canvas.getContext('2d');
                    ctx.save();
                    ctx.globalCompositeOperation = 'destination-over';
                    ctx.fillStyle = 'rgb(255, 255, 255)';
                    ctx.fillRect(0, 0, chart.width, chart.height);
                    ctx.restore();
                }
            }]
        });
        // console.log(new_chart);
        charts.push(new_chart);
    });
}

async function populateSubstationSelector() {
    const substations = await eel.fetch_substations()();
    const selector = document.getElementById('substation-selector');
    
    selector.innerHTML = '<option value="">Все подстанции</option>';
    
    substations.forEach(substation => {
        const option = document.createElement('option');
        option.value = substation;
        option.textContent = substation;
        selector.appendChild(option);
    });
    
    selector.addEventListener('change', function() {
        selected_substation = this.value;
        filterAvailableDevices();
    });
}

async function updateSubstationSelector() {
    const substations = await eel.fetch_substations()();
    const selector = document.getElementById('substation-selector');
    const existingOptions = Array.from(selector.options)
        .slice(1) // Пропускаем первый элемент
        .map(option => option.value);
    
    // Фильтруем новые подстанции, которых ещё нет в селекторе
    const newSubstations = substations.filter(
        substation => !existingOptions.includes(substation)
    );
    
    // Добавляем только новые подстанции
    newSubstations.forEach(substation => {
        const option = document.createElement('option');
        option.value = substation;
        option.textContent = substation;
        selector.appendChild(option);
    });
    
    // Если селектор был пуст (только "Все подстанции"), добавляем обработчик
    if (existingOptions.length === 0 && selector.options.length > 1) {
        selector.addEventListener('change', function() {
            selected_substation = this.value;
            filterAvailableDevices();
        });
    }
}

async function filterAvailableDevices() {
    const searchText = document.getElementById("search-available").value.toLowerCase();
    const substationFilter = selected_substation;
    
    const availableList = document.getElementById("device-list");
    const availableItems = availableList.getElementsByTagName("li");
    
    for (let item of availableItems) {
        const deviceName = item.innerText.toLowerCase();
        const deviceSubstation = item.dataset.substation_value;
        
        const matchesSearch = deviceName.includes(searchText);
        const matchesSubstation = substationFilter === '' || deviceSubstation.includes(substationFilter);
        
        if (matchesSearch && matchesSubstation) {
            item.style.display = "block";
        } else {
            item.style.display = "none";
        }
    }
    
    const savedList = document.getElementById("saved-device-list");
    const savedOptions = savedList.options;
    
    for (let i = 0; i < savedOptions.length; i++) {
        const option = savedOptions[i];
        const deviceName = option.innerText();
        const deviceSubstation = await eel.get_device_substation(option.innerText)();
        const substationMatch = substationFilter === '' || 
                            (deviceSubstation && deviceSubstation.includes(substationFilter));
        
        if (deviceName.includes(searchText) && substationMatch) {
            option.style.display = "block";
        } else {
            option.style.display = "none";
        }
    }
}

// function filterAvailableDevices() {
//     const searchText = document.getElementById("search-available").value.toLowerCase();
//     const availableList = document.getElementById("device-list");
//     const availableItems = availableList.getElementsByTagName("li");
//     for (let item of availableItems) {
//         const deviceName = item.innerText.toLowerCase();
//         if (deviceName.includes(searchText)) {
//             item.style.display = "block";
//         } else {
//             item.style.display = "none";
//         }
//     }
//     const savedList = document.getElementById("saved-device-list");
//     const savedOptions = savedList.options;
//     for (let i = 0; i < savedOptions.length; i++) {
//         const option = savedOptions[i];
//         const deviceName = option.innerText.toLowerCase();
//         if (deviceName.includes(searchText)) {
//             option.style.display = "block";
//         } else {
//             option.style.display = "none";
//         }
//     }
// }

function handleChange() {
    var letter = document.getElementById("saved-device-list");
    selected_saved_device = letter.options[letter.selectedIndex].innerText;
    addData();
}
async function delete_device_on_click() {
    if(selected_saved_device == null) return;
    await eel.delete_device(selected_saved_device)();
    var letter = document.getElementById("saved-device-list");
    letter.options[letter.selectedIndex].remove();
}

async function fetch_saved_devices(){
    device_list = await eel.fetch_saved_devices()();
    // console.log(device_list);
    let list = document.getElementById('saved-device-list');
    point: for (i = 0; i < device_list.length; i++) {
        for(i2 = 0; i2 < list.length; i2++)
        {
            if(device_list[i][1] == list[i2].innerText)
            {
                continue point;
            }
        }
        var item = document.createElement('option');
        item.value = device_list[i][2];
        item.innerText  = device_list[i][1];
        list.appendChild(item);
    }
}

function makeUL(data) {
    if(data.length){
        let list = document.getElementById('device-list');
        list.innerHTML = '';
        for (i = 0; i < data.length; i++) {
            var item = document.createElement('li');
            item.innerText = data[i].device_name;
            item.dataset.address_value = data[i].device_address;
            item.dataset.name_value = data[i].device_name;
            item.dataset.substation_value = data[i].substation;
            item.addEventListener('dblclick', function() {
                data_to_send = [this.dataset.name_value, this.dataset.address_value, this.dataset.substation_value];
                eel.add_device_to_db(data_to_send)();
                console.log(data_to_send);
                fetch_saved_devices();
                });
            list.appendChild(item);
        }
    }
    else{
        console.log('no devices detected');
    }
}

// function exportData(data, csvFilename = 'data.csv', xlsxFilename = 'data.xlsx') {
//     const worksheetData = [['Time', 'Value'], ...data];
//     const worksheet = XLSX.utils.aoa_to_sheet(worksheetData);
//     const workbook = XLSX.utils.book_new();
//     XLSX.utils.book_append_sheet(workbook, worksheet, 'Sheet1');
//     XLSX.writeFile(workbook, xlsxFilename);
//     const csv = worksheetData.map(row => row.join(',')).join('\n');
//     fs.writeFileSync(csvFilename, csv);
// }

function exportDataToExcelAndCSV() {
    const wb = XLSX.utils.book_new();

    last_data.forEach((data, index) => {
        // Преобразуем данные в формат [ [время, значение], ... ]
        const sheetData = [['Time', 'Value'], ...data];
        const ws = XLSX.utils.aoa_to_sheet(sheetData);
        XLSX.utils.book_append_sheet(wb, ws, `Dataset ${index + 1}`);
    });

    const wbout = XLSX.write(wb, { bookType: 'xlsx', type: 'array' });
    saveAs(new Blob([wbout], { type: 'application/octet-stream' }), 'data_export.xlsx');
}

function alert_emergency(device_name, error_msg){
    text = 'Датчик: ' + '. ' + error_msg;
    alert(text);
}