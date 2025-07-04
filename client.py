import base64
import io
import os
from socket import socket, AF_INET, SOCK_STREAM
from customtkinter import *
import threading
from tkinter import filedialog
from PIL import Image


class MainWindow(CTk):
    def __init__(self):
        super().__init__()
        self.geometry("400x300")
        self.configure(fg_color="lightcyan")
        self.username = None
        self.awaiting_username = True

        self.chat_field = CTkScrollableFrame(self, width=360, height=200, fg_color="lightblue")
        self.chat_field.place(x=10, y=10)

        self.button_field = CTkFrame(self, width=400, height=62, fg_color="aliceblue", border_width=2, border_color="darkgray")
        self.button_field.place(x=0, y=239)

        self.message_entry = CTkEntry(self, placeholder_text="Введіть повідомлення:", height=40, width=280, fg_color="lightblue", text_color="gray")
        self.message_entry.place(x=10, y=250)

        self.send_button = CTkButton(self, text=">", width=40, height=40, command=self.send_message, fg_color="lightcyan", text_color="gray", border_width=2, border_color="darkgray", hover_color="lightblue")
        self.send_button.place(x=300, y=250)

        self.open_img_button = CTkButton(self, text="+", width=40, height=40, command=self.open_image, fg_color="lightcyan", text_color="gray", border_width=2, border_color="darkgray", hover_color="lightblue")
        self.open_img_button.place(x=350, y=250)

        self.send_button.configure(state="normal")
        self.open_img_button.configure(state="disabled")

        try:
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.connect(("localhost", 8080))
            self.add_message("Введіть ваше ім’я:", is_system=True)
            threading.Thread(target=self.recv_message, daemon=True).start()
        except Exception as e:
            self.add_message(f"помилка: {e}", is_system=True)

    def add_message(self, message, img=None, from_self=False, is_system=False):
        bg = "transparent" if img else "lightcyan"
        message_frame = CTkFrame(
            self.chat_field,
            fg_color=bg
        )

        anchor_pos = "center" if is_system else ("e" if from_self else "w")
        message_frame.pack(pady=5, anchor=anchor_pos)
        wraplength_size = self.winfo_width() - 40

        CTkLabel(
            message_frame,
            text=message,
            wraplength=wraplength_size,
            text_color="gray",
            fg_color=bg,
            font=("Arial", 12),
            justify="center" if is_system else "left",
            image=img,
            compound="top" if img else None
        ).pack(padx=10, pady=5)

    def send_message(self):
        message = self.message_entry.get()
        if not message:
            return

        if self.awaiting_username:
            self.username = message.strip()
            self.awaiting_username = False

            self.add_message(f"Ласкаво просимо, {self.username}!", is_system=True)

            hello = f"TEXT@{self.username}@{self.username} приєднався до чату!\n"
            try:
                self.sock.sendall(hello.encode('utf-8'))
            except:
                self.add_message("Помилка надсилання привітання серверу", is_system=True)

            self.open_img_button.configure(state="normal")
        else:
            self.add_message(f"{self.username}: {message}", from_self=True)
            data = f"TEXT@{self.username}@{message}\n"
            try:
                self.sock.sendall(data.encode())
            except:
                self.add_message("Помилка надсилання", is_system=True)

        self.message_entry.delete(0, END)

    def recv_message(self):
        buffer = ""
        while True:
            try:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                buffer += chunk.decode(errors='ignore')

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    self.handle_line(line.strip())
            except:
                break
        self.sock.close()

    def handle_line(self, line):
        if not line:
            return
        parts = line.split("@", 3)
        msg_type = parts[0]

        if msg_type == "TEXT":
            author = parts[1]
            message = parts[2]

            if author == self.username and message.strip() == f"{author} приєднався до чату!":
                return

            if message.strip() == f"{author} приєднався до чату!":
                self.add_message(message, is_system=True)
            else:
                self.add_message(f"{author}: {message}", from_self=(author == self.username))

        elif msg_type == "IMAGE":
            author = parts[1]
            filename = parts[2]
            b64_img = parts[3]
            try:
                img_data = base64.b64decode(b64_img)
                pil_img = Image.open(io.BytesIO(img_data))

                max_width = 160
                w, h = pil_img.size
                if w > max_width:
                    ratio = max_width / w
                    w = int(w * ratio)
                    h = int(h * ratio)

                ctk_img = CTkImage(pil_img, size=(w, h))
                self.add_message(f"{author}, надіслав зображення: {filename}",
                                 img=ctk_img, from_self=(author == self.username))
            except:
                self.add_message("Помилка відображення картинки", is_system=True)

    def open_image(self):
        file_name = filedialog.askopenfilename()
        if not file_name:
            return

        with open(file_name, "rb") as f:
            raw = f.read()
        b64_data = base64.b64encode(raw).decode()
        short_name = os.path.basename(file_name)
        data = f"IMAGE@{self.username}@{short_name}@{b64_data}\n"

        try:
            self.sock.sendall(data.encode())
        except:
            self.add_message("Помилка відправки зображення", is_system=True)

        pil_img = Image.open(file_name)
        max_width = 160
        w, h = pil_img.size
        if w > max_width:
            ratio = max_width / w
            w = int(w * ratio)
            h = int(h * ratio)

        ctk_img = CTkImage(pil_img, size=(w, h))
        self.add_message('', img=ctk_img, from_self=True)


if __name__ == "__main__":
    win = MainWindow()
    win.mainloop()