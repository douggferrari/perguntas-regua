// Painel ao vivo: consulta /api/resultado a cada poucos segundos e leva o
// marcador de cada régua até a média das respostas (0% = Não, 100% = Sim).
// O deslize e a troca de cor ficam por conta das transições do CSS.
(() => {
  "use strict";

  const INTERVALO_MS = 3000;

  const painel = document.getElementById("painel");
  const modelo = document.getElementById("modelo-linha");
  const elTotal = document.getElementById("total");
  const qr = document.getElementById("qr");
  let linhas = new Map(); // id da pergunta -> <section>
  let ids = "";
  let recebido = "";

  const params = new URLSearchParams(location.search);
  const tema = params.get("tema");
  if (tema === "escuro") document.documentElement.dataset.theme = "dark";
  if (tema === "claro") document.documentElement.dataset.theme = "light";

  // Quem acabou de enviar cai aqui com ?enviado=1: avisa e tira o parâmetro da
  // URL, para recarregar a página não repetir o aviso.
  if (params.has("enviado")) {
    const aviso = document.getElementById("enviado");
    aviso.hidden = false;
    aviso.addEventListener("transitionend", () => (aviso.hidden = true));
    setTimeout(() => aviso.classList.add("saindo"), 6000);
    params.delete("enviado");
    const resto = params.toString();
    history.replaceState(null, "", location.pathname + (resto ? `?${resto}` : ""));
  }

  // Recria as linhas só quando o conjunto de perguntas muda no /admin.
  function montar(perguntas) {
    linhas = new Map();
    painel.replaceChildren(
      ...perguntas.map((p, i) => {
        const linha = modelo.content.firstElementChild.cloneNode(true);
        linha.querySelector(".linha-num").textContent = i + 1;
        linhas.set(p.id, linha);
        return linha;
      }),
    );
  }

  function aplicar(d) {
    const novos = d.perguntas.map((p) => p.id).join(",");
    if (novos !== ids) {
      ids = novos;
      montar(d.perguntas);
    }
    elTotal.textContent = d.total === 1 ? "1 resposta" : `${d.total} respostas`;
    for (const p of d.perguntas) {
      const linha = linhas.get(p.id);
      const temDados = p.media !== null;
      linha.querySelector(".linha-texto").textContent = p.texto;
      linha.classList.toggle("sem-dados", !temDados);
      // Sem respostas o marcador espera escondido no meio e, na primeira, desliza de lá.
      linha.querySelector(".regua").style.setProperty("--v", temDados ? p.media : 50);
      linha.querySelector(".regua-valor").textContent = temDados ? `${Math.round(p.media)}%` : "";
    }
  }

  let espera = null;
  let buscando = false;

  async function atualizar() {
    if (buscando) return; // a busca em andamento já agenda a próxima
    buscando = true;
    clearTimeout(espera);
    try {
      const resp = await fetch("/api/resultado", { cache: "no-store" });
      if (resp.ok) {
        const texto = await resp.text();
        if (texto !== recebido) {
          recebido = texto;
          aplicar(JSON.parse(texto));
        }
      }
    } catch {
      // rede caiu: tenta de novo no próximo ciclo
    }
    buscando = false;
    espera = setTimeout(atualizar, INTERVALO_MS);
  }

  // Aba escondida (celular bloqueado, outra aba na frente) tem o timer congelado
  // pelo navegador: ao reaparecer, busca na hora em vez de mostrar número velho.
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) atualizar();
  });
  addEventListener("pageshow", (e) => {
    if (e.persisted) atualizar();
  });

  qr.addEventListener("click", () => qr.classList.toggle("ampliado"));

  atualizar();
})();
