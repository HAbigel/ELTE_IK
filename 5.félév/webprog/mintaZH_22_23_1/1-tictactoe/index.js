const task1 = document.querySelector('#task1');
const task2 = document.querySelector('#task2');
const task3 = document.querySelector('#task3');
const task4 = document.querySelector('#task4');

const game = [
  "XXOO",
  "O OX",
  "OOO ",
];

const solution1 = game.every((row) => row.length === game[0].length);
task1.innerHTML = solution1;

const solution2 = game[0].split("").every((character) => character === "X" || character === "O"); // stringen nincs every mávelet ezért elószür tümbbé alakytjuk
// game[0].split("")
// Array.from(game[0])
// [...game[0]]
task2.innerHTML = solution2;

const f = game.join("").split(""); // azert nem flat mert az tobbdimenzios tomb ez meg stringek tombje
const solX = f.filter((char) => char === "X").length; // f.count("X");
const solO = f.filter((char) => char === "O").length;
task3.innerHTML = `X / O = ${solX} / ${solO}`; //solX + " / " + solY;

const solution4 = game.findIndex((row) => row.includes("XXX") || row.includes("OOO"));
task4.innerHTML = solution4;