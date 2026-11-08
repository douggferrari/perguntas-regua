// Réguas de resposta: cada pergunta vai de Não (0, à esquerda) a Sim (100, à
// direita). O campo só entra no formulário depois que a pessoa toca na régua,
// e o botão só libera com todas marcadas.
(() => {
  "use strict";

  const ARRASTE_MIN = 6; // px de deslize no dedo antes de virar arraste
  const PASSOS = { ArrowLeft: -5, ArrowDown: -5, ArrowRight: 5, ArrowUp: 5, PageDown: -10, PageUp: 10 };

  const form = document.getElementById("respostas");
  const botao = form.querySelector("button[type=submit]");
  const reguas = [...form.querySelectorAll(".regua-entrada")];

  function atualizarBotao() {
    const faltam = reguas.filter((r) => !r.closest(".questao").classList.contains("respondida")).length;
    botao.disabled = faltam > 0;
    botao.textContent =
      faltam === 0 ? "Enviar respostas" : faltam === 1 ? "Falta 1 régua" : `Faltam ${faltam} réguas`;
  }

  function marcar(regua, valor) {
    valor = Math.round(Math.min(100, Math.max(0, valor)));
    const questao = regua.closest(".questao");
    const campo = form.elements[regua.dataset.campo];
    campo.value = valor;
    campo.disabled = false;
    questao.classList.add("respondida");
    questao.querySelector(".valor").textContent = `${valor}%`;
    regua.style.setProperty("--v", valor);
    regua.setAttribute("aria-valuenow", valor);
    regua.setAttribute("aria-valuetext", `${valor}%`);
    atualizarBotao();
  }

  function valorEm(regua, x) {
    const t = regua.querySelector(".trilho").getBoundingClientRect();
    return ((x - t.left) / t.width) * 100;
  }

  for (const regua of reguas) {
    // No dedo, só marca num toque ou num deslize de lado: quem só está rolando
    // a página passa por cima da régua (o navegador cancela o ponteiro).
    let toque = null;

    regua.addEventListener("pointerdown", (e) => {
      if (e.button !== 0) return;
      toque = { id: e.pointerId, x: e.clientX, arrastando: e.pointerType === "mouse" };
      regua.setPointerCapture(e.pointerId);
      if (toque.arrastando) marcar(regua, valorEm(regua, e.clientX));
    });
    regua.addEventListener("pointermove", (e) => {
      if (!toque || e.pointerId !== toque.id) return;
      if (!toque.arrastando && Math.abs(e.clientX - toque.x) < ARRASTE_MIN) return;
      toque.arrastando = true;
      marcar(regua, valorEm(regua, e.clientX));
    });
    regua.addEventListener("pointerup", (e) => {
      if (!toque || e.pointerId !== toque.id) return;
      marcar(regua, valorEm(regua, e.clientX));
      toque = null;
    });
    regua.addEventListener("pointercancel", () => {
      toque = null;
    });
    regua.addEventListener("keydown", (e) => {
      const atual = Number(regua.getAttribute("aria-valuenow") ?? 50);
      let valor;
      if (e.key in PASSOS) valor = atual + PASSOS[e.key];
      else if (e.key === "Home") valor = 0;
      else if (e.key === "End") valor = 100;
      else return;
      e.preventDefault();
      marcar(regua, valor);
    });
  }

  form.addEventListener("submit", () => {
    botao.disabled = true; // duplo toque
  });
  // Voltar do "obrigado" pelo botão do celular restaura a página do cache:
  // recarrega para o servidor mostrar o que a pessoa já respondeu.
  addEventListener("pageshow", (e) => {
    if (e.persisted) location.reload();
  });

  atualizarBotao();
})();
