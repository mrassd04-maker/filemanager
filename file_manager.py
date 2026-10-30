import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
import tkinter as tk
from typing import Dict, Optional


class FileManager:
    def __init__(self, master: tk.Tk) -> None:
        self.master = master
        self.master.title("Файловый менеджер")
        self.master.geometry("850x520")
        self.master.minsize(600, 350)
        self.icon_path = Path(__file__).parent / "c:\\Users\\user\\Downloads\\provodnik_fajlov_vjmv55dzcch6.ico"
        if self.icon_path.exists():
            self.master.iconbitmap(str(self.icon_path))

        self.current_path = Path.home()
        self._item_paths: Dict[str, Path] = {}
        self.path_var = tk.StringVar(value=str(self.current_path))

        self._create_widgets()
        self.refresh()

    def _create_widgets(self) -> None:
        navigation = ttk.Frame(self.master, padding=8)
        navigation.pack(fill=tk.X)

        ttk.Button(navigation, text="Вверх", command=self.go_up).pack(side=tk.LEFT)
        ttk.Button(
            navigation, text="Обзор...", command=self.browse_folder
        ).pack(side=tk.LEFT, padx=(6, 8))
        ttk.Entry(navigation, textvariable=self.path_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )
        ttk.Button(
            navigation, text="Перейти", command=self.go_to_path
        ).pack(side=tk.LEFT, padx=(8, 0))

        columns = ("type", "size", "modified")
        self.tree = ttk.Treeview(
            self.master,
            columns=columns,
            show="tree headings",
            selectmode="browse",
        )
        self.tree.heading("#0", text="Имя", anchor=tk.W)
        self.tree.heading("type", text="Тип", anchor=tk.W)
        self.tree.heading("size", text="Размер", anchor=tk.E)
        self.tree.heading("modified", text="Изменён", anchor=tk.W)
        self.tree.column("#0", minwidth=180, width=380, stretch=True)
        self.tree.column("type", minwidth=80, width=120, stretch=False)
        self.tree.column("size", minwidth=80, width=100, stretch=False, anchor=tk.E)
        self.tree.column("modified", minwidth=140, width=160, stretch=False)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=8)
        self.tree.bind("<Double-1>", self.open_selected)
        self.tree.bind("<Return>", self.open_selected)

        actions = ttk.Frame(self.master, padding=8)
        actions.pack(fill=tk.X)
        ttk.Button(actions, text="Открыть", command=self.open_selected).pack(
            side=tk.LEFT
        )
        ttk.Button(actions, text="Новая папка", command=self.create_folder).pack(
            side=tk.LEFT, padx=(6, 0)
        )
        ttk.Button(actions, text="Новый файл", command=self.create_file).pack(
            side=tk.LEFT, padx=(6, 0)
        )
        ttk.Button(actions, text="Переименовать", command=self.rename_selected).pack(
            side=tk.LEFT, padx=(6, 0)
        )
        ttk.Button(actions, text="Удалить", command=self.delete_selected).pack(
            side=tk.LEFT, padx=(6, 0)
        )
        ttk.Button(actions, text="Обновить", command=self.refresh).pack(
            side=tk.RIGHT
        )

    def refresh(self) -> None:
        try:
            entries = list(self.current_path.iterdir())
            entries.sort(key=lambda path: (not path.is_dir(), path.name.casefold()))
        except OSError as error:
            self._clear_entries()
            messagebox.showerror(
                "Файловый менеджер",
                f"Не удалось прочитать папку:\n{self.current_path}\n\n{error}",
            )
            return

        self._clear_entries()
        self.path_var.set(str(self.current_path))

        for index, path in enumerate(entries):
            try:
                is_directory = path.is_dir()
                details = path.stat()
            except OSError as error:
                messagebox.showerror(
                    "Файловый менеджер",
                    f"Не удалось прочитать элемент «{path.name}»:\n{error}",
                )
                continue

            item_id = str(index)
            self._item_paths[item_id] = path
            item_type = "Папка" if is_directory else (path.suffix or "Файл")
            item_size = (
                ""
                if is_directory
                else f"{details.st_size:,} байт".replace(",", " ")
            )
            modified = datetime.fromtimestamp(details.st_mtime).strftime(
                "%d.%m.%Y %H:%M"
            )
            self.tree.insert(
                "",
                tk.END,
                iid=item_id,
                text=path.name,
                values=(item_type, item_size, modified),
            )

    def _clear_entries(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._item_paths.clear()

    @staticmethod
    def _is_valid_name(name: str) -> bool:
        if not name or name in {".", ".."} or name != name.strip():
            return False
        if any(character in name for character in '<>:"/\\|?*'):
            return False
        if any(ord(character) < 32 for character in name):
            return False
        if name.endswith("."):
            return False

        reserved_name = name.split(".", 1)[0].upper()
        reserved_names = {
            "CON",
            "PRN",
            "AUX",
            "NUL",
            *(f"COM{number}" for number in range(1, 10)),
            *(f"LPT{number}" for number in range(1, 10)),
        }
        return reserved_name not in reserved_names

    def go_to_path(self) -> None:
        path = Path(self.path_var.get()).expanduser()
        if not path.is_dir():
            messagebox.showerror(
                "Файловый менеджер",
                f"Папка не существует или недоступна:\n{path}",
            )
            return
        try:
            self.current_path = path.resolve()
        except OSError as error:
            messagebox.showerror(
                "Файловый менеджер", f"Не удалось перейти в папку:\n{error}"
            )
            return
        self.refresh()

    def go_up(self) -> None:
        parent = self.current_path.parent
        if parent != self.current_path:
            self.current_path = parent
            self.refresh()

    def browse_folder(self) -> None:
        selected = filedialog.askdirectory(
            title="Выберите папку",
            initialdir=str(self.current_path),
        )
        if selected:
            self.current_path = Path(selected)
            self.refresh()

    def _selected_path(self) -> Optional[Path]:
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo(
                "Файловый менеджер", "Сначала выберите файл или папку."
            )
            return None

        path = self._item_paths.get(selection[0])
        if path is None:
            messagebox.showerror(
                "Файловый менеджер",
                "Выбранный элемент уже недоступен. Обновите список.",
            )
        return path

    def open_selected(self, _event: Optional[tk.Event] = None) -> None:
        path = self._selected_path()
        if path is None:
            return
        if path.is_dir():
            self.current_path = path
            self.refresh()
            return

        try:
            if os.name == "nt":
                os.startfile(str(path))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except OSError as error:
            messagebox.showerror(
                "Файловый менеджер",
                f"Не удалось открыть «{path.name}»:\n{error}",
            )

    def create_folder(self) -> None:
        name = simpledialog.askstring("Новая папка", "Введите имя папки:")
        if name is None:
            return
        if not self._is_valid_name(name):
            messagebox.showerror(
                "Файловый менеджер", "Укажите допустимое имя папки."
            )
            return

        try:
            (self.current_path / name).mkdir()
        except OSError as error:
            messagebox.showerror(
                "Файловый менеджер", f"Не удалось создать папку:\n{error}"
            )
            return
        self.refresh()

    def create_file(self) -> None:
        name = simpledialog.askstring("Новый файл", "Введите имя файла:")
        if name is None:
            return
        if not self._is_valid_name(name):
            messagebox.showerror(
                "Файловый менеджер", "Укажите допустимое имя файла."
            )
            return

        try:
            (self.current_path / name).touch(exist_ok=False)
        except OSError as error:
            messagebox.showerror(
                "Файловый менеджер", f"Не удалось создать файл:\n{error}"
            )
            return
        self.refresh()

    def rename_selected(self) -> None:
        path = self._selected_path()
        if path is None:
            return

        name = simpledialog.askstring(
            "Переименование",
            "Введите новое имя:",
            initialvalue=path.name,
        )
        if name is None or name == path.name:
            return
        if not self._is_valid_name(name):
            messagebox.showerror(
                "Файловый менеджер", "Укажите допустимое имя."
            )
            return

        new_path = path.with_name(name)
        if name.casefold() != path.name.casefold() and new_path.exists():
            messagebox.showerror(
                "Файловый менеджер",
                f"Элемент с именем «{name}» уже существует.",
            )
            return

        try:
            path.rename(new_path)
        except OSError as error:
            messagebox.showerror(
                "Файловый менеджер",
                f"Не удалось переименовать «{path.name}»:\n{error}",
            )
            return
        self.refresh()

    def delete_selected(self) -> None:
        path = self._selected_path()
        if path is None:
            return

        is_directory = path.is_dir() and not path.is_symlink()
        warning = (
            " Вместе с ней будут удалены все вложенные элементы."
            if is_directory
            else ""
        )
        if not messagebox.askyesno(
            "Подтверждение удаления",
            f"Удалить «{path.name}»?{warning}\nЭто действие нельзя отменить.",
        ):
            return

        try:
            if is_directory:
                shutil.rmtree(path)
            else:
                path.unlink()
        except OSError as error:
            messagebox.showerror(
                "Файловый менеджер",
                f"Не удалось удалить «{path.name}»:\n{error}",
            )
            return
        self.refresh()


if __name__ == "__main__":
    root = tk.Tk()
    FileManager(root)
    root.mainloop()
    root.mainloop()
