import { board, money, setup } from "./state.js"; // figyelni kell hogy a .js ott legyen a végén
import { renderBoard, renderMoney } from "./render.js";
import { BOARD_SIZE, PATH } from "./params.js";
import { onCellClicked, onTimerTick } from "./events.js";

const boardElement = document.querySelector("#board");
const moneyElement = document.querySelector("#money");


boardElement.addEventListener("click", onCellClicked);
setInterval(onTimerTick, 1000);

setup(BOARD_SIZE, PATH);

boardElement.innerHTML = renderBoard(board);
moneyElement.innerHTML = renderMoney(money);
