"""simulador reversível de bennett com 3 fitas."""

from __future__ import annotations

import time
from typing import Any, Callable

from conversor import converter_para_quadruplas
from fita import Fita
from modelos import MTDefinition, Quintupla

LIMITE_PASSOS = 100_000


class SimuladorReversivel:
    """simulador de máquina de turing reversível de bennett com 3 fitas.

    fita 1 (trabalho):   executa a computação
    fita 2 (histórico):  grava índice da quíntupla executada em cada passo
    fita 3 (saída):      recebe cópia do resultado
    """

    def __init__(
        self,
        mt: MTDefinition,
        callback: Callable[[str, Any], None] | None = None,
        controlador: Any = None,
    ):
        self._mt = mt
        self._estado_atual = mt.estado_inicial
        self._estado_aceitacao = mt.estado_aceitacao
        self._entrada_original = mt.entrada

        self._callback = callback
        self._controlador = controlador

        # fitas
        self._fita_trabalho = Fita(mt.entrada)
        self._fita_historico = Fita()
        self._fita_saida = Fita()

        # converter quíntuplas em quádruplas
        max_estado = max(mt.estados)

        self._quadruplas, self._quadruplas_inversas, _ = (
            converter_para_quadruplas(
                mt.transicoes,
                max_estado
            )
        )

        # tabela de lookup:
        # (estado, símbolo) -> quíntupla original
        self._tabela: dict[tuple[int, str], Quintupla] = {
            (q.estado_atual, q.simbolo_lido): q
            for q in mt.transicoes
        }

        # contadores
        self._passos_estagio1 = 0
        self._passos_estagio2 = 0
        self._passos_estagio3 = 0
        self._historico_tamanho = 0

    # ============================================================
    # COMUNICAÇÃO COM A INTERFACE
    # ============================================================

    def _emitir(
        self,
        tipo: str,
        dados: Any = None
    ) -> None:
        """envia evento para a interface gráfica."""
        if self._callback is not None:
            self._callback(
                tipo,
                dados
            )

    def _snapshot_fita(
        self,
        fita: Fita
    ) -> dict[str, Any]:
        """faz uma cópia do estado atual de uma fita."""
        return {
            "celulas": dict(fita.celulas),
            "posicao": fita.posicao,
            "branco": fita.branco,
        }

    def _snapshot_fitas(
        self
    ) -> dict[str, dict[str, Any]]:
        """faz uma cópia das três fitas."""
        return {
            "fita1": self._snapshot_fita(
                self._fita_trabalho
            ),
            "fita2": self._snapshot_fita(
                self._fita_historico
            ),
            "fita3": self._snapshot_fita(
                self._fita_saida
            ),
        }

    def _emitir_atualizacao(
        self,
        estagio: str,
        passo: int,
        transicao: dict[str, Any] | None = None,
    ) -> None:
        """envia estado, fitas e transição para a interface."""

        self._emitir(
            "atualizacao",
            {
                "estado": self._estado_atual,
                "passo": passo,
                "estagio": estagio,
                "transicao": transicao,
                "fitas": self._snapshot_fitas(),
            }
        )

    def _aguardar_passo(self) -> bool:
        """aguarda o próximo passo quando estiver no modo manual."""

        if self._controlador is None:
            return True

        return self._controlador.aguardar_passo()

    def _passo_concluido(self) -> None:
        """informa à interface que o passo terminou."""

        if self._controlador is not None:
            self._controlador.passo_concluido()

    # ============================================================
    # EXECUÇÃO
    # ============================================================

    def executar(self) -> None:
        """executa os três estágios completos."""

        self._imprimir_cabecalho()

        self._emitir_atualizacao(
            "Preparação",
            0,
            None
        )

        aceita = self._estagio_computacao()

        self._estagio_copia()

        self._estagio_retorno()

        self._imprimir_resultado(
            aceita
        )

        self._emitir(
            "final",
            {
                "aceita": aceita,
                "estado": self._estado_atual,
                "fitas": self._snapshot_fitas(),
            }
        )

    # ============================================================
    # ESTÁGIO 1 — COMPUTAÇÃO
    # ============================================================

    def _estagio_computacao(self) -> bool:
        """emula o programa original na fita 1."""

        print("\n" + "=" * 60)
        print("  ESTÁGIO 1 — COMPUTAÇÃO (IDA)")
        print("=" * 60)

        passos = 0
        historico_pos = 0

        while (
            self._estado_atual
            != self._estado_aceitacao
        ):
            simbolo = self._fita_trabalho.ler()

            chave = (
                self._estado_atual,
                simbolo
            )

            if chave not in self._tabela:
                print(
                    f"\n  ✗ Sem transição para "
                    f"({self._estado_atual}, {simbolo}) — MT parou."
                )

                self._passos_estagio1 = passos

                self._emitir(
                    "status",
                    f"Sem transição para "
                    f"({self._estado_atual}, {simbolo})"
                )

                return False

            q = self._tabela[chave]

            # No passo a passo, aguarda o clique.
            if not self._aguardar_passo():
                self._passos_estagio1 = passos
                return False

            # Mantém o print original.
            self._imprimir_passo_ida(
                passos,
                q,
                simbolo
            )

            # ----------------------------------------------------
            # EXECUTA A QUÍNTUPLA ORIGINAL
            # ----------------------------------------------------

            self._fita_trabalho.escrever(
                q.simbolo_escrito
            )

            self._fita_trabalho.mover(
                q.direcao
            )

            self._estado_atual = (
                q.proximo_estado
            )

            # ----------------------------------------------------
            # GRAVA HISTÓRICO
            # ----------------------------------------------------

            self._fita_historico.posicao = (
                historico_pos
            )

            self._fita_historico.escrever(
                str(q.indice)
            )

            historico_pos += 1
            passos += 1

            # ----------------------------------------------------
            # ATUALIZA GUI
            # ----------------------------------------------------

            self._emitir_atualizacao(
                "Estágio 1 — Computação (Ida)",
                passos,
                {
                    "estado": q.estado_atual,
                    "simbolo_lido": simbolo,
                    "simbolo_escrito": q.simbolo_escrito,
                    "direcao": q.direcao,
                    "proximo_estado": q.proximo_estado,
                    "indice": q.indice,
                }
            )

            self._passo_concluido()

            if passos >= LIMITE_PASSOS:
                print(
                    f"\n  ⚠ Limite de {LIMITE_PASSOS} "
                    f"passos atingido — abortando."
                )

                self._passos_estagio1 = passos

                self._emitir(
                    "status",
                    f"Limite de {LIMITE_PASSOS} passos atingido."
                )

                return False

        if passos >= 50:
            print(
                f"  ... ({passos - 50} passos omitidos)"
            )

        print(
            f"\n  ✓ Estado de aceitação "
            f"({self._estado_aceitacao}) "
            f"atingido em {passos} passos."
        )

        print(
            f"  Fita 1 (resultado): "
            f"{self._fita_trabalho}"
        )

        print(
            f"  Fita 2 (histórico): "
            f"{self._fita_historico.conteudo_str()}"
        )

        self._passos_estagio1 = passos
        self._historico_tamanho = historico_pos

        self._emitir(
            "status",
            "Estado de aceitação atingido — iniciando cópia."
        )

        return True

    def _imprimir_passo_ida(
        self,
        passo: int,
        q: Quintupla,
        simbolo: str
    ) -> None:
        """imprime um passo da ida."""

        if passo >= 50:
            return

        print(
            f"  Passo {passo + 1:>4}: "
            f"Estado={q.estado_atual}, "
            f"Lê='{simbolo}' → "
            f"Escreve='{q.simbolo_escrito}', "
            f"Move={q.direcao}, "
            f"Estado'={q.proximo_estado}"
        )

        print(
            f"             Fita 1: "
            f"{self._fita_trabalho}"
        )

    # ============================================================
    # ESTÁGIO 2 — CÓPIA
    # ============================================================

    def _estagio_copia(self) -> None:
        """copia a fita 1 para a fita 3."""

        print("\n" + "=" * 60)
        print("  ESTÁGIO 2 — CÓPIA")
        print("=" * 60)

        pos_salva = (
            self._fita_trabalho.posicao
        )

        if self._fita_trabalho.celulas:
            pos_min = min(
                self._fita_trabalho.celulas.keys()
            )

            pos_max = max(
                self._fita_trabalho.celulas.keys()
            )
        else:
            pos_min = 0
            pos_max = 0

        passos = 0
        saida_pos = 0

        for i in range(
            pos_min,
            pos_max + 1
        ):
            simbolo = (
                self._fita_trabalho.celulas.get(
                    i,
                    self._fita_trabalho.branco
                )
            )

            if simbolo != self._fita_trabalho.branco:

                if not self._aguardar_passo():
                    return

                self._fita_saida.posicao = (
                    saida_pos
                )

                self._fita_saida.escrever(
                    simbolo
                )

                saida_pos += 1
                passos += 1

                self._emitir_atualizacao(
                    "Estágio 2 — Cópia",
                    passos,
                    {
                        "posicao": i,
                        "simbolo_lido": simbolo,
                        "simbolo_escrito": simbolo,
                    }
                )

                self._passo_concluido()

        self._fita_trabalho.posicao = (
            pos_salva
        )

        self._fita_saida.posicao = 0

        print(
            f"  Copiados {passos} símbolos "
            f"para a Fita 3."
        )

        print(
            f"  Fita 3 (saída): "
            f"{self._fita_saida.conteudo_str()}"
        )

        self._passos_estagio2 = passos

        self._emitir_atualizacao(
            "Estágio 2 — Cópia concluído",
            passos,
            None
        )

        self._emitir(
            "status",
            "Cópia concluída — iniciando retorno."
        )

    # ============================================================
    # ESTÁGIO 3 — RETORNO
    # ============================================================

    def _estagio_retorno(self) -> None:
        """desfaz exatamente a computação realizada."""

        print("\n" + "=" * 60)
        print("  ESTÁGIO 3 — RETORNO (DESFAZER)")
        print("=" * 60)

        if self._historico_tamanho == 0:
            print(
                "  (nada a desfazer — "
                "estágio 1 não completou)"
            )

            self._emitir(
                "status",
                "Nada a desfazer — estágio 1 não completou."
            )

            return

        passos = 0

        historico_pos = (
            self._historico_tamanho - 1
        )

        while historico_pos >= 0:

            self._fita_historico.posicao = (
                historico_pos
            )

            idx_str = (
                self._fita_historico.ler()
            )

            if (
                idx_str
                == self._fita_historico.branco
            ):
                break

            idx = int(idx_str)

            q_original = (
                self._mt.transicoes[idx]
            )

            if not self._aguardar_passo():
                return

            # ----------------------------------------------------
            # DESFAZER
            # ----------------------------------------------------

            dir_inversa = (
                'L'
                if q_original.direcao == 'R'
                else 'R'
            )

            self._fita_trabalho.mover(
                dir_inversa
            )

            self._fita_trabalho.escrever(
                q_original.simbolo_lido
            )

            self._estado_atual = (
                q_original.estado_atual
            )

            # ----------------------------------------------------
            # LIMPAR HISTÓRICO
            # ----------------------------------------------------

            self._fita_historico.escrever(
                self._fita_historico.branco
            )

            if passos < 50:
                print(
                    f"  Desfaz {passos + 1:>4}: "
                    f"Quíntupla[{idx}] inversa — "
                    f"Estado={q_original.estado_atual}, "
                    f"Restaura='{q_original.simbolo_lido}'"
                )

            historico_pos -= 1
            passos += 1

            # ----------------------------------------------------
            # ATUALIZA GUI
            # ----------------------------------------------------

            self._emitir_atualizacao(
                "Estágio 3 — Retorno (Desfazer)",
                passos,
                {
                    "indice": idx,
                    "estado": q_original.estado_atual,
                    "simbolo_restaurado":
                        q_original.simbolo_lido,
                    "direcao_inversa":
                        dir_inversa,
                }
            )

            self._passo_concluido()

        if passos >= 50:
            print(
                f"  ... ({passos - 50} passos omitidos)"
            )

        self._passos_estagio3 = passos

        print(
            f"\n  ✓ Retorno completo "
            f"em {passos} passos."
        )

    # ============================================================
    # IMPRESSÃO ORIGINAL
    # ============================================================

    def _imprimir_cabecalho(self) -> None:
        """imprime informações iniciais."""

        print(
            "╔" + "═" * 58 + "╗"
        )

        print(
            "║  SIMULADOR DE MÁQUINA DE "
            "TURING REVERSÍVEL (Bennett)     ║"
        )

        print(
            "╚" + "═" * 58 + "╝"
        )

        print()

        print(
            "── Definição da MT ──"
        )

        print(
            f"  Estados:            "
            f"{self._mt.estados}"
        )

        print(
            f"  Estado inicial:     "
            f"{self._mt.estado_inicial}"
        )

        print(
            f"  Estado de aceitação:"
            f"{self._mt.estado_aceitacao}"
        )

        print(
            f"  Alfabeto entrada:   "
            f"{self._mt.alfabeto_entrada}"
        )

        print(
            f"  Alfabeto fita:      "
            f"{self._mt.alfabeto_fita}"
        )

        print(
            f"  Transições:         "
            f"{self._mt.num_transicoes} quíntuplas"
        )

        print(
            f"  Entrada:            "
            f"'{self._mt.entrada}'"
        )

        print()

        print(
            "── Conversão para Quádruplas ──"
        )

        for i, q_orig in enumerate(
            self._mt.transicoes
        ):
            q1 = self._quadruplas[
                i * 2
            ]

            q2 = self._quadruplas[
                i * 2 + 1
            ]

            print(
                f"  {q_orig}  →  {q1}"
            )

            print(
                f"  {' ' * len(str(q_orig))}     {q2}"
            )

        print(
            f"  Total: "
            f"{len(self._quadruplas)} quádruplas "
            f"({self._mt.num_transicoes} × 2)"
        )

    def _imprimir_resultado(
        self,
        aceita: bool
    ) -> None:
        """imprime o resultado final."""

        print(
            "\n"
            + "╔"
            + "═" * 58
            + "╗"
        )

        print(
            "║  RESULTADO FINAL                                         ║"
        )

        print(
            "╚"
            + "═" * 58
            + "╝"
        )

        status = (
            "✓ ACEITA"
            if aceita
            else "✗ REJEITA"
        )

        print(
            f"\n  Entrada "
            f"'{self._mt.entrada}': "
            f"{status}"
        )

        saida = (
            self._fita_saida.conteudo_str()
        )

        if saida:
            print(
                f"  Saída (Fita 3):   "
                f"'{saida}'"
            )
        else:
            print(
                "  Saída (Fita 3):   "
                "(vazia)"
            )

        self._imprimir_validacoes()
        self._imprimir_estatisticas()

    def _imprimir_validacoes(self) -> None:
        """imprime as validações de reversibilidade."""

        print(
            "\n── Validações de Reversibilidade ──"
        )

        hist_limpa = (
            self._fita_historico.esta_limpa()
        )

        print(
            f"  Fita 2 (Histórico) limpa:    "
            f"{'✓' if hist_limpa else '✗'}"
        )

        fita1_conteudo = (
            self._fita_trabalho.conteudo_str()
        )

        fita1_ok = (
            fita1_conteudo
            == self._entrada_original
        )

        print(
            f"  Fita 1 restaurada ao original:"
            f"{'✓' if fita1_ok else '✗'}"
            f"  (atual='{fita1_conteudo}', "
            f"esperado='{self._entrada_original}')"
        )

        estado_ok = (
            self._estado_atual
            == self._mt.estado_inicial
        )

        print(
            f"  Estado restaurado ao inicial: "
            f"{'✓' if estado_ok else '✗'}"
            f"  (atual={self._estado_atual}, "
            f"esperado={self._mt.estado_inicial})"
        )

    def _imprimir_estatisticas(self) -> None:
        """imprime estatísticas."""

        total = (
            self._passos_estagio1
            + self._passos_estagio2
            + self._passos_estagio3
        )

        print(
            "\n── Estatísticas ──"
        )

        print(
            f"  Passos Estágio 1 (Ida):     "
            f"{self._passos_estagio1}"
        )

        print(
            f"  Passos Estágio 2 (Cópia):   "
            f"{self._passos_estagio2}"
        )

        print(
            f"  Passos Estágio 3 (Volta):   "
            f"{self._passos_estagio3}"
        )

        print(
            f"  Total de passos:            "
            f"{total}"
        )

        if self._passos_estagio1 > 0:
            razao = (
                total
                / self._passos_estagio1
            )

            print(
                f"  Razão total/ida:            "
                f"{razao:.2f}x "
                f"(Bennett prevê ~4V)"
            )