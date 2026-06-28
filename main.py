from controller import PhoneBookController
from model import PhoneBook, ContactsStorage
from view import ConsoleView


def run_app() -> None:
    storage = ContactsStorage()
    phone_book = PhoneBook()
    view = ConsoleView()

    controller = PhoneBookController(phone_book, storage, view)
    controller.run()


if __name__ == '__main__':
    try:
        run_app()
    except KeyboardInterrupt:
        pass
