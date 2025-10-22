from typing import Optional

from uiautomator2 import Device

from .selectors import Accounts, Blocks, Buttons, Items


class MainNodes:
    _instance = None
    _initialized = False

    def __new__(cls, device: Optional[Device] = None) -> "MainNodes":
        if cls._instance is None:
            if device is None:
                raise ValueError(
                    "Для первой инициализации необходимо предоставить устройство"
                )
            cls._instance = super(MainNodes, cls).__new__(cls)
        return cls._instance

    def __init__(self, device: Optional[Device] = None) -> None:
        if not MainNodes._initialized and device is not None:
            self.google_app = device(**Blocks.google_app)
            self.toolbar_container = device(**Blocks.toolbar_container)
            self.search_box = self.google_app.child(**Blocks.search_box)
            self.news_feed_box = self.google_app.child(**Blocks.news_feed_box)
            self.navigation_bar = self.google_app.child(**Blocks.navigation_bar)
            self.topbar_container = self.google_app.child(**Blocks.topbar_container)
            MainNodes._initialized = True


class ButtonNodes:
    def __init__(self, device: Device) -> None:
        self._main_nodes = MainNodes(device=device)

        self.home = self._main_nodes.navigation_bar.child(**Buttons.home)
        self.share = self._main_nodes.news_feed_box.child(**Buttons.share)
        self.more_options = self._main_nodes.news_feed_box.child(**Buttons.more_option)
        self.more_stories = self._main_nodes.news_feed_box.child(**Buttons.more_stories)
        self.share_link = self._main_nodes.toolbar_container.child(**Buttons.share_link)
        self.selected_account = self._main_nodes.topbar_container.child(
            **Buttons.selected_account
        )


class AccountNodes:
    def __init__(self, device: Device) -> None:
        self._main_nodes = MainNodes(device=device)

        self.accounts = device(**Accounts.accounts)
        self.accounts_info = device(**Accounts.accounts_info)
        self.accounts_label = device(**Accounts.accounts_label)
        self.account_management = device(**Accounts.account_management)
        self.accounts_scroll_container = device(**Accounts.accounts_scroll_container)


class ItemsNodes:
    def __init__(self, device: Device) -> None:
        self._main_nodes = MainNodes(device=device)

        self.content_preview_text = device(**Items.content_preview_text)


class Nodes:
    def __init__(self, device: Device) -> None:
        self.device = device

        self._init_nodes()

    def _init_nodes(self) -> None:
        self.blocks = MainNodes(device=self.device)
        self.items = ItemsNodes(device=self.device)
        self.buttons = ButtonNodes(device=self.device)
        self.accounts = AccountNodes(device=self.device)
