"""conversor de quíntuplas clássicas para quádruplas reversíveis de bennett."""

from __future__ import annotations

from modelos import Quadrupla, Quintupla


def converter_para_quadruplas(
    transicoes: list[Quintupla],
    max_estado: int,
) -> tuple[list[Quadrupla], list[Quadrupla], int]:
    """converte cada quíntupla em duas quádruplas com estado intermediário.

    cada quíntupla (lê-escreve-move) é separada em:
      - quádrupla de escrita (lê-escreve)
      - quádrupla de movimento (lê-move)

    retorna:
        (quadruplas_diretas, quadruplas_inversas, próximo_estado_disponível)
    """
    quadruplas: list[Quadrupla] = []
    inversas: list[Quadrupla] = []
    prox_estado = max_estado + 1

    for quintupla in transicoes:
        estado_inter = prox_estado
        prox_estado += 1

        direta_escrita, direta_movimento = _criar_par_direto(
            quintupla, estado_inter
        )
        quadruplas.extend([direta_escrita, direta_movimento])

        inversa_movimento, inversa_escrita = _criar_par_inverso(
            quintupla, estado_inter
        )
        inversas.extend([inversa_movimento, inversa_escrita])

    return quadruplas, inversas, prox_estado


def _criar_par_direto(
    q: Quintupla,
    estado_inter: int,
) -> tuple[Quadrupla, Quadrupla]:
    """cria o par de quádruplas diretas (estágio 1 — ida)."""
    # q1: (estado_atual, símbolo_lido) -> (estado_inter, símbolo_escrito)
    escrita = Quadrupla(
        estado_atual=q.estado_atual,
        simbolo_lido=q.simbolo_lido,
        proximo_estado=estado_inter,
        simbolo_escrito=q.simbolo_escrito,
        direcao=None,
        tipo='ESCREVER',
        indice_quintupla=q.indice,
    )
    # q2: (estado_inter, símbolo_escrito) -> (próximo_estado, direção)
    movimento = Quadrupla(
        estado_atual=estado_inter,
        simbolo_lido=q.simbolo_escrito,
        proximo_estado=q.proximo_estado,
        simbolo_escrito=None,
        direcao=q.direcao,
        tipo='MOVER',
        indice_quintupla=q.indice,
    )
    return escrita, movimento


def _criar_par_inverso(
    q: Quintupla,
    estado_inter: int,
) -> tuple[Quadrupla, Quadrupla]:
    """cria o par de quádruplas inversas (estágio 3 — volta).

    para inverter: trocar estados, trocar lido/escrito e inverter direção.
    """
    # inversa do movimento: trocar estados, inverter direção
    inv_movimento = Quadrupla(
        estado_atual=q.proximo_estado,
        simbolo_lido=q.simbolo_escrito,
        proximo_estado=estado_inter,
        simbolo_escrito=None,
        direcao='L' if q.direcao == 'R' else 'R',
        tipo='MOVER',
        indice_quintupla=q.indice,
    )
    # inversa da escrita: trocar estados, trocar lido/escrito
    inv_escrita = Quadrupla(
        estado_atual=estado_inter,
        simbolo_lido=q.simbolo_escrito,
        proximo_estado=q.estado_atual,
        simbolo_escrito=q.simbolo_lido,
        direcao=None,
        tipo='ESCREVER',
        indice_quintupla=q.indice,
    )
    return inv_movimento, inv_escrita
