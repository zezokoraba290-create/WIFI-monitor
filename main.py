import flet as ft

from gui.app import create_app


def main(page: ft.Page):

    create_app(page)


if __name__ == "__main__":

    ft.app(
        target=main
    )
