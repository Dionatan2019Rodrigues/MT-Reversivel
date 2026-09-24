"""simulador reversível de bennett com 3 fitas."""

from __future__ import annotations

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

    def __init__(self, mt: MTDefinition):
        self._mt = mt
        self._estado_atual = mt.estado_inicial
        self._estado_aceitacao = mt.estado_aceitacao
        self._entrada_original = mt.entrada

        # fitas
        self._fita_trabalho = Fita(mt.entrada)
        self._fita_historico = Fita()
        self._fita_saida = Fita()

        # converter quíntuplas em quádruplas
        max_estado = max(mt.estados)
        self._quadruplas, self._quadruplas_inversas, _ = (
            converter_para_quadruplas(mt.transicoes, max_estado)
        )

        # tabela de lookup: (estado, símbolo) -> quíntupla original
        self._tabela: dict[tuple[int, str], Quintupla] = {
            (q.estado_atual, q.simbolo_lido): q for q in mt.transicoes
        }

        # contadores
        self._passos_estagio1 = 0
        self._passos_estagio2 = 0
        self._passos_estagio3 = 0
        self._historico_tamanho = 0

    def executar(self) -> None:
        """executa os 3 estágios completos da máquina reversível."""
        self._imprimir_cabecalho()

        aceita = self._estagio_computacao()
        self._estagio_copia()
        self._estagio_retorno()

        self._imprimir_resultado(aceita)

    # --- estágio 1: computação (ida) ---

    def _estagio_computacao(self) -> bool:
        """emula o programa original na fita 1, gravando histórico na fita 2.

        retorna true se a MT atingiu o estado de aceitação.
        """
        print("\n" + "=" * 60)
        print("  ESTÁGIO 1 — COMPUTAÇÃO (IDA)")
        print("=" * 60)

        passos = 0
        historico_pos = 0

        while self._estado_atual != self._estado_aceitacao:
            simbolo = self._fita_trabalho.ler()
            chave = (self._estado_atual, simbolo)

            if chave not in self._tabela:
                print(
                    f"\n  ✗ Sem transição para "
                    f"({self._estado_atual}, {simbolo}) — MT parou."
                )
                self._passos_estagio1 = passos
                return False

            q = self._tabela[chave]
            self._imprimir_passo_ida(passos, q, simbolo)

            # executar a quíntupla na fita 1
            self._fita_trabalho.escrever(q.simbolo_escrito)
            self._fita_trabalho.mover(q.direcao)
            self._estado_atual = q.proximo_estado

            # gravar índice da quíntupla na fita 2
            self._fita_historico.posicao = historico_pos
            self._fita_historico.escrever(str(q.indice))
            historico_pos += 1

            passos += 1
            if passos >= LIMITE_PASSOS:
                print(
                    f"\n  ⚠ Limite de {LIMITE_PASSOS} passos atingido "
                    f"— abortando."
                )
                self._passos_estagio1 = passos
                return False

        if passos >= 50:
            print(f"  ... ({passos - 50} passos omitidos)")

        print(
            f"\n  ✓ Estado de aceitação ({self._estado_aceitacao}) "
            f"atingido em {passos} passos."
        )
        print(f"  Fita 1 (resultado): {self._fita_trabalho}")
        print(f"  Fita 2 (histórico): {self._fita_historico.conteudo_str()}")

        self._passos_estagio1 = passos
        self._historico_tamanho = historico_pos
        return True

    def _imprimir_passo_ida(
        self, passo: int, q: Quintupla, simbolo: str
    ) -> None:
        """imprime um passo do estágio 1, limitado aos primeiros 50."""
        if passo >= 50:
            return
        print(
            f"  Passo {passo + 1:>4}: Estado={q.estado_atual}, "
            f"Lê='{simbolo}' → Escreve='{q.simbolo_escrito}', "
            f"Move={q.direcao}, Estado'={q.proximo_estado}"
        )
        print(f"             Fita 1: {self._fita_trabalho}")

    # --- estágio 2: cópia ---

    def _estagio_copia(self) -> None:
        """copia o conteúdo relevante da fita 1 para a fita 3.

        processo intrinsecamente reversível (cópia bit-a-bit).
        """
        print("\n" + "=" * 60)
        print("  ESTÁGIO 2 — CÓPIA")
        print("=" * 60)

        pos_salva = self._fita_trabalho.posicao

        if self._fita_trabalho.celulas:
            pos_min = min(self._fita_trabalho.celulas.keys())
            pos_max = max(self._fita_trabalho.celulas.keys())
        else:
            pos_min = pos_max = 0

        # copiar cada célula não-branca da fita 1 para a fita 3
        passos = 0
        saida_pos = 0
        for i in range(pos_min, pos_max + 1):
            simbolo = self._fita_trabalho.celulas.get(
                i, self._fita_trabalho.branco
            )
            if simbolo != self._fita_trabalho.branco:
                self._fita_saida.posicao = saida_pos
                self._fita_saida.escrever(simbolo)
                saida_pos += 1
                passos += 1

        # restaurar posição do cabeçote da fita 1
        self._fita_trabalho.posicao = pos_salva
        self._fita_saida.posicao = 0

        print(f"  Copiados {passos} símbolos para a Fita 3.")
        print(f"  Fita 3 (saída): {self._fita_saida.conteudo_str()}")
        self._passos_estagio2 = passos

    # --- estágio 3: retorno (desfazer) ---

    def _estagio_retorno(self) -> None:
        """executa o inverso exato do estágio 1.

        lê a fita 2 de trás para frente, aplicando as quíntuplas
        inversas para restaurar a fita 1 e limpar a fita 2.
        """
        print("\n" + "=" * 60)
        print("  ESTÁGIO 3 — RETORNO (DESFAZER)")
        print("=" * 60)

        if self._historico_tamanho == 0:
            print("  (nada a desfazer — estágio 1 não completou)")
            return

        passos = 0
        historico_pos = self._historico_tamanho - 1

        while historico_pos >= 0:
            self._fita_historico.posicao = historico_pos
            idx_str = self._fita_historico.ler()

            if idx_str == self._fita_historico.branco:
                break

            idx = int(idx_str)
            q_original = self._mt.transicoes[idx]

            # desfazer: mover na direção oposta e restaurar símbolo
            dir_inversa = 'L' if q_original.direcao == 'R' else 'R'
            self._fita_trabalho.mover(dir_inversa)
            self._fita_trabalho.escrever(q_original.simbolo_lido)
            self._estado_atual = q_original.estado_atual

            # limpar posição do histórico
            self._fita_historico.escrever(self._fita_historico.branco)

            if passos < 50:
                print(
                    f"  Desfaz {passos + 1:>4}: Quíntupla[{idx}] inversa — "
                    f"Estado={q_original.estado_atual}, "
                    f"Restaura='{q_original.simbolo_lido}'"
                )

            historico_pos -= 1
            passos += 1

        if passos >= 50:
            print(f"  ... ({passos - 50} passos omitidos)")

        self._passos_estagio3 = passos
        print(f"\n  ✓ Retorno completo em {passos} passos.")

    # --- impressão ---

    def _imprimir_cabecalho(self) -> None:
        """imprime informações iniciais sobre a MT e as quádruplas geradas."""
        print("╔" + "═" * 58 + "╗")
        print("║  SIMULADOR DE MÁQUINA DE TURING REVERSÍVEL (Bennett)     ║")
        print("╚" + "═" * 58 + "╝")
        print()
        print("── Definição da MT ──")
        print(f"  Estados:            {self._mt.estados}")
        print(f"  Estado inicial:     {self._mt.estado_inicial}")
        print(f"  Estado de aceitação:{self._mt.estado_aceitacao}")
        print(f"  Alfabeto entrada:   {self._mt.alfabeto_entrada}")
        print(f"  Alfabeto fita:      {self._mt.alfabeto_fita}")
        print(f"  Transições:         {self._mt.num_transicoes} quíntuplas")
        print(f"  Entrada:            '{self._mt.entrada}'")
        print()
        print("── Conversão para Quádruplas ──")
        for i, q_orig in enumerate(self._mt.transicoes):
            q1 = self._quadruplas[i * 2]
            q2 = self._quadruplas[i * 2 + 1]
            print(f"  {q_orig}  →  {q1}")
            print(f"  {' ' * len(str(q_orig))}     {q2}")
        print(
            f"  Total: {len(self._quadruplas)} quádruplas "
            f"({self._mt.num_transicoes} × 2)"
        )

    def _imprimir_resultado(self, aceita: bool) -> None:
        """imprime o resultado final e as validações de reversibilidade."""
        print("\n" + "╔" + "═" * 58 + "╗")
        print("║  RESULTADO FINAL                                         ║")
        print("╚" + "═" * 58 + "╝")

        status = "✓ ACEITA" if aceita else "✗ REJEITA"
        print(f"\n  Entrada '{self._mt.entrada}': {status}")

        saida = self._fita_saida.conteudo_str()
        print(f"  Saída (Fita 3):   '{saida}'" if saida else
              "  Saída (Fita 3):   (vazia)")

        self._imprimir_validacoes()
        self._imprimir_estatisticas()

    def _imprimir_validacoes(self) -> None:
        """imprime as validações de reversibilidade."""
        print("\n── Validações de Reversibilidade ──")

        hist_limpa = self._fita_historico.esta_limpa()
        print(f"  Fita 2 (Histórico) limpa:    {'✓' if hist_limpa else '✗'}")

        fita1_conteudo = self._fita_trabalho.conteudo_str()
        fita1_ok = fita1_conteudo == self._entrada_original
        print(
            f"  Fita 1 restaurada ao original:{'✓' if fita1_ok else '✗'}"
            f"  (atual='{fita1_conteudo}', "
            f"esperado='{self._entrada_original}')"
        )

        estado_ok = self._estado_atual == self._mt.estado_inicial
        print(
            f"  Estado restaurado ao inicial: {'✓' if estado_ok else '✗'}"
            f"  (atual={self._estado_atual}, "
            f"esperado={self._mt.estado_inicial})"
        )

    def _imprimir_estatisticas(self) -> None:
        """imprime estatísticas de passos dos 3 estágios."""
        total = (
            self._passos_estagio1
            + self._passos_estagio2
            + self._passos_estagio3
        )
        print("\n── Estatísticas ──")
        print(f"  Passos Estágio 1 (Ida):     {self._passos_estagio1}")
        print(f"  Passos Estágio 2 (Cópia):   {self._passos_estagio2}")
        print(f"  Passos Estágio 3 (Volta):   {self._passos_estagio3}")
        print(f"  Total de passos:            {total}")

        if self._passos_estagio1 > 0:
            razao = total / self._passos_estagio1
            print(
                f"  Razão total/ida:            {razao:.2f}x "
                f"(Bennett prevê ~4V)"
            )
