"""Контроллер приложения телефонного справочника."""

import math
from typing import TypedDict, Callable

from model import PhoneBook, ContactsStorage, AppError, Contact, ContactsStorageError, ContactNotFoundError
from view import ConsoleView


class MenuAction(TypedDict):
    """Пункт меню с названием и обработчиком действия."""

    title: str
    action: Callable[[], bool]


class PhoneBookController:
    """Контроллер телефонного справочника."""

    CONTACTS_PER_PAGE: int = 10

    def __init__(
            self,
            phone_book: PhoneBook,
            storage: ContactsStorage,
            view: ConsoleView
    ) -> None:
        """
        Инициализация контроллера телефонного справочника.

        Args:
            phone_book: объект телефонного справочника.
            storage: хранилище контактов.
            view: консольное представление.
        """

        self.phone_book = phone_book
        self.storage = storage
        self.view = view

    def run(self) -> None:
        """Запуск основного цикла приложения."""

        if not self.load_contacts():
            return

        self.view.print_title("Телефонная книга")
        self.view.print_info(f"Файл контактов: {self.storage.path}")
        self.view.print_info(
            f"Загружено контактов: {self.phone_book.get_contacts_count()}"
        )

        while self._process_actions([
            {
                "title": "Показать все контакты",
                "action": self.show_all_contacts,
            },
            {
                "title": "Найти контакт",
                "action": self.search_contacts,
            },
            {
                "title": "Добавить контакт",
                "action": self.add_contact,
            },
            {
                "title": "Выбрать контакт",
                "action": self.select_contact,
            },
            {
                "title": "Сохранить",
                "action": self.save_contacts,
            },
            {
                "title": "Выход",
                "action": self.exit_app,
            },
        ]):
            pass

    def load_contacts(self) -> bool:
        """
        Загрузка контактов при старте приложения.

        Returns: удалось ли загрузить контакты.
        """

        path = self.view.input_contacts_path("contacts.json")
        if not path:
            path = "contacts.json"

        try:
            self.storage.set_path(path)
        except ContactsStorageError as err:
            self.view.print_error(f"Ошибка определения файла контактов: {str(err)}")
            return False

        try:
            contacts = self.storage.load_contacts()
        except ContactsStorageError as err:
            self.view.print_error(f"Ошибка загрузки контактов: {str(err)}")
            return False

        self.phone_book = PhoneBook(contacts)
        return True

    def exit_app(self) -> bool:
        """
        Выход из приложения.

        Returns: нужно ли продолжать основной цикл приложения.
        """

        if not self.phone_book.has_changes:
            return False

        self.view.print_warning("Есть несохраненные изменения")
        is_save = self.view.input_yes_no("Сохранить перед выходом?")

        if is_save:
            return self.save_contacts(is_exit=True)

        return False

    def show_all_contacts(self) -> bool:
        """
        Отображение всех контактов с постраничной навигацией.

        Returns: нужно ли продолжать основной цикл приложения.
        """

        current_page = 1
        page_size = self.CONTACTS_PER_PAGE

        def next_page() -> bool:
            """
            Переход на следующую страницу.

            Returns: нужно ли продолжать просмотр списка контактов.
            """

            nonlocal current_page

            if current_page == pages_count:
                return True

            current_page += 1
            return True

        def previous_page() -> bool:
            """
            Переход на предыдущую страницу.

            Returns: нужно ли продолжать просмотр списка контактов.
            """

            nonlocal current_page

            if current_page == 1:
                return True

            current_page -= 1
            return True

        def select_page() -> bool:
            """
            Выбор страницы списка контактов.

            Returns: нужно ли продолжать просмотр списка контактов.
            """

            nonlocal current_page

            selected_page = self.view.input_page_number(
                1, pages_count
            )
            if selected_page is not None:
                current_page = selected_page

            return True

        is_showing = True
        while is_showing:
            self.view.print_title("Список контактов")

            contacts_count = self.phone_book.get_contacts_count()

            if not contacts_count:
                self.view.print_info("Список контактов пуст")
                break

            pages_count = max(
                1, int(math.ceil(contacts_count / page_size))
            )
            current_page = min(current_page, pages_count)

            contacts_on_page = self.phone_book.get_contacts_page(
                current_page, page_size
            )

            self.view.print_contacts([
                [contact.id, contact.name, contact.phone, contact.comment]
                for contact in contacts_on_page
            ])
            self.view.print_info(f"Всего контактов: {contacts_count}")
            self.view.print_info(f"Страница {current_page} из {pages_count}")

            is_showing = self._process_actions([
                {
                    "title": "Следующая страница",
                    "action": next_page,
                },
                {
                    "title": "Предыдущая страница",
                    "action": previous_page,
                },
                {
                    "title": "Выбор страницы",
                    "action": select_page,
                },
                {
                    "title": "Выбор контакта",
                    "action": lambda: self.select_contact(contacts_on_page),
                },
                {
                    "title": "Назад",
                    "action": lambda: False
                },
            ])

        return True

    def search_contacts(self) -> bool:
        """
        Поиск контактов по введенному запросу.

        Returns: нужно ли продолжать основной цикл приложения.
        """

        self.view.print_title("Поиск контактов")

        search = self.view.input_search_query()
        found_contacts = self.phone_book.find_contacts(search)

        if not found_contacts:
            self.view.print_info("Ничего не найдено")
            return True

        is_searching = True
        while is_searching:
            self.view.print_contacts([
                [contact.id, contact.name, contact.phone, contact.comment]
                for contact in found_contacts
            ])
            self.view.print_info(f"Найдено контактов: {len(found_contacts)}")

            is_searching = self._process_actions([
                {
                    "title": "Выбор контакта",
                    "action": lambda: self.select_contact(found_contacts),
                },
                {
                    "title": "Назад",
                    "action": lambda: False
                },
            ])

        return True

    def add_contact(self) -> bool:
        """
        Добавление нового контакта.

        Returns: нужно ли продолжать основной цикл приложения.
        """

        self.view.print_title("Добавление контакта")
        contact_data = self.view.input_contact_data()

        try:
            new_contact = self.phone_book.add_contact(
                name=contact_data["name"],
                phone=contact_data["phone"],
                comment=contact_data["comment"],
            )
        except AppError as err:
            self.view.print_error(f"Не удалось добавить контакт: {err}")
            return True

        self.view.print_success("Контакт добавлен:")
        self.view.print_contact([
            new_contact.id,
            new_contact.name,
            new_contact.phone,
            new_contact.comment,
        ])

        return True

    def select_contact(self, visible_contacts: list[Contact] | None = None) -> bool:
        """
        Выбор контакта для просмотра, редактирования или удаления.

        Args:
            visible_contacts: список контактов, доступных для выбора.

        Returns: нужно ли продолжать основной цикл приложения.
        """

        input_contact_id = self.view.input_contact_id()
        if input_contact_id is None:
            return True

        contact_id = input_contact_id

        if visible_contacts is None:
            visible_contacts = self.phone_book.get_contacts()

        try:
            contact = self.phone_book.get_contact(contact_id)
        except ContactNotFoundError as err:
            self.view.print_error(str(err))
            return True

        if visible_contacts is not None:
            available_contact_ids = {contact.id for contact in visible_contacts}
            if contact_id not in available_contact_ids:
                self.view.print_error(
                    f"Контакт с ID {contact_id} не найден в текущем списке"
                )
                return True

        def edit_contact() -> bool:
            """
            Редактирование выбранного контакта.

            Returns: нужно ли продолжать работу с выбранным контактом.
            """

            nonlocal contact
            contact_name: str | None = None
            contact_phone: str | None = None
            contact_comment: str | None = None

            def edit_contact_name() -> bool:
                """
                Редактирование имени контакта.

                Returns: нужно ли продолжать редактирование контакта.
                """

                nonlocal contact_name
                contact_name = self.view.input_field("Имя")
                return True

            def edit_contact_phone() -> bool:
                """
                Редактирование телефона контакта.

                Returns: нужно ли продолжать редактирование контакта.
                """

                nonlocal contact_phone
                contact_phone = self.view.input_field("Телефон")
                return True

            def edit_contact_comment() -> bool:
                """
                Редактирование комментария контакта.

                Returns: нужно ли продолжать редактирование контакта.
                """

                nonlocal contact_comment
                contact_comment = self.view.input_field("Комментарий")
                return True

            is_editing = True
            while is_editing:
                is_editing = self._process_actions([
                    {
                        "title": "Редактировать \"Имя\"",
                        "action": edit_contact_name,
                    },
                    {
                        "title": "Редактировать \"Телефон\"",
                        "action": edit_contact_phone,
                    },
                    {
                        "title": "Редактировать \"Комментарий\"",
                        "action": edit_contact_comment,
                    },
                    {
                        "title": "Назад",
                        "action": lambda: False
                    },
                ])

            contact = self.phone_book.update_contact(
                contact_id=contact_id,
                name=contact_name,
                phone=contact_phone,
                comment=contact_comment
            )

            return True

        def delete_contact() -> bool:
            """
            Удаление выбранного контакта.

            Returns: нужно ли продолжать работу с выбранным контактом.
            """

            self.phone_book.delete_contact(contact_id)
            if visible_contacts is not None:
                visible_contacts.remove(contact)

            self.view.print_success("Контакт удален")

            return False

        is_selected = True
        while is_selected:
            self.view.print_title("Выбран контакт:")
            self.view.print_contact([
                contact.id,
                contact.name,
                contact.phone,
                contact.comment,
            ])

            is_selected = self._process_actions([
                {
                    "title": "Редактировать",
                    "action": edit_contact,
                },
                {
                    "title": "Удалить",
                    "action": delete_contact,
                },
                {
                    "title": "Назад",
                    "action": lambda: False
                },
            ])

        return True

    def save_contacts(self, is_exit: bool = False) -> bool:
        """
        Сохранение контактов в хранилище.

        Args:
            is_exit: выполняется ли сохранение перед выходом из приложения.

        Returns: нужно ли продолжать основной цикл приложения.
        """

        try:
            self.storage.save_contacts(self.phone_book.get_contacts())
        except ContactsStorageError as err:
            self.view.print_info(f"Ошибка сохранения контактов: {str(err)}")
            return True

        self.phone_book.mark_saved()
        self.view.print_success(f"Контакты сохранены в файл: {self.storage.path}")
        return not is_exit

    def _process_actions(self, actions: list[MenuAction]) -> bool:
        """
        Обработка выбранного пункта меню.

        Args:
            actions: список доступных действий меню.

        Returns: нужно ли продолжать текущий цикл меню.
        """

        item = self.view.choose_menu_item(
            [action["title"] for action in actions],
        )

        if item is None:
            return True

        try:
            return actions[item]["action"]()
        except AppError as err:
            self.view.print_error(str(err))
            return True
