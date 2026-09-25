"""interface gráfica do simulador reversível de Bennett."""

from __future__ import annotations

import queue
import threading
import time
import tkinter as tk


class Visualizador:
    """interface gráfica paralela ao simulador do terminal."""

    def __init__(self):
        self.janela = tk.Tk()

        self.janela.title(
            "Máquina de Turing Reversível — Bennett"
        )

        self.janela.geometry(
            "1150x780"
        )

        self.janela.minsize(
            950,
            680
        )

        # Comunicação segura entre a thread do simulador
        # e a thread principal do Tkinter.
        self.eventos = queue.Queue()

        self.simulador = None
        self.thread = None

        # Controle da execução.
        self.iniciado = False
        self.finalizado = False
        self.modo_passo = False
        self.passo_em_execucao = False

        self.evento_passo = (
            threading.Event()
        )

        self.parar_evento = (
            threading.Event()
        )

        # Velocidade da execução automática.
        self.velocidade = tk.DoubleVar(
            value=0.20
        )

        # Informações da interface.
        self.estado_var = tk.StringVar(
            value="—"
        )

        self.passo_var = tk.StringVar(
            value="Passo: 0"
        )

        self.estagio_var = tk.StringVar(
            value="Estágio: aguardando"
        )

        self.status_var = tk.StringVar(
            value="AGUARDANDO EXECUÇÃO"
        )

        self.transicao_var = tk.StringVar(
            value="Aguardando execução..."
        )

        self._criar_interface()

        self.janela.after(
            30,
            self._processar_eventos
        )

    # ============================================================
    # CONFIGURAÇÃO
    # ============================================================

    def configurar(
        self,
        simulador
    ):
        """recebe o simulador criado pelo simulador.py."""

        self.simulador = simulador

        self._atualizar_interface_com_simulador()

    def _atualizar_interface_com_simulador(
        self
    ):
        """mostra as fitas antes da execução."""

        if self.simulador is None:
            return

        self.estado_var.set(
            str(
                self.simulador._estado_atual
            )
        )

        self._desenhar_fita(
            self.canvas_fita1,
            self._snapshot(
                self.simulador._fita_trabalho
            )
        )

        self._desenhar_fita(
            self.canvas_fita2,
            self._snapshot(
                self.simulador._fita_historico
            )
        )

        self._desenhar_fita(
            self.canvas_fita3,
            self._snapshot(
                self.simulador._fita_saida
            )
        )

    @staticmethod
    def _snapshot(
        fita
    ):
        """faz uma cópia visual de uma fita."""

        return {
            "celulas": dict(
                fita.celulas
            ),
            "posicao": fita.posicao,
            "branco": fita.branco,
        }

    # ============================================================
    # INTERFACE
    # ============================================================

    def _criar_interface(
        self
    ):
        titulo = tk.Label(
            self.janela,
            text=(
                "Máquina de Turing "
                "Reversível — Bennett"
            ),
            font=(
                "Arial",
                20,
                "bold"
            )
        )

        titulo.pack(
            pady=(15, 3)
        )

        subtitulo = tk.Label(
            self.janela,
            text=(
                "Visualização em tempo real — "
                "entrada e prints continuam no terminal"
            ),
            font=(
                "Arial",
                10
            )
        )

        subtitulo.pack(
            pady=(0, 12)
        )

        # --------------------------------------------------------
        # INFORMAÇÕES
        # --------------------------------------------------------

        frame_info = tk.Frame(
            self.janela
        )

        frame_info.pack(
            fill="x",
            padx=25,
            pady=5
        )

        self._criar_info_box(
            frame_info,
            "Estado atual",
            self.estado_var,
            fonte=(
                "Courier New",
                18,
                "bold"
            )
        )

        self._criar_info_box(
            frame_info,
            "Execução",
            self.passo_var,
            extra=self.estagio_var,
            fonte=(
                "Courier New",
                12
            )
        )

        self._criar_info_box(
            frame_info,
            "Status",
            self.status_var,
            fonte=(
                "Arial",
                11,
                "bold"
            )
        )

        # --------------------------------------------------------
        # CONTROLES
        # --------------------------------------------------------

        frame_controles = tk.LabelFrame(
            self.janela,
            text="Controles",
            padx=12,
            pady=12
        )

        frame_controles.pack(
            fill="x",
            padx=25,
            pady=10
        )

        # ÚNICO BOTÃO DE EXECUÇÃO AUTOMÁTICA.
        self.botao_executar = tk.Button(
            frame_controles,
            text="▶ EXECUTAR",
            command=self.executar,
            width=20,
            height=2,
            font=(
                "Arial",
                11,
                "bold"
            )
        )

        self.botao_executar.pack(
            side=tk.LEFT,
            padx=10
        )

        # ÚNICO BOTÃO MANUAL.
        self.botao_passo = tk.Button(
            frame_controles,
            text="⏭ PASSO A PASSO",
            command=self.proximo_passo,
            width=20,
            height=2,
            font=(
                "Arial",
                11,
                "bold"
            )
        )

        self.botao_passo.pack(
            side=tk.LEFT,
            padx=10
        )

        # Velocidade da execução automática.
        frame_velocidade = tk.Frame(
            frame_controles
        )

        frame_velocidade.pack(
            side=tk.RIGHT,
            padx=10
        )

        tk.Label(
            frame_velocidade,
            text="Velocidade:"
        ).pack(
            side=tk.LEFT
        )

        tk.Scale(
            frame_velocidade,
            from_=0.05,
            to=1.0,
            resolution=0.05,
            orient=tk.HORIZONTAL,
            variable=self.velocidade,
            length=180
        ).pack(
            side=tk.LEFT,
            padx=5
        )

        # --------------------------------------------------------
        # TRANSIÇÃO
        # --------------------------------------------------------

        frame_transicao = tk.LabelFrame(
            self.janela,
            text="Transição atual",
            padx=10,
            pady=8
        )

        frame_transicao.pack(
            fill="x",
            padx=25,
            pady=(0, 10)
        )

        tk.Label(
            frame_transicao,
            textvariable=self.transicao_var,
            font=(
                "Courier New",
                11
            ),
            anchor="w"
        ).pack(
            fill="x"
        )

        # --------------------------------------------------------
        # FITAS
        # --------------------------------------------------------

        frame_fitas = tk.LabelFrame(
            self.janela,
            text="Fitas em tempo real",
            padx=10,
            pady=10
        )

        frame_fitas.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=(0, 15)
        )

        self.canvas_fita1 = (
            self._criar_fita(
                frame_fitas,
                "Fita 1 — Trabalho"
            )
        )

        self.canvas_fita2 = (
            self._criar_fita(
                frame_fitas,
                "Fita 2 — Histórico"
            )
        )

        self.canvas_fita3 = (
            self._criar_fita(
                frame_fitas,
                "Fita 3 — Saída"
            )
        )

    def _criar_info_box(
        self,
        parent,
        titulo,
        variavel,
        extra=None,
        fonte=None
    ):
        box = tk.LabelFrame(
            parent,
            text=titulo,
            padx=10,
            pady=8
        )

        box.pack(
            side=tk.LEFT,
            fill="both",
            expand=True,
            padx=5
        )

        tk.Label(
            box,
            textvariable=variavel,
            font=fonte or (
                "Arial",
                11
            )
        ).pack()

        if extra is not None:

            tk.Label(
                box,
                textvariable=extra,
                font=(
                    "Courier New",
                    10
                )
            ).pack(
                pady=(3, 0)
            )

    # ============================================================
    # FITAS
    # ============================================================

    def _criar_fita(
        self,
        parent,
        titulo
    ):
        frame = tk.Frame(
            parent
        )

        frame.pack(
            fill="x",
            pady=5
        )

        tk.Label(
            frame,
            text=titulo,
            font=(
                "Arial",
                10,
                "bold"
            ),
            anchor="w"
        ).pack(
            fill="x"
        )

        canvas = tk.Canvas(
            frame,
            height=82,
            background="white",
            highlightthickness=1,
            highlightbackground="gray"
        )

        canvas.pack(
            fill="x"
        )

        canvas.bind(
            "<Configure>",
            lambda event, c=canvas:
                self._redesenhar_canvas(c)
        )

        self._desenhar_fita_vazia(
            canvas
        )

        return canvas

    def _redesenhar_canvas(
        self,
        canvas
    ):
        snapshot = getattr(
            canvas,
            "_ultimo_snapshot",
            None
        )

        if snapshot is None:
            self._desenhar_fita_vazia(
                canvas
            )
        else:
            self._desenhar_fita(
                canvas,
                snapshot
            )

    def _desenhar_fita_vazia(
        self,
        canvas
    ):
        canvas.delete("all")

        largura = max(
            canvas.winfo_width(),
            800
        )

        tamanho = 55

        centro = (
            largura // 2
        )

        inicio = (
            centro
            - 4 * tamanho
        )

        for i in range(9):

            x1 = (
                inicio
                + i * tamanho
            )

            x2 = (
                x1
                + tamanho
            )

            canvas.create_rectangle(
                x1,
                22,
                x2,
                67,
                outline="black"
            )

            canvas.create_text(
                (x1 + x2) // 2,
                45,
                text="B",
                font=(
                    "Courier New",
                    12
                )
            )

        self._desenhar_cabeca(
            canvas,
            centro
        )

    def _desenhar_cabeca(
        self,
        canvas,
        centro
    ):
        canvas.create_polygon(
            centro - 8,
            8,
            centro + 8,
            8,
            centro,
            20,
            fill="black"
        )

    def _desenhar_fita(
        self,
        canvas,
        snapshot
    ):
        canvas._ultimo_snapshot = snapshot

        canvas.delete("all")

        celulas = snapshot.get(
            "celulas",
            {}
        )

        posicao = snapshot.get(
            "posicao",
            0
        )

        branco = snapshot.get(
            "branco",
            "B"
        )

        largura = max(
            canvas.winfo_width(),
            800
        )

        tamanho = 55

        centro = (
            largura // 2
        )

        inicio = (
            centro
            - 4 * tamanho
        )

        # Mostra nove células,
        # sempre centradas no cabeçote.
        for i, indice in enumerate(
            range(
                posicao - 4,
                posicao + 5
            )
        ):
            x1 = (
                inicio
                + i * tamanho
            )

            x2 = (
                x1
                + tamanho
            )

            simbolo = celulas.get(
                indice,
                branco
            )

            canvas.create_rectangle(
                x1,
                22,
                x2,
                67,
                outline="black"
            )

            canvas.create_text(
                (x1 + x2) // 2,
                45,
                text=str(simbolo),
                font=(
                    "Courier New",
                    12
                )
            )

        self._desenhar_cabeca(
            canvas,
            centro
        )

    # ============================================================
    # EXECUTAR
    # ============================================================

    def executar(
        self
    ):
        """inicia a execução automática."""

        if (
            self.iniciado
            or self.simulador is None
        ):
            return

        self.iniciado = True
        self.modo_passo = False

        self.status_var.set(
            "EXECUTANDO..."
        )

        self.botao_executar.config(
            state=tk.DISABLED
        )

        self.botao_passo.config(
            state=tk.DISABLED
        )

        self.evento_passo.set()

        self._iniciar_thread()

    # ============================================================
    # PASSO A PASSO
    # ============================================================

    def proximo_passo(
        self
    ):
        """inicia ou libera exatamente um passo."""

        if (
            self.finalizado
            or self.simulador is None
        ):
            return

        # Primeiro clique:
        # inicia o modo passo a passo.
        if not self.iniciado:

            self.iniciado = True
            self.modo_passo = True
            self.passo_em_execucao = True

            self.status_var.set(
                "PASSO A PASSO — EXECUTANDO"
            )

            self.botao_executar.config(
                state=tk.DISABLED
            )

            self.botao_passo.config(
                state=tk.DISABLED
            )

            self.evento_passo.set()

            self._iniciar_thread()

            return

        # Cliques seguintes:
        # liberam exatamente um passo.
        if (
            self.modo_passo
            and not self.passo_em_execucao
        ):
            self.passo_em_execucao = True

            self.botao_passo.config(
                state=tk.DISABLED
            )

            self.status_var.set(
                "PASSO A PASSO — EXECUTANDO"
            )

            self.evento_passo.set()

    # ============================================================
    # THREAD
    # ============================================================

    def _iniciar_thread(
        self
    ):
        if (
            self.thread is not None
            and self.thread.is_alive()
        ):
            return

        self.thread = threading.Thread(
            target=self._rodar_simulador,
            daemon=True
        )

        self.thread.start()

    def _rodar_simulador(
        self
    ):
        try:
            self.simulador.executar()

        except Exception as erro:

            self.eventos.put(
                (
                    "erro",
                    str(erro)
                )
            )

    # ============================================================
    # CONTROLADOR DO SIMULADOR
    # ============================================================

    def aguardar_passo(
        self
    ):
        """aguarda autorização para o próximo passo."""

        if self.parar_evento.is_set():
            return False

        # Execução automática.
        if not self.modo_passo:
            return True

        # Passo a passo.
        self.evento_passo.wait()

        if self.parar_evento.is_set():
            return False

        self.evento_passo.clear()

        return True

    def passo_concluido(
        self
    ):
        """chamado pelo simulador após cada alteração real."""

        if self.modo_passo:

            self.passo_em_execucao = False

            self.eventos.put(
                (
                    "aguardando_passo",
                    None
                )
            )

        else:

            atraso = float(
                self.velocidade.get()
            )

            if atraso > 0:
                time.sleep(
                    atraso
                )

    def deve_parar(
        self
    ):
        return self.parar_evento.is_set()

    # ============================================================
    # CALLBACK DO SIMULADOR
    # ============================================================

    def enviar_evento(
        self,
        tipo,
        dados=None
    ):
        """recebe eventos do simulador."""

        self.eventos.put(
            (
                tipo,
                dados
            )
        )

    # ============================================================
    # PROCESSAMENTO DOS EVENTOS
    # ============================================================

    def _processar_eventos(
        self
    ):
        try:

            while True:

                tipo, dados = (
                    self.eventos.get_nowait()
                )

                if tipo == "atualizacao":

                    self._processar_atualizacao(
                        dados
                    )

                elif tipo == "status":

                    self.status_var.set(
                        str(dados)
                    )

                elif tipo == "aguardando_passo":

                    self.status_var.set(
                        "AGUARDANDO PRÓXIMO PASSO"
                    )

                    self.botao_passo.config(
                        state=tk.NORMAL
                    )

                elif tipo == "final":

                    self._processar_final(
                        dados
                    )

                elif tipo == "erro":

                    self._processar_erro(
                        dados
                    )

        except queue.Empty:
            pass

        self.janela.after(
            30,
            self._processar_eventos
        )

    def _processar_atualizacao(
        self,
        dados
    ):
        if not dados:
            return

        self.estado_var.set(
            str(
                dados.get(
                    "estado",
                    "—"
                )
            )
        )

        self.passo_var.set(
            f"Passo: "
            f"{dados.get('passo', 0)}"
        )

        self.estagio_var.set(
            f"Estágio: "
            f"{dados.get('estagio', '—')}"
        )

        transicao = dados.get(
            "transicao"
        )

        if transicao:
            self._atualizar_transicao(
                transicao
            )

        fitas = dados.get(
            "fitas"
        )

        if fitas:

            self._desenhar_fita(
                self.canvas_fita1,
                fitas["fita1"]
            )

            self._desenhar_fita(
                self.canvas_fita2,
                fitas["fita2"]
            )

            self._desenhar_fita(
                self.canvas_fita3,
                fitas["fita3"]
            )

    def _atualizar_transicao(
        self,
        transicao
    ):
        partes = []

        if "indice" in transicao:

            partes.append(
                f"Quíntupla[{transicao['indice']}]"
            )

        if "estado" in transicao:

            partes.append(
                f"Estado={transicao['estado']}"
            )

        if "simbolo_lido" in transicao:

            partes.append(
                f"Lê='{transicao['simbolo_lido']}'"
            )

        if "simbolo_escrito" in transicao:

            partes.append(
                f"Escreve='{transicao['simbolo_escrito']}'"
            )

        if "direcao" in transicao:

            partes.append(
                f"Move={transicao['direcao']}"
            )

        if "proximo_estado" in transicao:

            partes.append(
                f"Estado'={transicao['proximo_estado']}"
            )

        if "simbolo_restaurado" in transicao:

            partes.append(
                "Restaura="
                f"'{transicao['simbolo_restaurado']}'"
            )

        if "direcao_inversa" in transicao:

            partes.append(
                "Move inverso="
                f"{transicao['direcao_inversa']}"
            )

        if partes:

            self.transicao_var.set(
                " | ".join(partes)
            )

    def _processar_final(
        self,
        dados
    ):
        self.finalizado = True
        self.passo_em_execucao = False

        self.status_var.set(
            "EXECUÇÃO FINALIZADA"
        )

        self.botao_executar.config(
            state=tk.DISABLED
        )

        self.botao_passo.config(
            state=tk.DISABLED
        )

        if (
            dados
            and dados.get("fitas")
        ):
            fitas = dados["fitas"]

            self._desenhar_fita(
                self.canvas_fita1,
                fitas["fita1"]
            )

            self._desenhar_fita(
                self.canvas_fita2,
                fitas["fita2"]
            )

            self._desenhar_fita(
                self.canvas_fita3,
                fitas["fita3"]
            )

    def _processar_erro(
        self,
        erro
    ):
        self.status_var.set(
            "ERRO NA EXECUÇÃO"
        )

        self.transicao_var.set(
            str(erro)
        )

        self.botao_executar.config(
            state=tk.DISABLED
        )

        self.botao_passo.config(
            state=tk.DISABLED
        )

    # ============================================================
    # LOOP PRINCIPAL
    # ============================================================

    def iniciar(
        self
    ):
        self.janela.mainloop()