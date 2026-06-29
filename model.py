"""Модели и хранилище данных телефонного справочника."""

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


class AppError(Exception):
    """Базовое исключение приложения."""

    pass


class ContactError(AppError):
    """Исключение для ошибок в данных контакта."""

    pass


class ContactsStorageError(AppError):
    """Исключение для ошибок хранилища контактов."""

    pass


class PhoneBookError(AppError):
    """Исключение для ошибок телефонного справочника."""

    pass


class ContactNotFoundError(PhoneBookError):
    """Исключение для ситуации, когда контакт не найден."""

    pass


@dataclass(frozen=True)
class Contact:
    """Контакт телефонного справочника."""

    id: int
    name: str
    phone: str
    comment: str = ""

    def __post_init__(self) -> None:
        """Валидация данных контакта."""

        if type(self.id) is not int or self.id <= 0:
            raise ContactError("ID контакта должен быть положительным числом")
        if not isinstance(self.name, str) or not self.name.strip():
            raise ContactError("Имя контакта должно быть непустой строкой")
        if not isinstance(self.phone, str) or not self.phone.strip():
            raise ContactError("Телефон контакта должен быть непустой строкой")
        if not isinstance(self.comment, str):
            raise ContactError("Комментарий должен быть строкой")

    def to_dict(self) -> dict[str, Any]:
        """
        Преобразование контакта в словарь.

        Returns: словарь с данными контакта.
        """

        return asdict(self)

    @classmethod
    def from_dict(cls, data: Any) -> "Contact":
        """
        Создание контакта из словаря.

        Args:
            data: словарь с данными контакта.

        Returns: объект контакта.
        """

        if not isinstance(data, dict):
            raise ContactError("Контакт должен быть объектом JSON")

        required_fields = ("name", "phone", "id")
        for field in required_fields:
            if field not in data:
                raise ContactError(f"В контакте отсутствует поле: {field}")

        return cls(
            id=data["id"],
            name=data["name"],
            phone=data["phone"],
            comment=data.get("comment", ""),
        )


class PhoneBook:
    """Телефонный справочник с операциями над коллекцией контактов."""

    def __init__(self, contacts: list[Contact] | None = None) -> None:
        """
        Инициализация телефонного справочника.

        Args:
            contacts: список контактов.
        """
        self._contacts: list[Contact] = contacts.copy() if contacts is not None else []
        self._contacts_id_idx: dict[int, int] = {}
        self._has_changes: bool = False
        self._next_contact_id: int = 1

        self._rebuild_indexes()
        self._next_contact_id = max(self._contacts_id_idx.keys(), default=0) + 1

    @property
    def has_changes(self) -> bool:
        """
        Признак несохраненных изменений.

        Returns: были ли изменения в справочнике.
        """

        return self._has_changes

    def mark_saved(self) -> None:
        """Сброс признака несохраненных изменений."""

        self._has_changes = False

    def get_contact(self, contact_id: int) -> Contact:
        """
        Получение контакта по ID.

        Args:
            contact_id: ID контакта.

        Returns: контакт.

        Raises:
            ContactNotFoundError: если контакт не найден.
        """

        try:
            contact_index = self._contacts_id_idx[contact_id]
        except KeyError:
            raise ContactNotFoundError(f"Контакт с ID {contact_id} не найден")

        return self._contacts[contact_index]

    def add_contact(self, name: str, phone: str, comment: str = "") -> Contact:
        """
        Добавление нового контакта.

        Args:
            name: наименование контакта.
            phone: телефон контакта.
            comment: комментарий.

        Returns: добавленный контакт.
        """

        contact = Contact(
            id=self._next_contact_id,
            name=name,
            phone=phone,
            comment=comment,
        )

        self._contacts.append(contact)
        self._contacts_id_idx[contact.id] = len(self._contacts) - 1
        self._has_changes = True
        self._next_contact_id += 1

        return contact

    def update_contact(
            self,
            contact_id: int,
            name: str | None = None,
            phone: str | None = None,
            comment: str | None = None,
    ) -> Contact:
        """
        Обновление контакта.

        Args:
            contact_id: ID контакта.
            name: наименование контакта.
            phone: телефон контакта.
            comment: комментарий.

        Returns: обновленный контакт.

        Raises:
            ContactNotFoundError: если контакт не найден.
        """

        contact = self.get_contact(contact_id)

        # Инспекция почему-то ломается и думает, что contact.name может быть
        # None (аналогично и для других полей).

        # noinspection PyTypeChecker
        new_name: str = contact.name if name is None else name
        # noinspection PyTypeChecker
        new_phone: str = contact.phone if phone is None else phone
        # noinspection PyTypeChecker
        new_comment: str = contact.comment if comment is None else comment

        updated_contact = Contact(
            id=contact.id,
            name=new_name,
            phone=new_phone,
            comment=new_comment,
        )

        if contact != updated_contact:
            contact_index = self._contacts_id_idx[contact.id]
            self._contacts[contact_index] = updated_contact
            self._has_changes = True

        return updated_contact

    def delete_contact(self, contact_id: int) -> Contact:
        """
        Удаление контакта.

        Args:
            contact_id: ID контакта.

        Returns: удаленный контакт.

        Raises:
            ContactNotFoundError: если контакт не найден.
        """

        contact = self.get_contact(contact_id)
        contact_index = self._contacts_id_idx[contact.id]

        del self._contacts[contact_index]
        self._has_changes = True
        self._rebuild_indexes()

        return contact

    def find_contacts(self, search: str) -> list[Contact]:
        """
        Поиск контактов.

        Args:
            search: текст поиска.

        Returns: список найденных контактов.
        """

        search = search.strip().lower()
        found_contacts = [
            contact for contact in self._contacts
            if (search in contact.name.lower()
                or search in contact.phone.lower()
                or search in contact.comment.lower())
        ]

        return found_contacts

    def get_contacts(self) -> list[Contact]:
        """
        Получение списка всех контактов.

        Returns: список контактов.
        """

        return self._contacts.copy()

    def get_contacts_count(self) -> int:
        """
        Получение количества контактов.

        Returns: количество контактов.
        """

        return len(self._contacts)

    def get_contacts_page(self, page: int, page_size: int) -> list[Contact]:
        """
        Постраничное получение списка контактов.

        Args:
            page: номер страницы.
            page_size: количество контактов на странице.

        Returns: список контактов на странице.

        Raises:
            PhoneBookError: если указаны некорректные page или page_size.
        """

        if page <= 0:
            raise PhoneBookError(
                "Номер страницы должен быть положительным числом"
            )

        if page_size <= 0:
            raise PhoneBookError(
                "Размер страницы должен быть положительным числом"
            )

        start = (page - 1) * page_size
        end = start + page_size

        return self._contacts[start:end]

    def _rebuild_indexes(self) -> None:
        """Перестроение индекса контактов."""

        self._contacts_id_idx = {
            contact.id: index
            for index, contact in enumerate(self._contacts)
        }

        if len(self._contacts_id_idx) != len(self._contacts):
            raise PhoneBookError("Среди контактов найдены дубликаты по ID")


class ContactsStorageJSONReader:
    """Чтение контактов из JSON-файла."""

    @classmethod
    def load(cls, path: Path) -> list[Contact]:
        """
        Загрузка контактов из JSON-файла.

        Args:
            path: путь к JSON-файлу контактов.

        Returns: список контактов.

        Raises:
            ContactsStorageError: при ошибках чтения и декодирования контактов.
        """

        try:
            with path.open("r", encoding="utf-8") as file:
                contacts = json.load(file)
        except OSError:
            raise ContactsStorageError(
                f"Ошибка при чтении файла: {path}"
            )
        except json.JSONDecodeError:
            raise ContactsStorageError(
                f"Ошибка декодирования JSON файла: {path}"
            )

        if not isinstance(contacts, list):
            raise ContactsStorageError(
                f"Некорректный формат файла контактов: {path}"
            )

        try:
            contacts = [Contact.from_dict(contact) for contact in contacts]
        except ContactError as err:
            raise ContactsStorageError(
                f"Некорректные данные контакта: {err}"
            )
        return contacts


class ContactsStorageJSONWriter:
    """Сохранение контактов в JSON-файл."""

    @classmethod
    def write(cls, contacts: list[Contact], path: Path) -> None:
        """
        Сохранение контактов в JSON-файл.

        Args:
            contacts: список контактов.
            path: путь к JSON-файлу.

        Raises:
            ContactsStorageError: при ошибке сохранения файла.
        """

        temp_contacts_path = path.with_suffix(f"{path.suffix}.tmp")
        contacts = [contact.to_dict() for contact in contacts]

        try:
            with temp_contacts_path.open("w", encoding="utf-8") as file:
                json.dump(contacts, file, ensure_ascii=False, indent=2)
            temp_contacts_path.replace(path)
        except OSError:
            raise ContactsStorageError(
                f"Ошибка при сохранении файла: {path}"
            )


class ContactsStorage:
    """Фасад для работы с файлом контактов."""

    def __init__(self) -> None:
        """Инициализация хранилища контактов."""

        self._path: Path | None = None

    def set_path(self, path_str: str = "contacts.json") -> None:
        """
        Установка пути к файлу контактов.

        Args:
            path_str: путь до файла контактов.

        Raises:
            ContactsStorageError: при некорректном расширении файла контактов.
        """

        path = Path(path_str)

        if path.suffix and path.suffix != ".json":
            raise ContactsStorageError(
                "Некорректное расширение файла. "
                f"Ожидается .json, получено {path.suffix}"
            )
        elif not path.suffix:
            path = path.with_suffix(".json")

        self._path = path

    @property
    def path(self) -> Path:
        """
        Путь к файлу контактов.

        Returns: путь к файлу контактов.

        Raises:
            ContactsStorageError: если путь не задан.
        """

        if self._path is None:
            raise ContactsStorageError("Путь для файла с контактами не задан")
        return self._path

    def load_contacts(self) -> list[Contact]:
        """
        Загрузка контактов из хранилища.

        Returns: список контактов.

        Raises:
            ContactsStorageError: если не задан путь или не удалось загрузить
            контакты.
        """

        if not self.path.exists():
            try:
                self.path.parent.mkdir(parents=True, exist_ok=True)
            except OSError:
                raise ContactsStorageError(
                    f"Ошибка при создании файла: {self.path}"
                )

            ContactsStorageJSONWriter.write([], self.path)
            return []

        return ContactsStorageJSONReader.load(self.path)

    def save_contacts(self, contacts: list[Contact]) -> None:
        """
        Сохранение контактов в хранилище.

        Args:
            contacts: список контактов.

        Raises:
            ContactsStorageError: если не задан путь или не удалось сохранить
                контакты.
        """

        ContactsStorageJSONWriter.write(contacts, self.path)
