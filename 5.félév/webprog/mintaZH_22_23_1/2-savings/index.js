const form = document.querySelector("form");
const divContainer = document.querySelector(".container");

const inputElements = document.querySelectorAll("input");
let totalConsumption = 0;


function calculateTotalConsumption(){
    totalConsumption = 0;
    for (const inputElement of inputElements){
        // 1.
        // const consumption = Number(inputElement.dataset.consumption); // ez is teljesen jó
        const consumption = Number(inputElement.getAttribute("data-consumption"));
        totalConsumption += consumption;
    }
    console.log(totalConsumption);
}


function updateChart(){
    for (const inputElement of inputElements){
        const maxConsumption = Number(inputElement.getAttribute("data-consumption"));

        // 2.
        const value = inputElement.value;
        const max = inputElement.getAttribute("max");
        const currentConsumption = value / max * maxConsumption;
        console.log(currentConsumption);

        // 3.
        const id = inputElement.id;
        const labelElement = document.querySelector(`label[for=${id}]`);
        labelElement.style.width = `${currentConsumption / totalConsumption * 100}%`;
    }
}

function onSliderChange(){
    updateChart();
}

form.addEventListener("input", onSliderChange);

calculateTotalConsumption();
updateChart();