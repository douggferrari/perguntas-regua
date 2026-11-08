// Réguas de resposta: cada pergunta é Não (à esquerda) ou Sim (à direita), sem
// meio-termo: o toque ou o arraste leva o marcador para o lado mais perto, e
// tocar nas palavras Não/Sim também vale. O campo só entra no formulário depois
// que a pessoa escolhe um lado, e o botão só libera com todas respondidas.
(() => {
  "use strict";

  const ARRASTE_MIN = 6; // px de deslize no dedo antes de virar arraste
  const TECLAS = { ArrowLeft: false, ArrowDown: false, Home: false, ArrowRight: true, ArrowUp: true, End: true };

  const form = document.getElementById("respostas");
  const botao = form.querySelector("button[type=submit]");
  const reguas = [...form.querySelectorAll(".regua-entrada")];

  function atualizarBotao() {
    const faltam = reguas.filter((r) => !r.closest(".questao").classList.contains("respondida")).length;
    botao.disabled = faltam > 0;
    botao.textContent =
      faltam === 0 ? "Enviar respostas" : faltam === 1 ? "Falta 1 pergunta" : `Faltam ${faltam} perguntas`;
  }

  function marcar(regua, sim) {
    const valor = sim ? 100 : 0;
    const questao = regua.closest(".questao");
    const campo = form.elements[regua.dataset.campo];
    campo.value = valor;
    campo.disabled = false;
    questao.classList.add("respondida");
    questao.dataset.resposta = sim ? "sim" : "nao";
    questao.querySelector(".valor").textContent = sim ? "Sim" : "Não";
    regua.style.setProperty("--v", valor);
    regua.setAttribute("aria-valuenow", valor);
    regua.setAttribute("aria-valuetext", sim ? "Sim" : "Não");
    atualizarBotao();
  }

  function ladoSim(regua, x) {
    const t = regua.querySelector(".trilho").getBoundingClientRect();
    return x >= t.left + t.width / 2;
  }

  for (const regua of reguas) {
    // No dedo, só marca num toque ou num deslize de lado: quem só está rolando
    // a página passa por cima da régua (o navegador cancela o ponteiro).
    let toque = null;

    regua.addEventListener("pointerdown", (e) => {
      if (e.button !== 0) return;
      toque = { id: e.pointerId, x: e.clientX, arrastando: e.pointerType === "mouse" };
      regua.setPointerCapture(e.pointerId);
      if (toque.arrastando) marcar(regua, ladoSim(regua, e.clientX));
    });
    regua.addEventListener("pointermove", (e) => {
      if (!toque || e.pointerId !== toque.id) return;
      if (!toque.arrastando && Math.abs(e.clientX - toque.x) < ARRASTE_MIN) return;
      toque.arrastando = true;
      marcar(regua, ladoSim(regua, e.clientX));
    });
    regua.addEventListener("pointerup", (e) => {
      if (!toque || e.pointerId !== toque.id) return;
      marcar(regua, ladoSim(regua, e.clientX));
      toque = null;
    });
    regua.addEventListener("pointercancel", () => {
      toque = null;
    });
    regua.addEventListener("keydown", (e) => {
      if (!(e.key in TECLAS)) return;
      e.preventDefault();
      marcar(regua, TECLAS[e.key]);
    });

    const questao = regua.closest(".questao");
    questao.querySelector(".extremos .nao").addEventListener("click", () => marcar(regua, false));
    questao.querySelector(".extremos .sim").addEventListener("click", () => marcar(regua, true));
  }

  form.addEventListener("submit", () => {
    botao.disabled = true; // duplo toque
  });
  // Voltar do resultado pelo botão do celular restaura esta página do cache:
  // recarrega para o servidor mostrar o que a pessoa já respondeu.
  addEventListener("pageshow", (e) => {
    if (e.persisted) location.reload();
  });

  atualizarBotao();
})();
