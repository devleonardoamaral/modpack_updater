# import sys


def main():
    from .app import App

    App.get_instance().root.mainloop()


if __name__ == "__main__":
    main()
