import tkinter
import tkinter.scrolledtext as st
import tkinter.filedialog
import tkinter.messagebox
import tkinter.ttk as ttk
import threading

from PIL import Image, ImageTk

import mtp

PADDING_Y = 20
PADDING_X = 20


class MTPClient:
    def __init__(self):
        self.root = tkinter.Tk()
        self.init_root()
        self.create_gui()

        self.root.mainloop()

    def init_root(self):
        """
        Inits the main window
        """
        self.root.geometry('800x500')
        self.root.resizable(False, False)
        self.root.title('MTP Klient')
        ico = Image.open('assets/icon.png')
        photo = ImageTk.PhotoImage(ico)
        self.root.wm_iconphoto(True, photo)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        """
        Is called when the main window is closed
        """
        for thread in threading.enumerate():
            if thread.getName() == "MTPThread":
                thread.join()
        self.root.destroy()

    def create_gui(self):
        """Creates the gui"""
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)

        self.create_fields()
        self.create_meme_thumbnail()
        self.create_remaining()

        self.bind_check_funcs()

    def create_fields(self):
        """
        Creates the upper left part of the gui
        """
        # create a frame (container for all fields)
        frame = tkinter.Frame(self.root)
        frame.grid(column=0, row=0, sticky='nwes', padx=PADDING_X, pady=PADDING_Y)

        # ip adress
        self.ip_adr_label: tkinter.Label = tkinter.Label(frame, text="IP adresa:")
        self.ip_adr_label.grid(column=0, row=0, sticky="w")

        self.ip_adr_entry_content: tkinter.StringVar = tkinter.StringVar()
        self.ip_adr_entry: tkinter.Entry = tkinter.Entry(frame, textvariable=self.ip_adr_entry_content)
        self.ip_adr_entry.grid(column=1, row=0)

        # port
        self.port_label: tkinter.Label = tkinter.Label(frame, text="Port:")
        self.port_label.grid(column=0, row=1, sticky="w")

        self.port_entry_content: tkinter.StringVar = tkinter.StringVar()
        self.port_entry: tkinter.Entry = tkinter.Entry(frame, textvariable=self.port_entry_content)
        self.port_entry.grid(column=1, row=1)

        # nick
        self.nick_label: tkinter.Label = tkinter.Label(frame, text="Nick:")
        self.nick_label.grid(column=0, row=2, sticky="w")

        self.nick_entry_content: tkinter.StringVar = tkinter.StringVar()
        self.nick_entry: tkinter.Entry = tkinter.Entry(frame, textvariable=self.nick_entry_content)
        self.nick_entry.grid(column=1, row=2)

        # password
        self.password_label: tkinter.Label = tkinter.Label(frame, text="Heslo:")
        self.password_label.grid(column=0, row=3, sticky="w")

        self.password_entry_content: tkinter.StringVar = tkinter.StringVar()
        self.password_entry: tkinter.Entry = tkinter.Entry(frame, textvariable=self.password_entry_content)
        self.password_entry.grid(column=1, row=3)

        # NSFW
        self.nsfw_var: tkinter.BooleanVar = tkinter.BooleanVar(value=False)

        self.nsfw_checkbox: tkinter.Checkbutton = tkinter.Checkbutton(frame, text="NSFW",
                                                                      variable=self.nsfw_var)
        self.nsfw_checkbox.grid(column=0, row=4, sticky='nwes', columnspan=2)

        # browse meme
        self.browse_meme_label: tkinter.Label = tkinter.Label(frame, text="Meme:")
        self.browse_meme_label.grid(column=0, row=5, pady=40, sticky="w")

        self.meme_path: tkinter.StringVar = tkinter.StringVar()
        self.meme_button: tkinter.Button = tkinter.Button(frame, text="Procházet", command=self.on_browse_click)
        self.meme_button.grid(column=1, row=5, pady=40, sticky="nwes")

    def on_browse_click(self, event=None):
        path = tkinter.filedialog.askopenfilename(filetypes=[("MEMES (*.png, *.jpg, *.jpeg)", "*.png *.jpg *.jpeg")])

        if path:
            self.update_meme_thumbnail(path)
            self.meme_path.set(path)

    def update_meme_thumbnail(self, meme_path):
        img = Image.open(meme_path)
        img.thumbnail((600, 300), Image.ANTIALIAS)
        image = ImageTk.PhotoImage(img)

        self.meme_thumbnail.configure(image=image)
        self.meme_thumbnail.img = image

    def create_meme_thumbnail(self):
        """
        Creates the upper right part of the gui
        """
        self.meme_thumbnail: tkinter.Label = tkinter.Label(self.root)
        self.meme_thumbnail.grid(row=0, column=1, sticky='nwes', pady=(PADDING_Y, 0), padx=(0, PADDING_X))
        self.update_meme_thumbnail("assets/thumbnail.png")

    def create_remaining(self):
        """
        Creates the bottom part of the gui
        """
        self.upload_frame = tkinter.Frame(self.root)
        self.upload_frame.grid(column=0, row=1, sticky='nwes', padx=PADDING_X, pady=(0, PADDING_Y), columnspan=2)

        self.upload_frame.columnconfigure(0, weight=1)
        self.upload_frame.columnconfigure(1, weight=1)

        self.desc_label: tkinter.Label = tkinter.Label(self.upload_frame, text="Popisek:")
        self.desc_label.grid(column=0, row=0, sticky="w")

        self.desc_content: tkinter.StringVar = tkinter.StringVar()
        self.desc: st.ScrolledText = st.ScrolledText(self.upload_frame, width=55, height=9)
        self.desc.grid(column=0, row=1, sticky="nwes")
        self.desc.bind('<KeyRelease>', self.on_desc_edited)

        self.create_upload_button()

    def create_upload_button(self):
        upload_thread = threading.Thread(target=self.on_upload_click)
        upload_thread.setName("MTPThread")

        self.upload_button: tkinter.Button = tkinter.Button(self.upload_frame, text="Nahrát",
                                                            command=upload_thread.start)
        self.upload_button.grid(column=1, row=1, sticky="nwes", padx=(30, 0))
        self.upload_button["state"] = "disabled"

    def on_desc_edited(self, event=None):
        self.desc_content.set(self.desc.get("1.0", "end"))
        # print(self.desc_content.get())
        #self.desc.replace("1.0", "end", self.desc_content.get())

    def on_upload_click(self, event=None):
        # disable everything to prevent the user from editing the data that is being sent
        # create progress bar
        self.upload_button.grid_forget()

        self.pb_label = tkinter.Label(self.upload_frame, text="Nahrávám...")
        self.pb_label.grid(column=1, row=0, padx=(30, 0), sticky="w")

        self.pb = ttk.Progressbar(self.upload_frame, orient="horizontal", mode='determinate')
        self.pb.grid(column=1, row=1, padx=(30, 0), sticky="nwe")
        self.pb.start()

        self.ip_adr_entry["state"] = "disabled"
        self.port_entry["state"] = "disabled"
        self.nick_entry["state"] = "disabled"
        self.password_entry["state"] = "disabled"
        self.nsfw_checkbox["state"] = "disabled"
        self.meme_button["state"] = "disabled"
        self.desc["state"] = "disabled"

        try:
            mtp_con = mtp.MTPConnection(self.ip_adr_entry_content.get(), int(self.port_entry_content.get()),
                                        self.nick_entry_content.get(), self.meme_path.get(), self.password_entry_content.get(),
                                        self.desc.get("1.0", "end"), str(self.nsfw_var.get()).lower())

            if mtp_con.successful:
                tkinter.messagebox.showinfo(title="MEME", message="Meme bylo úspěšně nahráno!")
                self.update_meme_thumbnail("assets/thumbnail.png")
                self.meme_path.set("")
            else:
                tkinter.messagebox.showerror(title="MEME", message="Došlo k chybě při nahrávání")

        except mtp.MTPError as mtperr:
            tkinter.messagebox.showerror(title="MEME", message="Došlo k chybě MTP")
            # print("Došlo k chybě MTP")
        except Exception:
            tkinter.messagebox.showerror(title="MEME", message="Došlo k chybě při nahrávání")
            # print("Došlo k nějaké jiné chybě")
        finally:
            self.pb.stop()

        self.ip_adr_entry["state"] = "normal"
        self.port_entry["state"] = "normal"
        self.nick_entry["state"] = "normal"
        self.password_entry["state"] = "normal"
        self.nsfw_checkbox["state"] = "normal"
        self.desc["state"] = "normal"
        self.meme_button["state"] = "normal"

        self.pb_label.grid_forget()
        self.pb.grid_forget()

        self.create_upload_button()
        self.meme_path.set(self.meme_path.get())

    def bind_check_funcs(self):
        """
        Binds the entries, meme choosing button and description with check functions, so the user can send meme
        only if all information is filled in
        """
        self.ip_adr_entry_content.trace_add("write", self.check_filled)
        self.port_entry_content.trace_add("write", self.check_filled)
        self.nick_entry_content.trace_add("write", self.check_filled)
        self.password_entry_content.trace_add("write", self.check_filled)
        self.desc_content.trace_add("write", self.check_filled)
        self.meme_path.trace_add("write", self.check_filled)

    def check_filled(self, *args):
        if self.ip_adr_entry_content.get() and self.port_entry_content.get() and self.nick_entry_content.get() and \
                self.password_entry_content.get() and self.desc_content.get() and self.meme_path.get():
            self.upload_button["state"] = "normal"
        else:
            self.upload_button["state"] = "disabled"


if __name__ == "__main__":
    MTPClient()
