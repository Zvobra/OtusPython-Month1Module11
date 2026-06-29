"""Консольное представление телефонного справочника."""

import textwrap
from typing import Any, Iterable, Sequence


class ConsoleView:
    """Консольное представление телефонного справочника."""

    YES_ANSWERS: set[str] = {"1", "y", "yes", "д", "да", "true", "t"}
    NO_ANSWERS: set[str] = {"0", "n", "no", "н", "нет", "false", "f"}
    TABLE_PADDING: int = 2
    TABLE_COLUMN_MAX_WIDTH: int = 32
    BOLD_START: str = "\033[1m"
    BOLD_RESET: str = "\033[0m"

    @classmethod
    def print_blank_line(cls) -> None:
        """Вывод пустой строки."""

        print()

    @classmethod
    def print_title(cls, title: str) -> None:
        """
        Вывод заголовка.

        Args:
            title: текст заголовка.
        """

        border = "=" * (len(title) + 4)
        cls.print_blank_line()
        print(border)
        print(f"  {title}")
        print(border)

    @classmethod
    def print_section(cls, title: str) -> None:
        """
        Вывод названия секции.

        Args:
            title: название секции.
        """

        cls.print_blank_line()
        print(title)
        print("-" * len(title))

    @classmethod
    def print_success(cls, message: str) -> None:
        """
        Вывод сообщения об успехе.

        Args:
            message: текст сообщения.
        """

        print(f"[OK] {message}")

    @classmethod
    def print_warning(cls, message: str) -> None:
        """
        Вывод предупреждения.

        Args:
            message: текст предупреждения.
        """

        print(f"[!] {message}")

    @classmethod
    def print_error(cls, message: str) -> None:
        """
        Вывод сообщения об ошибке.

        Args:
            message: текст ошибки.
        """

        print(f"[Ошибка] {message}")

    @classmethod
    def print_info(cls, message: str) -> None:
        """
        Вывод информационного сообщения.

        Args:
            message: текст сообщения.
        """

        print(f"[i] {message}")

    @classmethod
    def format_cell(cls, value: Any, width: int) -> str:
        """
        Форматирование ячейки таблицы.

        Args:
            value: значение ячейки.
            width: ширина ячейки.

        Returns: отформатированная ячейка.
        """

        text = str(value)
        return f" {text:<{width}} "

    @classmethod
    def format_bold_cell(cls, value: Any, width: int) -> str:
        """
        Форматирование ячейки таблицы в полужирном стиле.

        Args:
            value: значение ячейки.
            width: ширина ячейки.

        Returns: отформатированная ячейка.
        """

        text = str(value)
        return f" {cls.BOLD_START}{text:<{width}}{cls.BOLD_RESET} "

    @classmethod
    def wrap_cell(cls, value: Any, width: int) -> list[str]:
        """
        Перенос текста в ячейке таблицы.

        Args:
            value: значение ячейки.
            width: ширина ячейки.

        Returns: список строк ячейки.
        """

        text = str(value)
        lines = textwrap.wrap(
            text,
            width=width,
            break_long_words=True,
            break_on_hyphens=False,
        )

        return lines or [""]

    @classmethod
    def print_table(cls, headers: list[str], rows: list[list[Any]]) -> None:
        """
        Вывод таблицы.

        Args:
            headers: заголовки таблицы.
            rows: строки таблицы.
        """

        columns_width = [len(header) for header in headers]

        for row in rows:
            for index, value in enumerate(row[:len(headers)]):
                columns_width[index] = max(columns_width[index], len(str(value)))

        columns_width = [
            min(width, max(cls.TABLE_COLUMN_MAX_WIDTH, len(headers[index])))
            for index, width in enumerate(columns_width)
        ]

        separator = "+".join(
            "-" * (width + cls.TABLE_PADDING)
            for width in columns_width
        )
        border = f"+{separator}+"

        print(border)
        print(
            "|"
            + "|".join(
                cls.format_bold_cell(header, columns_width[index])
                for index, header in enumerate(headers)
            )
            + "|"
        )
        print(border)

        for row in rows:
            wrapped_cells = [
                cls.wrap_cell(
                    row[index] if index < len(row) else "",
                    columns_width[index],
                )
                for index in range(len(headers))
            ]
            row_height = max((len(cell) for cell in wrapped_cells), default=0)

            for line_index in range(row_height):
                print(
                    "|"
                    + "|".join(
                        cls.format_cell(
                            cell[line_index] if line_index < len(cell) else "",
                            columns_width[index],
                        )
                        for index, cell in enumerate(wrapped_cells)
                    )
                    + "|"
                )
            print(border)

    @classmethod
    def print_contact(cls, row: Sequence[Any]) -> None:
        """
        Вывод одного контакта.

        Args:
            row: данные контакта.
        """

        cls.print_table(
            ["ID", "Имя", "Телефон", "Комментарий"],
            [list(row)],
        )

    @classmethod
    def print_contacts(cls, rows: Iterable[Sequence[Any]]) -> None:
        """
        Вывод списка контактов.

        Args:
            rows: список строк с данными контактов.
        """

        rows = [list(row) for row in rows]
        if not rows:
            cls.print_info("Список контактов пуст")
            return

        cls.print_table(["ID", "Имя", "Телефон", "Комментарий"], rows)

    @classmethod
    def input_yes_no(cls, question: str) -> bool:
        """
        Ввод ответа да/нет.

        Args:
            question: текст вопроса.

        Returns: выбранный пользователем ответ.
        """

        answer: bool | None = None
        while answer is None:
            answer_input = input(f"{question} (да/нет): ")
            answer_input = answer_input.strip().lower()

            if answer_input in cls.YES_ANSWERS:
                answer = True
            elif answer_input in cls.NO_ANSWERS:
                answer = False
            else:
                cls.print_error("Введите да или нет")

        return answer

    @classmethod
    def choose_menu_item(cls, items: list[str]) -> int | None:
        """
        Выбор пункта меню.

        Args:
            items: список пунктов меню.

        Returns: индекс выбранного пункта или None при ошибке ввода.
        """

        cls.print_section("Доступные действия")

        for number, item in enumerate(items, start=1):
            print(f"  {number}. {item}")

        value = input(
            f"\nВыберите действие [1-{len(items)}]: "
        ).strip()

        if not value.isdigit():
            cls.print_error("Необходимо ввести номер действия.")
            return None

        index = int(value) - 1
        if index not in range(0, len(items)):
            cls.print_error("Такого действия не существует.")
            return None

        return index

    @classmethod
    def input_page_number(cls, number_from: int, number_to: int) -> int | None:
        """
        Ввод номера страницы.

        Args:
            number_from: минимальный номер страницы.
            number_to: максимальный номер страницы.

        Returns: номер страницы или None при ошибке ввода.
        """

        number_input = input(
            f"Введите номер страницы [{number_from}-{number_to}]: "
        ).strip()

        if not number_input.isdigit():
            cls.print_error("Необходимо ввести номер страницы")
            return None

        number = int(number_input)
        if number not in range(number_from, number_to + 1):
            cls.print_error("Такой страницы не существует")
            return None

        return number

    @classmethod
    def input_contact_id(cls) -> int | None:
        """
        Ввод ID контакта.

        Returns: ID контакта или None при ошибке ввода.
        """

        contact_id_input = input("ID: ").strip()

        if not contact_id_input.isdigit():
            cls.print_error("ID контакта должен быть положительным числом")
            return None

        contact_id = int(contact_id_input)
        if contact_id <= 0:
            cls.print_error("ID контакта должен быть положительным числом")
            return None

        return contact_id

    @classmethod
    def input_contact_data(cls) -> dict[str, str]:
        """
        Ввод данных контакта.

        Returns: словарь с данными контакта.
        """

        name = input("Имя: ").strip()
        phone = input("Телефон: ").strip()
        comment = input("Комментарий: ").strip()

        return {
            "name": name,
            "phone": phone,
            "comment": comment,
        }

    @classmethod
    def input_field(cls, field: str) -> str:
        """
        Ввод значения поля.

        Args:
            field: название поля.

        Returns: введенное значение.
        """

        return input(f"{field}: ").strip()

    @classmethod
    def input_search_query(cls) -> str:
        """
        Ввод поискового запроса.

        Returns: поисковый запрос.
        """

        return input("Поиск: ").strip().lower()

    @classmethod
    def input_contacts_path(cls, default_path: str) -> str:
        """
        Ввод пути к файлу контактов.

        Args:
            default_path: путь по умолчанию.

        Returns: введенный путь к файлу контактов.
        """

        return input(
            f"Файл контактов [{default_path}]: "
        ).strip()
