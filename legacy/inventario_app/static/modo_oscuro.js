document.addEventListener("DOMContentLoaded", () => {
  const btn = document.createElement("button");
  btn.textContent = "🌓 Modo";
  btn.style.position = "fixed";
  btn.style.bottom = "15px";
  btn.style.right = "15px";
  btn.style.zIndex = "1000";
  btn.style.padding = "10px 15px";
  btn.style.borderRadius = "8px";
  btn.style.backgroundColor = "#3498db";
  btn.style.color = "white";
  btn.style.border = "none";
  btn.style.cursor = "pointer";

  btn.onclick = () => {
    document.body.classList.toggle("dark-mode");
    const modo = document.body.classList.contains("dark-mode") ? "oscuro" : "claro";
    localStorage.setItem("modo-tema", modo);
  };

  document.body.appendChild(btn);

  // Restaurar preferencia
  if (localStorage.getItem("modo-tema") === "oscuro") {
    document.body.classList.add("dark-mode");
  }
});
