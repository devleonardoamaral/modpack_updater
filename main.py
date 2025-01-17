import sys


def main(argv):
    from app.app import App

    App.get_instance().root.mainloop()


if __name__ == "__main__":
    main(sys.argv)
