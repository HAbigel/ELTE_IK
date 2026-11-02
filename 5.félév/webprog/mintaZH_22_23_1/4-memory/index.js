const inputCircleNumber = document.querySelector("#circle-number");
const buttonStart = document.querySelector("#start");
const divContainer = document.querySelector("#container");
const divOutput = document.querySelector("#output");

// Application state

let canGuess = false;
let solution = [];
let series = [];

// ========= Utility functions =========

function random(a, b) {
  return Math.floor(Math.random() * (b - a + 1)) + a;
}

function toggleHighlight(node) {
  node.classList.toggle("highlight")
  node.addEventListener("animationend", function (e) {
    node.classList.remove("highlight");
  }, {once: true});
}

// =====================================

// 1.
function updateCircleCount(){
  const circleCount = Number(inputCircleNumber.value);
  divContainer.innerHTML = "";
  for(let i = 0; i < circleCount; i += 1){
    divContainer.innerHTML += `<a class="circle"></a>`;
  }
}

inputCircleNumber.addEventListener("input", updateCircleCount);

// 2.
function startGame(){
  const circleCount = Number(inputCircleNumber.value);
  series = [];
  for(let i = 0; i < circleCount; i += 1){
    series.push(random(1, circleCount));
  }
  console.log(series);
  
  // 3.
  highlightFromSeries(0);
}

buttonStart.addEventListener("click", startGame)

// 3.
function highlightFromSeries(seriesIndex){
  const firstHighlightIndex = series[seriesIndex] - 1;
  const circleElements = document.querySelectorAll(".circle");
  toggleHighlight(circleElements[firstHighlightIndex]);

  // 4.
  if(seriesIndex < series.length-1){
    setTimeout(() => highlightFromSeries(seriesIndex + 1), 1000);
  }
}


