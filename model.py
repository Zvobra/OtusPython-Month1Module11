import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


class AppError(Exception):
    pass


class ContactError(AppError):
    pass


class ContactsStorageError(AppError):
    pass


class PhoneBookError(AppError):
    pass


class ContactNotFoundError(PhoneBookError):
    pass


@dataclass(frozen=True)
class Contact:
    id: int
    name: str
    phone: str
    comment: str = ""

    def __post_init__(self) -> None:
        if type(self.id) is not int or self.id <= 0:
            raise ContactError("ID контакта должен быть положительным числом")
        if not isinstance(self.name, str) or not self.name.strip():
            raise ContactError("Имя контакта должно быть непустой строкой")
        if not isinstance(self.phone, str) or not self.phone.strip():
            raise ContactError("Телефон контакта должен быть непустой строкой")
        if not isinstance(self.comment, str):
            raise ContactError("Комментарий должен быть строкой")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Any) -> "Contact":
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
    def __init__(self, contacts: list[Contact] | None = None) -> None:
        self._contacts: list[Contact] = contacts.copy() if contacts is not None else []
        self._contacts_id_idx: dict[int, int] = {}
        self._has_changes: bool = False
        self._next_contact_id: int = 1

        self._rebuild_indexes()
        self._next_contact_id = max(self._contacts_id_idx.keys(), default=0) + 1

    @property
    def has_changes(self) -> bool:
        return self._has_changes

    def mark_saved(self) -> None:
        self._has_changes = False

    def get_contact(self, contact_id: int) -> Contact:
        try:
            contact_index = self._contacts_id_idx[contact_id]
        except KeyError:
            raise ContactNotFoundError(f"Контакт с ID {contact_id} не найден")

        return self._contacts[contact_index]

    def add_contact(self, name: str, phone: str, comment: str = "") -> Contact:
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
        contact = self.get_contact(contact_id)
        contact_index = self._contacts_id_idx[contact.id]

        del self._contacts[contact_index]
        self._has_changes = True
        self._rebuild_indexes()

        return contact

    def find_contacts(self, search: str) -> list[Contact]:
        search = search.strip().lower()
        found_contacts = [
            contact for contact in self._contacts
            if (search in contact.name.lower()
                or search in contact.phone.lower()
                or search in contact.comment.lower())
        ]

        return found_contacts

    def get_contacts(self) -> list[Contact]:
        return self._contacts.copy()

    def get_contacts_count(self) -> int:
        return len(self._contacts)

    def get_contacts_page(self, page: int, page_size: int) -> list[Contact]:
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

    def _rebuild_indexes(self):
        self._contacts_id_idx = {
            contact.id: index
            for index, contact in enumerate(self._contacts)
        }

        if len(self._contacts_id_idx) != len(self._contacts):
            raise PhoneBookError("Среди контактов найдены дубликаты по ID")


class ContactsStorageJSONReader:
    @classmethod
    def load(cls, path: Path) -> list[Contact]:
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
    @classmethod
    def write(cls, contacts: list[Contact], path: Path) -> None:
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
    def __init__(self) -> None:
        self._path: Path | None = None

    def set_path(self, path_str: str = "contacts.json") -> None:
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
        if self._path is None:
            raise ContactsStorageError("Путь для файла с контактами не задан")
        return self._path

    def load_contacts(self) -> list[Contact]:
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
        ContactsStorageJSONWriter.write(contacts, self.path)
