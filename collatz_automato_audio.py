
import io
import math
import os
import platform
import random
import struct
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
import wave

from tkinter import messagebox


# Tenta importar winsound para reprodução instantânea no Windows.
try:
    import winsound

    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False


class CollatzAutomatonAudioApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Autômato Celular e Sonificação de Collatz")
        self.root.geometry("960x700")
        self.root.configure(bg="#1e1e2e")

        self.current_number = 27
        self.steps = []
        self.is_playing = False
        self.stop_requested = False

        # Definição das escalas musicais (frequências base em Hz
        # a partir de C4 = 261.63 Hz).
        self.scales = {
            "Pentatônica Maior (Harmônica)": [
                261.63,
                293.66,
                329.63,
                392.00,
                440.00,
                523.25,
                587.33,
                659.25,
                783.99,
                880.00,
            ],
            "Menor Natural (Dramática)": [
                261.63,
                293.66,
                311.13,
                349.23,
                392.00,
                415.30,
                466.16,
                523.25,
                587.33,
                622.25,
            ],
            "Cromática (Experimental)": [
                261.63,
                277.18,
                293.66,
                311.13,
                329.63,
                349.23,
                369.99,
                392.00,
                415.30,
                440.00,
                466.16,
                493.88,
            ],
            "Contagem de Bits '1' (Hz Direto)": "bits_hz",
        }

        self.setup_ui()
        self.generate_and_draw()

    def setup_ui(self):

        # Painel Superior 1: Controles Numéricos e Alinhamento.
        control_frame = tk.Frame(
            self.root,
            bg="#282a36",
            pady=8,
            padx=10,
        )
        control_frame.pack(fill=tk.X)

        tk.Label(
            control_frame,
            text="Número (n):",
            fg="#f8f8f2",
            bg="#282a36",
            font=("Arial", 10, "bold"),
        ).pack(side=tk.LEFT, padx=5)

        self.entry_num = tk.Entry(
            control_frame,
            font=("Consolas", 12),
            width=12,
        )
        self.entry_num.insert(0, str(self.current_number))
        self.entry_num.pack(side=tk.LEFT, padx=5)
        self.entry_num.bind(
            "<Return>",
            lambda event: self.on_calculate(),
        )

        btn_style = {
            "font": ("Arial", 9, "bold"),
            "bd": 0,
            "padx": 10,
            "pady": 5,
            "cursor": "hand2",
        }

        tk.Button(
            control_frame,
            text="Calcular",
            bg="#50fa7b",
            fg="#282a36",
            command=self.on_calculate,
            **btn_style,
        ).pack(side=tk.LEFT, padx=4)

        tk.Button(
            control_frame,
            text="- 1",
            bg="#6272a4",
            fg="#f8f8f2",
            command=lambda: self.adjust_number(-1),
            **btn_style,
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            control_frame,
            text="+ 1",
            bg="#6272a4",
            fg="#f8f8f2",
            command=lambda: self.adjust_number(1),
            **btn_style,
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            control_frame,
            text="Aleatório (Ímpar)",
            bg="#bd93f9",
            fg="#282a36",
            command=self.random_odd,
            **btn_style,
        ).pack(side=tk.LEFT, padx=5)

        # Alinhamento.
        self.align_var = tk.StringVar(value="right")

        tk.Label(
            control_frame,
            text="Alinhamento:",
            fg="#f8f8f2",
            bg="#282a36",
            font=("Arial", 10),
        ).pack(side=tk.LEFT, padx=(15, 5))

        tk.Radiobutton(
            control_frame,
            text="Direita (LSB)",
            variable=self.align_var,
            value="right",
            bg="#282a36",
            fg="#f8f8f2",
            selectcolor="#44475a",
            command=self.generate_and_draw,
        ).pack(side=tk.LEFT)

        tk.Radiobutton(
            control_frame,
            text="Esquerda (MSB)",
            variable=self.align_var,
            value="left",
            bg="#282a36",
            fg="#f8f8f2",
            selectcolor="#44475a",
            command=self.generate_and_draw,
        ).pack(side=tk.LEFT)

        # Painel Superior 2: Controles de Sonificação (Áudio).
        audio_frame = tk.Frame(
            self.root,
            bg="#21222c",
            pady=8,
            padx=10,
        )
        audio_frame.pack(fill=tk.X)

        self.btn_play = tk.Button(
            audio_frame,
            text="▶ Tocar Sonificação",
            bg="#ffb86c",
            fg="#282a36",
            command=self.toggle_audio,
            **btn_style,
        )
        self.btn_play.pack(side=tk.LEFT, padx=5)

        tk.Label(
            audio_frame,
            text="Escala Musical:",
            fg="#f8f8f2",
            bg="#21222c",
            font=("Arial", 10),
        ).pack(side=tk.LEFT, padx=(10, 5))

        scale_menu = tk.OptionMenu(
            audio_frame,
            self.scale_var,
            *self.scales.keys(),
        ) if hasattr(self, "scale_var") else None

        if scale_menu is None:
            self.scale_var = tk.StringVar(
                value="Pentatônica Maior (Harmônica)"
            )
            scale_menu = tk.OptionMenu(
                audio_frame,
                self.scale_var,
                *self.scales.keys(),
            )

        scale_menu.config(
            bg="#44475a",
            fg="#f8f8f2",
            highlightthickness=0,
            bd=0,
            font=("Arial", 9),
        )
        scale_menu["menu"].config(
            bg="#44475a",
            fg="#f8f8f2",
        )
        scale_menu.pack(side=tk.LEFT, padx=5)

        tk.Label(
            audio_frame,
            text="Velocidade (ms/nota):",
            fg="#f8f8f2",
            bg="#21222c",
            font=("Arial", 10),
        ).pack(side=tk.LEFT, padx=(15, 5))

        self.speed_slider = tk.Scale(
            audio_frame,
            from_=50,
            to=400,
            orient=tk.HORIZONTAL,
            bg="#21222c",
            fg="#f8f8f2",
            highlightthickness=0,
            length=130,
        )
        self.speed_slider.set(140)
        self.speed_slider.pack(side=tk.LEFT)

        # Painel de Estatísticas e Nota Atual.
        self.stats_label = tk.Label(
            self.root,
            text="",
            fg="#8be9fd",
            bg="#1e1e2e",
            font=("Consolas", 10),
            pady=5,
        )
        self.stats_label.pack(fill=tk.X)

        # Área de Visualização (Canvas com Scrollbars).
        canvas_frame = tk.Frame(
            self.root,
            bg="#1e1e2e",
        )
        canvas_frame.pack(
            fill=tk.BOTH,
            expand=True,
            padx=10,
            pady=10,
        )

        self.v_scroll = tk.Scrollbar(
            canvas_frame,
            orient=tk.VERTICAL,
        )
        self.h_scroll = tk.Scrollbar(
            canvas_frame,
            orient=tk.HORIZONTAL,
        )

        self.canvas = tk.Canvas(
            canvas_frame,
            bg="#181825",
            highlightthickness=0,
            yscrollcommand=self.v_scroll.set,
            xscrollcommand=self.h_scroll.set,
        )

        self.v_scroll.config(command=self.canvas.yview)
        self.h_scroll.config(command=self.canvas.xview)

        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True,
        )

    def get_collatz_binary_steps(self, n):

        steps = []
        max_val = n

        while n > 1:
            steps.append((n, bin(n)[2:]))

            if n % 2 == 0:
                n = n // 2
            else:
                n = 3 * n + 1

            if n > max_val:
                max_val = n

        steps.append((1, "1"))

        return steps, max_val

    def generate_and_draw(self):

        self.stop_audio()
        self.canvas.delete("all")

        self.steps, max_val = self.get_collatz_binary_steps(
            self.current_number
        )

        total_steps = len(self.steps) - 1
        max_bits = len(bin(max_val)[2:])

        self.stats_label.config(
            text=(
                f"Início: {self.current_number} "
                f"({bin(self.current_number)[2:]})"
                f" | Passos até 1: {total_steps}"
                f" | Pico Máximo: {max_val}"
                f" ({max_bits} bits)"
            )
        )

        self.cell_size = max(
            5,
            min(16, 750 // max(max_bits, 1)),
        )

        self.offset_x = 120
        self.offset_y = 20
        self.max_bits = max_bits

        for row_idx, (dec_val, bin_str) in enumerate(self.steps):

            y1 = self.offset_y + row_idx * self.cell_size
            y2 = y1 + self.cell_size

            if self.cell_size >= 8:
                self.canvas.create_text(
                    self.offset_x - 10,
                    (y1 + y2) / 2,
                    text=str(dec_val),
                    anchor="e",
                    fill="#6272a4",
                    font=("Consolas", 8),
                )

            start_col = (
                max_bits - len(bin_str)
                if self.align_var.get() == "right"
                else 0
            )

            for bit_idx, bit in enumerate(bin_str):

                col_idx = start_col + bit_idx

                x1 = self.offset_x + col_idx * self.cell_size
                x2 = x1 + self.cell_size

                if bit == "1":
                    color = (
                        "#ff79c6"
                        if dec_val % 2 != 0
                        else "#50fa7b"
                    )
                else:
                    color = "#282a36"

                outline_color = (
                    "#181825"
                    if self.cell_size > 5
                    else ""
                )

                self.canvas.create_rectangle(
                    x1,
                    y1,
                    x2,
                    y2,
                    fill=color,
                    outline=outline_color,
                )

        total_width = (
            self.offset_x
            + (max_bits * self.cell_size)
            + 40
        )

        total_height = (
            self.offset_y
            + (len(self.steps) * self.cell_size)
            + 40
        )

        self.canvas.config(
            scrollregion=(0, 0, total_width, total_height)
        )

    def get_frequency_for_step(self, dec_val, bin_str):

        selected = self.scales[self.scale_var.get()]

        if selected == "bits_hz":
            ones_count = bin_str.count("1")
            return 220.0 + (ones_count * 45.0)

        else:
            note_index = dec_val % len(selected)
            return selected[note_index]

    def generate_wav_bytes(self, freq, duration_sec, is_odd):

        sample_rate = 22050
        n_samples = int(sample_rate * duration_sec)

        buf = io.BytesIO()

        with wave.open(buf, "wb") as wav_file:

            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)

            frames = bytearray()

            for i in range(n_samples):

                t = i / sample_rate

                env = min(
                    1.0,
                    i / (sample_rate * 0.015),
                ) * min(
                    1.0,
                    (n_samples - i) / (sample_rate * 0.03),
                )

                if is_odd:
                    val = (
                        0.7 * math.sin(2 * math.pi * freq * t)
                        + 0.3 * math.sin(4 * math.pi * freq * t)
                    )
                else:
                    val = math.sin(2 * math.pi * freq * t)

                sample = int(val * env * 16000)

                frames.extend(struct.pack("<h", sample))

            wav_file.writeframes(frames)

        return buf.getvalue()

    def play_wav_data(self, wav_bytes):

        if HAS_WINSOUND:
            winsound.PlaySound(
                wav_bytes,
                winsound.SND_MEMORY,
            )

        else:
            with tempfile.NamedTemporaryFile(
                suffix=".wav",
                delete=False,
            ) as tmp:
                tmp.write(wav_bytes)
                tmp_path = tmp.name

            try:
                sys_name = platform.system()

                if sys_name == "Darwin":
                    subprocess.run(
                        ["afplay", tmp_path],
                        check=False,
                    )
                else:
                    subprocess.run(
                        ["aplay", "-q", tmp_path],
                        check=False,
                    )

            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

    def toggle_audio(self):

        if self.is_playing:
            self.stop_audio()

        else:
            self.is_playing = True
            self.stop_requested = False

            self.btn_play.config(
                text="⏹ Parar Áudio",
                bg="#ff5555",
                fg="#f8f8f2",
            )

            threading.Thread(
                target=self.audio_playback_loop,
                daemon=True,
            ).start()

    def stop_audio(self):

        self.stop_requested = True
        self.is_playing = False

        self.btn_play.config(
            text="▶ Tocar Sonificação",
            bg="#ffb86c",
            fg="#282a36",
        )

        self.canvas.delete("highlight")

    def audio_playback_loop(self):

        for row_idx, (dec_val, bin_str) in enumerate(self.steps):

            if self.stop_requested:
                break

            duration_ms = self.speed_slider.get()
            duration_sec = duration_ms / 1000.0

            freq = self.get_frequency_for_step(
                dec_val,
                bin_str,
            )

            is_odd = dec_val % 2 != 0

            self.root.after(
                0,
                self.highlight_row,
                row_idx,
                dec_val,
                freq,
            )

            wav_bytes = self.generate_wav_bytes(
                freq,
                duration_sec,
                is_odd,
            )

            self.play_wav_data(wav_bytes)

        self.root.after(0, self.stop_audio)

    def highlight_row(self, row_idx, dec_val, freq):

        self.canvas.delete("highlight")

        y1 = self.offset_y + row_idx * self.cell_size
        y2 = y1 + self.cell_size

        x2 = (
            self.offset_x
            + (self.max_bits * self.cell_size)
            + 10
        )

        self.canvas.create_rectangle(
            self.offset_x - 5,
            y1,
            x2,
            y2,
            outline="#f1fa8c",
            width=2,
            tags="highlight",
        )

        total_height = (
            self.offset_y
            + (len(self.steps) * self.cell_size)
            + 40
        )

        if total_height > 0:
            self.canvas.yview_moveto(
                max(0.0, (y1 - 150) / total_height)
            )

        self.stats_label.config(
            text=(
                f"Tocando Passo {row_idx}/{len(self.steps)-1}"
                f" | Valor: {dec_val}"
                f" | Frequência: {freq:.2f} Hz"
            )
        )

    def on_calculate(self):

        try:
            val = int(self.entry_num.get())

            if val < 1:
                raise ValueError

            self.current_number = val
            self.generate_and_draw()

        except ValueError:
            messagebox.showerror(
                "Erro",
                "Por favor, insira um número inteiro positivo "
                "(maior que 0).",
            )

    def adjust_number(self, delta):

        new_val = max(
            1,
            self.current_number + delta,
        )

        self.current_number = new_val

        self.entry_num.delete(0, tk.END)
        self.entry_num.insert(0, str(new_val))

        self.generate_and_draw()

    def random_odd(self):

        new_val = random.randrange(3, 100000, 2)

        self.current_number = new_val

        self.entry_num.delete(0, tk.END)
        self.entry_num.insert(0, str(new_val))

        self.generate_and_draw()


if __name__ == "__main__":

    root = tk.Tk()
    app = CollatzAutomatonAudioApp(root)
    root.mainloop()
