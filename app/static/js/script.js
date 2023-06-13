async function load_move_status() {
  const response = await fetch('http://127.0.0.1:5000/current_game');
  const is_your_move = await response.json();
  console.log(is_your_move)
}

setInterval(load_move_status, 2000);