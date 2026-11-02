import { enemies } from "./state.js";

export function renderMoney(money){
    return money; //`🪙 ${money}`;
}

export function renderBoard(board){ // ha paraméterként kapja meg akk tiszta fv lesz és könnyen tesztelhető, míg ha imoportként akkor nem
    return `${board.map(renderRow).join("")}`;
}

function renderRow(row){ // nem mindent kell exportálni, ez pl belső fv
    return `${row.map(renderCell).join("")}`;
}

function renderCell(cell){
    const classes = ["cell"];
    if(cell.isRoad) {
        classes.push("road")
    }
    if(enemies.some((enemy) => enemy.x === cell.x && enemy.y === cell.y)){
        classes.push("enemy");
    }
    if(cell.isTower){
        classes.push("tower")
    }
    return `<div class="${classes.join(" ")}"></div>`;
    //működik de csúnya: return `<div class="cell${cell.isRoad ? " road" : ""}"></div>`;
}