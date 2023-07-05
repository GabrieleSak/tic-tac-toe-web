async function load_move_status() {
  const response = await fetch('http://127.0.0.1:5000/current_game');
  const is_your_move = await response.json();
  return is_your_move["your_move"];
}

function updateDiv()
{
    $("#board").load(" #board > *");
    $("#player").load(" #player > *");
}

async function reload_page() {
    let is_your_move = await load_move_status();
    console.log(is_your_move);
    if (is_your_move === true) {
        updateDiv();
    }
}


setInterval(reload_page, 2000);

