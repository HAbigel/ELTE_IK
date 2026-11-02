import { BOARD_SIZE } from "./params.js";
import { board, buyTower, money, moveEnemies } from "./state.js";
import { renderBoard, renderMoney } from "./render.js";

const boardElement = document.querySelector("#board");
const moneyElement = document.querySelector("#money");

export function onCellClicked(event){
    if(!event.target.closest("div.cell")) { 
        return ;
    }

    // const boardElement = event.target.closest("#board");
    // const moneyElement = document.querySelector("#money");

    const cellElement = event.target.closest("div.cell");
    if (cellElement.classList.contains("road")) {
        return;
    }

    const cellIndex = Array.from(boardElement.children).indexOf(cellElement);
    const y = Math.floor(cellIndex/ BOARD_SIZE);
    const x = cellIndex % BOARD_SIZE;

    buyTower(x, y);
    moneyElement.innerHTML = renderMoney(money);
    boardElement.innerHTML = renderBoard(board);
}

export function onTimerTick(){
    moveEnemies();
    boardElement.innerHTML = renderBoard(board); // itt honnan ismeri a board
}