from __future__ import annotations
import webbrowser
import shutil
from pathlib import Path

from kivy.uix.anchorlayout import AnchorLayout
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.textinput import TextInput
from kivy.core.clipboard import Clipboard
from kivy.uix.checkbox import CheckBox
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.utils import platform
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.filechooser import FileChooserListView

from core.contacts import ContactsStore
from core.crypto_utils import CryptoManager
from core.storage import (
    CONTACTS_FILE,
    MY_PRIVATE_KEY_FILE,
    MY_PUBLIC_KEY_FILE,
    ensure_app_dirs,
)


class MainScreen(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.private_key = None
        self.public_key = None

        ensure_app_dirs()
        self.contacts = ContactsStore(CONTACTS_FILE)

        self.is_android = platform == "android"

        self.main_container = BoxLayout(orientation="vertical")
        self.add_widget(self.main_container)

        if self.is_android:
            self._build_top_bar()
            self._build_tabs_android()
            self._build_side_menu()
        else:
            self._build_tabs_desktop()

        self._build_identity_tab()
        self._build_sign_tab()
        self._build_verify_tab()
        self._build_contacts_tab()
        self._build_import_export_tab()
        self._refresh_contacts_spinner()
        self._load_existing_keys_if_possible()

        Clock.schedule_once(lambda dt: self.show_about_popup(), 0.2)
    
    #---------------------------------
    #------------- OS TABS -----------
    #---------------------------------
    
    def _build_tabs_android(self):
        self.tabs = TabbedPanel(do_default_tab=False)
        self.tabs.tab_pos = "bottom_mid"
        self.tabs.tab_height = dp(56)
        self.tabs.bind(size=self._update_android_tab_widths)
        self._update_android_tab_widths()
        self.main_container.add_widget(self.tabs)

    def _build_tabs_desktop(self):
        self.tabs = TabbedPanel(do_default_tab=False)
        self.tabs.tab_pos = "top_mid"
        self.main_container.add_widget(self.tabs)
        
    #------------ END OS TABS ---------------------
    
    def _build_side_menu(self):
        self.menu_overlay = Button(
            background_normal="",
            background_color=(0, 0, 0, 0),
            size_hint=(None, None),
            size=(0, 0),
            pos=(-1000, -1000),
            opacity=0,
        )
        self.menu_overlay.bind(on_release=lambda _x: self.close_side_menu())
        self.add_widget(self.menu_overlay)

        self.side_menu = BoxLayout(
            orientation="vertical",
            size_hint=(None, 1),
            width=dp(260),
            pos=(-dp(260), 0),
            padding=dp(16),
            spacing=dp(12),
        )

        with self.side_menu.canvas.before:
            Color(0.12, 0.12, 0.12, 1)
            self._side_menu_rect = Rectangle(pos=self.side_menu.pos, size=self.side_menu.size)

        self.side_menu.bind(pos=self._update_side_menu_rect, size=self._update_side_menu_rect)

        header = Label(
            text="Eliptic Signer",
            color=(1, 1, 1, 1),
            bold=True,
            font_size="22sp",
            size_hint_y=None,
            height=dp(50),
            halign="left",
            valign="middle",
        )
        header.bind(size=lambda instance, value: setattr(instance, "text_size", value))

        btn_identity = Button(text="Identity", size_hint_y=None, height=dp(48))
        btn_sign = Button(text="Sign", size_hint_y=None, height=dp(48))
        btn_verify = Button(text="Verify", size_hint_y=None, height=dp(48))
        btn_contacts = Button(text="Contacts", size_hint_y=None, height=dp(48))

        spacer = Widget()

        btn_about = Button(text="About", size_hint_y=None, height=dp(48))
        btn_close = Button(text="Close", size_hint_y=None, height=dp(48))
        btn_import_export = Button(text="Import / Export Keys", size_hint_y=None, height=dp(48))

        btn_identity.bind(on_release=lambda _x: self._switch_tab_from_menu("Identity"))
        btn_sign.bind(on_release=lambda _x: self._switch_tab_from_menu("Sign"))
        btn_verify.bind(on_release=lambda _x: self._switch_tab_from_menu("Verify"))
        btn_contacts.bind(on_release=lambda _x: self._switch_tab_from_menu("Contacts"))

        btn_import_export.bind(on_release=lambda _x: self._switch_tab_from_menu("Import/Export"))

        btn_about.bind(on_release=lambda _x: self._open_about_from_side_menu())
        btn_close.bind(on_release=lambda _x: self._close_app())

        self.side_menu.add_widget(header)
        self.side_menu.add_widget(btn_identity)
        self.side_menu.add_widget(btn_sign)
        self.side_menu.add_widget(btn_verify)
        self.side_menu.add_widget(btn_contacts)
        self.side_menu.add_widget(btn_import_export)
        self.side_menu.add_widget(spacer)
        self.side_menu.add_widget(btn_about)
        self.side_menu.add_widget(btn_close)

        self.add_widget(self.side_menu)
    
    def _update_side_menu_rect(self, instance, _value):
        self._side_menu_rect.pos = instance.pos
        self._side_menu_rect.size = instance.size
    
    def open_hamburger_menu(self, _instance):
        if not self.is_android:
            return

        self.menu_overlay.size = self.size
        self.menu_overlay.pos = self.pos
        self.menu_overlay.opacity = 1
        self.menu_overlay.background_color = (0, 0, 0, 0.35)

        Animation.cancel_all(self.side_menu)
        Animation(x=0, d=0.2).start(self.side_menu)

    def close_side_menu(self):
        if not self.is_android:
            return

        self.menu_overlay.opacity = 0
        self.menu_overlay.background_color = (0, 0, 0, 0)
        self.menu_overlay.size = (0, 0)
        self.menu_overlay.pos = (-1000, -1000)

        Animation.cancel_all(self.side_menu)
        Animation(x=-self.side_menu.width, d=0.2).start(self.side_menu)

    def _switch_tab_from_menu(self, tab_name):
        self._switch_tab(tab_name)
        self.close_side_menu()

    def _open_about_from_side_menu(self):
        self.close_side_menu()
        Clock.schedule_once(lambda dt: self.show_about_popup(), 0.22)

    def _open_import_from_side_menu(self):
        self._switch_tab_from_menu("Import/Export")

    def _open_export_from_side_menu(self):
        self._switch_tab_from_menu("Import/Export")

    def _close_app(self):
        from kivy.app import App
        App.get_running_app().stop()


    
    def _popup(self, title: str, message: str) -> None:
        outer = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(12))

        scroll = ScrollView(size_hint=(1, 1))

        msg = Label(
            text=message,
            halign="left",
            valign="top",
            size_hint_y=None,
        )
        msg.bind(
            width=lambda instance, value: setattr(instance, "text_size", (value, None))
        )
        msg.bind(
            texture_size=lambda instance, value: setattr(instance, "height", value[1])
        )

        scroll.add_widget(msg)

        btn = Button(text="OK", size_hint_y=None, height=dp(44))

        outer.add_widget(scroll)
        outer.add_widget(btn)

        popup = Popup(
            title=title,
            content=outer,
            size_hint=(0.88, 0.5),
            auto_dismiss=False,
        )

        btn.bind(on_release=popup.dismiss)
        popup.open()

    def _load_existing_keys_if_possible(self):
        if MY_PRIVATE_KEY_FILE.exists():
            self.status_label.text = "Private key found on disk. Use Load Private Key."
        else:
            self.status_label.text = "No private key loaded. Generate one to start."


    def _build_identity_tab(self):
        tab = TabbedPanelItem(text="Identity")

        page = BoxLayout(orientation="vertical", padding=0, spacing=dp(6))

        scroll = ScrollView()
        layout = BoxLayout(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(10),
            size_hint_y=None,
        )
        layout.bind(minimum_height=layout.setter("height"))
        
        if self.is_android:
            layout.add_widget(self._android_tab_header("Identity"))
        
        self.password_input = TextInput(
            hint_text="Password to protect private key (optional)",
            multiline=False,
            password=True,
            size_hint_y=None,
            height=dp(40),
        )

        self.show_password_checkbox = CheckBox(
            active=False,
            size_hint=(None, None),
            size=(dp(40), dp(40)),
        )
        self.show_password_checkbox.bind(active=self.on_toggle_password_visibility)

        label = Label(
            text="Show password",
            size_hint_x=None,
            width=dp(150),
            halign="left",
            valign="middle",
        )
        label.bind(size=lambda instance, value: setattr(instance, "text_size", value))

        password_box = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(40),
            spacing=dp(10),
        )
        password_box.add_widget(self.show_password_checkbox)
        password_box.add_widget(label)

        self.public_key_output = TextInput(
            readonly=True,
            size_hint_y=None,
            height=dp(50),
        )

        self.status_label = Label(
            text="",
            size_hint_y=None,
            height=dp(40),
        )

        lbl_key_mgmt = Label(
            text="Key Management:",
            size_hint_y=None,
            height=dp(30),
            halign="left",
            valign="middle",
        )
        lbl_key_mgmt.bind(size=lambda instance, value: setattr(instance, "text_size", value))

        btn_generate = Button(
            text="Generate new Ed25519 key",
            size_hint_y=None,
            height=dp(48),
        )
        btn_save = Button(
            text="Save private/public key",
            size_hint_y=None,
            height=dp(48),
        )
        btn_load = Button(
            text="Load private key",
            size_hint_y=None,
            height=dp(48),
        )
        btn_copy_pub = Button(
            text="Copy public key",
            size_hint_y=None,
            height=dp(40),
        )

        btn_generate.bind(on_release=self.on_generate_key)
        btn_save.bind(on_release=self.on_save_key)
        btn_load.bind(on_release=self.on_load_key)
        btn_copy_pub.bind(on_release=self.on_copy_public_key)

        layout.add_widget(lbl_key_mgmt)
        layout.add_widget(btn_generate)
        layout.add_widget(btn_save)
        layout.add_widget(btn_load)

        layout.add_widget(self.password_input)
        layout.add_widget(password_box)
        layout.add_widget(Label(text="Public key (Base64):", size_hint_y=None, height=dp(30)))
        layout.add_widget(self.public_key_output)
        layout.add_widget(btn_copy_pub)
        layout.add_widget(self.status_label)

        scroll.add_widget(layout)
        page.add_widget(scroll)

        if self.is_android:
            tab.add_widget(page)
        else:
            tab.add_widget(self._wrap_with_footer_links(page))

        self.tabs.add_widget(tab)


    def _build_sign_tab(self):
        tab = TabbedPanelItem(text="Sign")

        page = BoxLayout(orientation="vertical", padding=0, spacing=dp(6))

        scroll = ScrollView()
        
        layout = BoxLayout(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(10),
            size_hint_y=None,
        )
        layout.bind(minimum_height=layout.setter("height"))
        
        if self.is_android:
            layout.add_widget(self._android_tab_header("Sign"))
        
        self.sign_text_input = TextInput(
            hint_text="Write text to sign",
            size_hint_y=None,
            height=dp(80),
        )
                
        self.signature_output = TextInput(
            readonly=True,
            size_hint_y=None,
            height=dp(70),
        )
                
        self.hash_output = TextInput(
            hint_text="Hash ID",
            readonly=True,
            multiline=False,
            size_hint_y=None,
            height=dp(40),
        )
                
        btn_sign = Button(text="Sign text", size_hint_y=None, height=dp(48))
        btn_copy_sig = Button(text="Copy signature", size_hint_y=None, height=dp(40))
        btn_copy_hash = Button(text="Copy Hash ID", size_hint_y=None, height=dp(40))

        btn_sign.bind(on_release=self.on_sign_text)
        btn_copy_sig.bind(on_release=self.on_copy_signature)
        btn_copy_hash.bind(on_release=self.on_copy_hash)

        lbl = Label(text="Text:", size_hint_y=None, height=dp(28), halign="left", valign="middle")
        lbl.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        layout.add_widget(lbl)
        layout.add_widget(self.sign_text_input)
        if self.is_android:
            layout.add_widget(self._android_paste_button(self.sign_text_input, "Paste text"))
        layout.add_widget(btn_sign)

        lbl = Label(text="Signature (Base64):", size_hint_y=None, height=dp(28), halign="left", valign="middle")
        lbl.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        layout.add_widget(lbl)
        layout.add_widget(self.signature_output)
        layout.add_widget(btn_copy_sig)

        lbl = Label(text="Hash ID:", size_hint_y=None, height=dp(28), halign="left", valign="middle")
        lbl.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        layout.add_widget(lbl)
        layout.add_widget(self.hash_output)
        layout.add_widget(btn_copy_hash)

        scroll.add_widget(layout)
        page.add_widget(scroll)

        if self.is_android:
            tab.add_widget(page)
        else:
            tab.add_widget(self._wrap_with_footer_links(page))

        self.tabs.add_widget(tab)


    def _build_verify_tab(self):
        tab = TabbedPanelItem(text="Verify")

        page = BoxLayout(orientation="vertical", padding=0, spacing=dp(6))

        scroll = ScrollView()
        layout = BoxLayout(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(10),
            size_hint_y=None,
        )
        layout.bind(minimum_height=layout.setter("height"))
        
        if self.is_android:
            layout.add_widget(self._android_tab_header("Verify"))
        
        self.verify_text_input = TextInput(
            hint_text="Text to verify",
            size_hint_y=None,
            height=dp(80),
        )
                
        self.verify_signature_input = TextInput(
            hint_text="Signature in Base64",
            size_hint_y=None,
            height=dp(70),
        )
                
        self.verify_hashid_input = TextInput(
            hint_text="Hash ID (quick check, not full verification)",
            multiline=False,
            size_hint_y=None,
            height=dp(40),
        )
                
        self.verify_contact_spinner = Spinner(
            text="Select public key",
            values=[],
            size_hint_y=None,
            height=dp(44),
        )
        self.verify_contact_spinner.bind(text=self.on_verify_contact_selected)

        hash_contact_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(44),
            spacing=dp(10),
        )

        self.verify_hashid_input.size_hint_x = 0.4
        self.verify_contact_spinner.size_hint_x = 0.6

        hash_contact_row.add_widget(self.verify_hashid_input)
        hash_contact_row.add_widget(self.verify_contact_spinner)

        self.verify_public_key_preview = TextInput(
            hint_text="Loaded public key Base64 will appear here",
            readonly=True,
            size_hint_y=None,
            height=dp(60),
        )
                
        self.verify_result = Label(
            text="",
            size_hint_y=None,
            height=dp(50),
        )

        btn_verify = Button(
            text="Verify",
            size_hint_y=None,
            height=dp(48),
        )
        btn_verify.bind(on_release=self.on_verify_text)

        lbl = Label(text="Text:", size_hint_y=None, height=dp(28), halign="left", valign="middle")
        lbl.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        layout.add_widget(lbl)
        layout.add_widget(self.verify_text_input)
        if self.is_android:
            layout.add_widget(self._android_paste_button(self.verify_text_input, "Paste text"))

        lbl = Label(text="Signature (Base64):", size_hint_y=None, height=dp(28), halign="left", valign="middle")
        lbl.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        layout.add_widget(lbl)
        layout.add_widget(self.verify_signature_input)
        if self.is_android:
            layout.add_widget(self._android_paste_button(self.verify_signature_input, "Paste signature"))
        
        lbl_hash = Label(
            text="Hash ID (optional):             Contact:",
            size_hint_y=None,
            height=dp(28),
            halign="left",
            valign="middle",
        )
        lbl_hash.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        layout.add_widget(lbl_hash)
        layout.add_widget(hash_contact_row)

        layout.add_widget(Label(text="Loaded public key Base64:", size_hint_y=None, height=dp(28)))
        layout.add_widget(self.verify_public_key_preview)

        layout.add_widget(btn_verify)
        layout.add_widget(self.verify_result)

        scroll.add_widget(layout)
        page.add_widget(scroll)

        if self.is_android:
            tab.add_widget(page)
        else:
            tab.add_widget(self._wrap_with_footer_links(page))

        self.tabs.add_widget(tab)

    def _build_contacts_tab(self):
        tab = TabbedPanelItem(text="Contacts")

        page = BoxLayout(orientation="vertical", padding=0, spacing=dp(6))

        scroll = ScrollView()
        outer = BoxLayout(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(10),
            size_hint_y=None,
        )
        outer.bind(minimum_height=outer.setter("height"))
        
        if self.is_android:
            outer.add_widget(self._android_tab_header("Contacts"))
        
        self.contact_name_input = TextInput(
            hint_text="Contact name / callsign",
            multiline=False,
            size_hint_y=None,
            height=dp(40),
        )
                
        self.contact_key_input = TextInput(
            hint_text="Paste public key Base64 or PEM here",
            size_hint_y=None,
            height=dp(100),
        )

        btn_add = Button(text="Add public key", size_hint_y=None, height=dp(48))
        btn_add.bind(on_release=self.on_add_contact)

        title_lbl = Label(
            text="Saved public keys:",
            size_hint_y=None,
            height=dp(28),
            halign="left",
            valign="middle",
        )
        title_lbl.bind(size=lambda instance, value: setattr(instance, "text_size", value))

        top_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(44),
            spacing=dp(10),
        )

        self.contacts_spinner = Spinner(
            text="Select contact",
            values=[],
        )
        self.contacts_spinner.bind(text=self.on_contact_selected)

        btn_rename = Button(
            text="Rename",
            size_hint_x=None,
            width=dp(120),
        )
        btn_rename.bind(on_release=self.on_rename_contact)

        top_row.add_widget(self.contacts_spinner)
        top_row.add_widget(btn_rename)

        btn_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(44),
            spacing=dp(10),
        )

        btn_view = Button(text="View PEM")
        btn_delete = Button(text="Delete contact")
        btn_use_verify = Button(text="Use in Verify")

        btn_view.bind(on_release=self.on_view_contact_key)
        btn_delete.bind(on_release=self.on_delete_contact)
        btn_use_verify.bind(on_release=self.on_use_contact_in_verify)

        btn_row.add_widget(btn_view)
        btn_row.add_widget(btn_delete)
        btn_row.add_widget(btn_use_verify)

        self.selected_contact_key_preview = TextInput(
            hint_text="Selected public key will appear here",
            readonly=True,
            size_hint_y=None,
            height=dp(100),
        )

        outer.add_widget(self.contact_name_input)
        outer.add_widget(self.contact_key_input)
        if self.is_android:
            outer.add_widget(self._android_paste_button(self.contact_key_input, "Paste public key"))
        outer.add_widget(btn_add)
        outer.add_widget(title_lbl)
        outer.add_widget(top_row)
        outer.add_widget(btn_row)
        outer.add_widget(self.selected_contact_key_preview)

        scroll.add_widget(outer)
        page.add_widget(scroll)

        if self.is_android:
            tab.add_widget(page)
        else:
            tab.add_widget(self._wrap_with_footer_links(page))

        self.tabs.add_widget(tab)

        self._refresh_contacts_list()

    def _refresh_contacts_spinner(self):
        names = sorted(self.contacts.list_contacts().keys())
        self.verify_contact_spinner.values = names
        if names and self.verify_contact_spinner.text == "Select public key":
            self.verify_contact_spinner.text = names[0]

    def _refresh_contacts_list(self):
        items = self.contacts.list_contacts()
        names = sorted(items.keys())

        if hasattr(self, "contacts_spinner"):
            self.contacts_spinner.values = names
            if names:
                if self.contacts_spinner.text == "Select contact":
                    self.contacts_spinner.text = names[0]
            else:
                self.contacts_spinner.text = "Select contact"

        if hasattr(self, "verify_contact_spinner"):
            self.verify_contact_spinner.values = names
            if names:
                if self.verify_contact_spinner.text == "Select public key":
                    self.verify_contact_spinner.text = names[0]
            else:
                self.verify_contact_spinner.text = "Select public key"

        if not names:
            if hasattr(self, "selected_contact_key_preview"):
                self.selected_contact_key_preview.text = ""
            if hasattr(self, "verify_public_key_preview"):
                self.verify_public_key_preview.text = ""

    def on_generate_key(self, _instance):
        has_loaded_key = self.private_key is not None
        has_saved_key = MY_PRIVATE_KEY_FILE.exists()

        if not has_loaded_key and not has_saved_key:
            self._generate_new_key_now()
            return

        content = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(12))

        msg = Label(
            text=(
                "Are you sure you want to create a new Ed25519 key?\n\n"
                "If you continue, the current key will be replaced in memory.\n"
                "If you save it afterwards, the previously saved private key will be overwritten."
            ),
            halign="left",
            valign="middle",
            size_hint_y=None,
        )
        msg.bind(width=lambda instance, value: setattr(instance, "text_size", (value, None)))
        msg.bind(texture_size=lambda instance, value: setattr(instance, "height", value[1]))

        buttons = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(44),
            spacing=dp(10),
        )

        btn_cancel = Button(text="Cancel")
        btn_ok = Button(text="Create new key")

        buttons.add_widget(btn_cancel)
        buttons.add_widget(btn_ok)

        content.add_widget(msg)
        content.add_widget(buttons)

        popup = Popup(
            title="Confirm new key",
            content=content,
            size_hint=(0.75, 0.42),
            auto_dismiss=False,
        )

        btn_cancel.bind(on_release=popup.dismiss)

        def do_create(_btn):
            popup.dismiss()
            self._generate_new_key_now()

        btn_ok.bind(on_release=do_create)

        popup.open()

    def on_save_key(self, _instance):
        
        if not self.private_key:
            self._popup("Error", "Generate or load a private key first.")
            return

        if not MY_PRIVATE_KEY_FILE.exists():
            self._save_key_now()
            return

        content = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(12))

        msg = Label(
            text=(
                "A private key is already saved.\n\n"
                "If you continue, the existing private/public key files will be overwritten."
            ),
            halign="left",
            valign="middle",
            size_hint_y=None,
        )
        msg.bind(width=lambda instance, value: setattr(instance, "text_size", (value, None)))
        msg.bind(texture_size=lambda instance, value: setattr(instance, "height", value[1]))

        buttons = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(44),
            spacing=dp(10),
        )

        btn_cancel = Button(text="Cancel")
        btn_ok = Button(text="Overwrite")

        buttons.add_widget(btn_cancel)
        buttons.add_widget(btn_ok)

        content.add_widget(msg)
        content.add_widget(buttons)

        popup = Popup(
            title="Confirm overwrite",
            content=content,
            size_hint=(0.75, 0.35),
            auto_dismiss=False,
        )

        btn_cancel.bind(on_release=popup.dismiss)

        def do_save(_btn):
            popup.dismiss()
            self._save_key_now()

        btn_ok.bind(on_release=do_save)

        popup.open()

    def on_load_key(self, _instance):
        if not MY_PRIVATE_KEY_FILE.exists():
            self._popup("Error", "No saved private key found yet.")
            return

        password = self.password_input.text.strip() or None
        try:
            self.private_key = CryptoManager.load_private_key(MY_PRIVATE_KEY_FILE, password)
            self.public_key = self.private_key.public_key()
            self.public_key_output.text = CryptoManager.public_key_to_base64(self.public_key)
            self.status_label.text = "Private key loaded successfully."
        except Exception as exc:
            self._popup("Load error", str(exc))


    def on_sign_text(self, _instance):
        if not self.private_key:
            self._popup("Error", "Load or generate a private key first.")
            return

        text = self.sign_text_input.text
        if not text.strip():
            self._popup("Error", "Write some text first.")
            return

        signature = CryptoManager.sign_text(self.private_key, text)
        self.signature_output.text = CryptoManager.signature_to_b64(signature)
        self.hash_output.text = CryptoManager.short_hash_id(text, signature)

    def _save_key_now(self):
        password = self.password_input.text.strip() or None
        CryptoManager.save_private_key(self.private_key, MY_PRIVATE_KEY_FILE, password)
        CryptoManager.save_public_key(self.public_key, MY_PUBLIC_KEY_FILE)
        self.status_label.text = f"Keys saved in {MY_PRIVATE_KEY_FILE.parent}"
        
        
    def on_verify_text(self, _instance):
        name = self.verify_contact_spinner.text

        if not name or name == "Select public key":
            self._popup("Error", "Select a saved public key.")
            return

        text = self.verify_text_input.text
        sig_b64 = self.verify_signature_input.text.strip()
        hashid = self.verify_hashid_input.text.strip()

        if not text.strip():
            self._popup("Error", "Text is empty.")
            return

        pem = self.contacts.get_public_key_pem(name)

        if not pem:
            self.verify_public_key_preview.text = ""
            self._popup("Error", f"Public key not found for: {name}")
            return

        try:
            public_key = CryptoManager.load_public_key_from_pem_text(pem)
            self.verify_public_key_preview.text = CryptoManager.public_key_to_base64(public_key)
        except Exception as exc:
            self.verify_public_key_preview.text = f"Error loading key: {exc}"
            self._popup("Error", str(exc))
            return

        if not pem:
            self._popup("Error", f"Public key not found for: {name}")
            return

        try:
            public_key = CryptoManager.load_public_key_from_pem_text(pem)

            sig_ok = None
            hashid_ok = None

            if sig_b64:
                signature = CryptoManager.signature_from_auto(sig_b64)
                sig_ok = CryptoManager.verify_text(public_key, text, signature)

                if hashid:
                    hashid_ok = CryptoManager.verify_hash_id(text, signature, hashid)

            elif hashid:
                result = "Hash ID present, but full signature is required for cryptographic verification"
                self.verify_result.text = result
                self._popup("Verification result", result)
                return

            else:
                result = "Write a signature or Hash ID"
                self.verify_result.text = result
                self._popup("Verification result", result)
                return

            if sig_ok is True and hashid_ok is True:
                result = "VALID signature + VALID Hash ID"
            elif sig_ok is True and hashid_ok is None:
                result = "VALID signature"
            elif sig_ok is True and hashid_ok is False:
                result = "VALID signature but INVALID Hash ID"
            elif sig_ok is False:
                result = "INVALID signature"
            else:
                result = "Verification error"

            self.verify_result.text = result
            self._popup("Verification result", result)

        except Exception as exc:
            result = f"Error: {exc}"
            self.verify_result.text = result
            self._popup("Verification result", result)

    def on_add_contact(self, _instance):
        name = self.contact_name_input.text.strip().upper()
        key_text = self.contact_key_input.text.strip()

        if not name:
            self._popup("Error", "Contact name is required.")
            return

        if not key_text:
            self._popup("Error", "Paste a public key first.")
            return

        try:
            public_key = CryptoManager.load_public_key_auto(key_text)
            pem_text = CryptoManager.public_key_to_pem_text(public_key)
            b64_text = CryptoManager.public_key_to_base64(public_key)
        except Exception as exc:
            self._popup("Error", f"Invalid public key: {exc}")
            return

        self.contacts.add_contact(name, pem_text)
        self.contact_name_input.text = ""
        self.contact_key_input.text = ""
        self.selected_contact_key_preview.text = b64_text
        self._refresh_contacts_list()
        self.contacts_spinner.text = name
        self._popup("OK", f"Public key saved for {name}.")
        
        
    def on_copy_signature(self, _instance):
        text = self.signature_output.text.strip()
        if not text:
            self._popup("Error", "No signature to copy.")
            return
        Clipboard.copy(text)
        self._popup("OK", "Signature copied.")

    def on_copy_hash(self, _instance):
        text = self.hash_output.text.strip()
        if not text:
            self._popup("Error", "No Hash ID to copy.")
            return
        Clipboard.copy(text)
        self._popup("OK", "Hash ID copied.")

    
    def on_verify_contact_selected(self, spinner, text):
        if not text or text == "Select public key":
            self.verify_public_key_preview.text = ""
            return

        pem = self.contacts.get_public_key_pem(text)
        if not pem:
            self.verify_public_key_preview.text = ""
            return

        try:
            public_key = CryptoManager.load_public_key_from_pem_text(pem)
            self.verify_public_key_preview.text = CryptoManager.public_key_to_base64(public_key)
        except Exception as exc:
            self.verify_public_key_preview.text = f"Error loading key: {exc}"
    
    
    def on_copy_public_key(self, _instance):
        text = self.public_key_output.text.strip()
        if not text:
            self._popup("Error", "No public key to copy.")
            return

        Clipboard.copy(text)
        self._popup("OK", "Public key copied.")
    
    def on_toggle_password_visibility(self, checkbox, active):
        self.password_input.password = not active
    
    def on_contact_selected(self, spinner, text):
        if not text or text == "Select contact":
            self.selected_contact_key_preview.text = ""
            return

        pem = self.contacts.get_public_key_pem(text)
        if not pem:
            self.selected_contact_key_preview.text = ""
            return

        try:
            public_key = CryptoManager.load_public_key_from_pem_text(pem)
            self.selected_contact_key_preview.text = CryptoManager.public_key_to_base64(public_key)
        except Exception as exc:
            self.selected_contact_key_preview.text = f"Error loading key: {exc}"


    def on_view_contact_key(self, _instance):
        name = self.contacts_spinner.text
        if not name or name == "Select contact":
            self._popup("Error", "Select a contact first.")
            return

        pem = self.contacts.get_public_key_pem(name)
        if not pem:
            self._popup("Error", "Public key not found.")
            return

        self.selected_contact_key_preview.text = pem

    
    def on_delete_contact(self, _instance):
        name = self.contacts_spinner.text
        if not name or name == "Select contact":
            self._popup("Error", "Select a contact first.")
            return

        content = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(12))

        info_label = Label(
            text=f"Delete contact: {name}?",
            size_hint_y=None,
            height=dp(40),
            halign="left",
            valign="middle",
        )
        info_label.bind(size=lambda instance, value: setattr(instance, "text_size", value))

        buttons = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(44),
            spacing=dp(10),
        )

        btn_cancel = Button(text="Cancel")
        btn_delete = Button(text="Delete")

        buttons.add_widget(btn_cancel)
        buttons.add_widget(btn_delete)

        content.add_widget(info_label)
        content.add_widget(buttons)

        popup = Popup(
            title="Delete contact",
            content=content,
            size_hint=(0.7, 0.3),
            auto_dismiss=False,
        )

        def do_delete(_btn):
            try:
                self.contacts.remove_contact(name)
                self.selected_contact_key_preview.text = ""
                self._refresh_contacts_list()
                popup.dismiss()
                self._popup("OK", f"Contact deleted: {name}")
            except Exception as exc:
                self._popup("Error", str(exc))

        btn_cancel.bind(on_release=popup.dismiss)
        btn_delete.bind(on_release=do_delete)

        popup.open()


    def on_use_contact_in_verify(self, _instance):
        name = self.contacts_spinner.text
        if not name or name == "Select contact":
            self._popup("Error", "Select a contact first.")
            return

        if hasattr(self, "verify_contact_spinner"):
            self.verify_contact_spinner.text = name
            pem = self.contacts.get_public_key_pem(name)

        if not pem:
            self.verify_public_key_preview.text = ""
            self._popup("Error", f"Public key not found for: {name}")
            return

        try:
            public_key = CryptoManager.load_public_key_from_pem_text(pem)
            self.verify_public_key_preview.text = CryptoManager.public_key_to_base64(public_key)
        except Exception as exc:
            self.verify_public_key_preview.text = f"Error loading key: {exc}"
            self._popup("Error", str(exc))
            return

        self._popup("OK", f"Contact loaded into Verify: {name}")
    
    
    def on_rename_contact(self, _instance):
        old_name = self.contacts_spinner.text
        if not old_name or old_name == "Select contact":
            self._popup("Error", "Select a contact first.")
            return

        content = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(12))

        info_label = Label(
            text=f"Current name: {old_name}",
            size_hint_y=None,
            height=dp(30),
            halign="left",
            valign="middle",
        )
        info_label.bind(size=lambda instance, value: setattr(instance, "text_size", value))

        new_name_input = TextInput(
            text=old_name,
            hint_text="New contact name",
            multiline=False,
            size_hint_y=None,
            height=dp(40),
        )

        buttons = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(44),
            spacing=dp(10),
        )

        btn_cancel = Button(text="Cancel")
        btn_ok = Button(text="Rename")

        buttons.add_widget(btn_cancel)
        buttons.add_widget(btn_ok)

        content.add_widget(info_label)
        content.add_widget(new_name_input)
        content.add_widget(buttons)

        popup = Popup(
            title="Rename contact",
            content=content,
            size_hint=(0.7, 0.35),
            auto_dismiss=False,
        )

        def do_rename(_btn):
            new_name = new_name_input.text.strip().upper()

            if not new_name:
                self._popup("Error", "New contact name cannot be empty.")
                return

            try:
                self.contacts.rename_contact(old_name, new_name)
                self._refresh_contacts_list()
                self.contacts_spinner.text = new_name

                pem = self.contacts.get_public_key_pem(new_name)
                self.selected_contact_key_preview.text = pem or ""

                popup.dismiss()
                self._popup("OK", f"Contact renamed: {old_name} to {new_name}")
            except Exception as exc:
                self._popup("Error", str(exc))

        btn_cancel.bind(on_release=popup.dismiss)
        btn_ok.bind(on_release=do_rename)

        popup.open()
    
    def on_open_about_tab(self, _instance):
        self.show_about_popup()
    
            
    def show_about_popup(self):
        outer = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(8))

        # pequenyo margen superior para que no se coma el titulo
        outer.add_widget(Widget(size_hint_y=None, height=dp(4)))

        content = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(12),
        )
        content.bind(minimum_height=content.setter("height"))
        title = Label(
            text="Eliptic Signer",
            bold=True,
            color=(0.23, 0.64, 1, 1),
            halign="left",
            valign="middle",
            size_hint_y=None,
            font_size="28sp" if self.is_android else "22sp",
        )
        title.bind(width=lambda instance, value: setattr(instance, "text_size", (value, None)))
        title.bind(texture_size=lambda instance, value: setattr(instance, "height", value[1]))

        version = Label(
            text="Version 0.1.1",
            halign="left",
            valign="middle",
            size_hint_y=None,
            font_size="18sp" if self.is_android else "14sp",
        )

        version.bind(width=lambda instance, value: setattr(instance, "text_size", (value, None)))
        version.bind(texture_size=lambda instance, value: setattr(instance, "height", value[1]))
        
        intro = Label(
            text=(
                "This app creates Ed25519 keys, signs text messages, and verifies "
                "signatures using stored public keys.\n\n"
                "It is designed as a practical tool for identity verification, "
                "including compact oriented identifiers for radio/comms use.\n\n"
                "Made by [ref=qn][color=3aa3ff]Quixote Network[/color][/ref]."
            ),
            markup=True,
            halign="left",
            valign="top",
            size_hint_y=None,
        )
        intro.bind(width=lambda instance, value: setattr(instance, "text_size", (value, None)))
        intro.bind(texture_size=lambda instance, value: setattr(instance, "height", value[1]))

        intro.bind(on_ref_press=lambda instance, ref: webbrowser.open("https://quixote.info"))
        intro.bind(width=lambda instance, value: setattr(instance, "text_size", (value, None)))
        intro.bind(texture_size=lambda instance, value: setattr(instance, "height", value[1]))

        btn_repo = Button(
            text="Open GitHub Repository",
            size_hint_y=None,
            height=dp(44),
        )
        btn_repo.bind(on_release=lambda _x: webbrowser.open("https://github.com/QuixoteNetwork/eliptic-signer"))

        support_text = Label(
            text="Support this project on Ko-fi:",
            halign="left",
            valign="middle",
            size_hint_y=None,
        )
        support_text.bind(width=lambda instance, value: setattr(instance, "text_size", (value, None)))
        support_text.bind(texture_size=lambda instance, value: setattr(instance, "height", value[1]))

        btn_kofi = Button(
            text="Support on Ko-fi",
            size_hint_y=None,
            height=dp(44),
        )
        btn_kofi.bind(on_release=lambda _x: webbrowser.open("https://ko-fi.com/quixotesystems"))

        close_link = Label(
            text='[ref=close][color=3aa3ff]Close[/color][/ref]',
            markup=True,
            size_hint_y=None,
            height=dp(28),
            halign="center",
            valign="middle",
        )
        close_link.bind(size=lambda instance, value: setattr(instance, "text_size", value))
        
        content.add_widget(title)
        content.add_widget(version)
        content.add_widget(intro)
        content.add_widget(support_text)
        content.add_widget(btn_kofi)
        content.add_widget(btn_repo)
        

        scroll = ScrollView()
        scroll.add_widget(content)

        outer.add_widget(scroll)
        outer.add_widget(close_link)

        popup = Popup(
            title="About",
            content=outer,
            size_hint=(0.9, 0.84),
            auto_dismiss=False,
        )

        close_link.bind(on_ref_press=lambda instance, ref: popup.dismiss())
        popup.open()
    
    def _generate_new_key_now(self):
        self.private_key = CryptoManager.generate_private_key()
        self.public_key = self.private_key.public_key()
        self.public_key_output.text = CryptoManager.public_key_to_base64(self.public_key)
        self.status_label.text = "New Ed25519 key generated in memory."
      
      
    #--------------------------------------------------   
    #-------------- ANDROID ADAPTATION ----------------
    #--------------------------------------------------
    
    def _scroll_to_input(self, scroll, target_input):
        def do_scroll(_dt):
            try:
                scroll.scroll_to(target_input, padding=dp(80), animate=False)
            except Exception:
                pass
        Clock.schedule_once(do_scroll, 0.1)
        
        
    def _is_android(self):
        return platform == "android"

    def _input_h(self):
        return dp(48) if self._is_android() else dp(40)

    def _button_h(self):
        return dp(54) if self._is_android() else dp(48)

    def _small_button_h(self):
        return dp(48) if self._is_android() else dp(40)

    def _row_h(self):
        return dp(52) if self._is_android() else dp(44)

    def _section_h(self):
        return dp(32) if self._is_android() else dp(28)

    def _page_padding(self):
        return dp(14) if self._is_android() else dp(10)

    def _page_spacing(self):
        return dp(12) if self._is_android() else dp(10)
        
    def _build_top_bar(self):
        top_bar = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(56),
            padding=(dp(8), dp(8)),
            spacing=dp(8),
        )

        with top_bar.canvas.before:
            Color(0.10, 0.45, 0.85, 1)
            self._top_bar_rect = Rectangle(pos=top_bar.pos, size=top_bar.size)

        top_bar.bind(pos=self._update_top_bar_rect, size=self._update_top_bar_rect)

        btn_menu = Button(
            text="Menu",
            size_hint=(None, None),
            size=(dp(72), dp(40)),
            background_normal="",
            background_color=(1, 1, 1, 0.15),
            color=(1, 1, 1, 1),
            font_size="16sp",
        )
        btn_menu.bind(on_release=self.open_hamburger_menu)

        spacer = Widget()

        title = Label(
            text="Eliptic Signer",
            color=(1, 1, 1, 1),
            halign="right",
            valign="middle",
            size_hint_x=None,
            width=dp(180),
        )
        title.bind(size=lambda instance, value: setattr(instance, "text_size", value))

        top_bar.add_widget(btn_menu)
        top_bar.add_widget(spacer)
        top_bar.add_widget(title)

        self.main_container.add_widget(top_bar)

    def _update_top_bar_rect(self, instance, _value):
        self._top_bar_rect.pos = instance.pos
        self._top_bar_rect.size = instance.size
    

    def _switch_tab(self, tab_name, popup=None):
        for tab in self.tabs.tab_list:
            if tab.text == tab_name:
                self.tabs.switch_to(tab)
                break

        if popup:
            popup.dismiss()
        
    def _update_android_tab_widths(self, *_args):
        if not self.is_android:
            return

        width = self.tabs.width

        # fallback por si aun no esta renderizado
        if width <= 0:
            from kivy.core.window import Window
            width = Window.width

        num_tabs = 4

        self.tabs.tab_width = width / num_tabs
    
    def _android_tab_header(self, title_text: str):
        wrapper = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(44),
            spacing=dp(4),
        )

        title = Label(
            text=title_text,
            size_hint_y=None,
            height=dp(28),
            halign="left",
            valign="middle",
            color=(1, 1, 1, 1),
        )
        title.bind(size=lambda instance, value: setattr(instance, "text_size", value))

        line = Widget(size_hint_y=None, height=dp(2))
        with line.canvas.before:
            Color(0.10, 0.45, 0.85, 1)
            line._rect = Rectangle(pos=line.pos, size=line.size)
        line.bind(pos=lambda inst, val: setattr(inst._rect, "pos", inst.pos))
        line.bind(size=lambda inst, val: setattr(inst._rect, "size", inst.size))

        wrapper.add_widget(title)
        wrapper.add_widget(line)
        return wrapper
    
    def _paste_from_clipboard(self, target_input):
        try:
            pasted = Clipboard.paste() or ""
            target_input.text = pasted
        except Exception as exc:
            self._popup("Paste error", str(exc))
    
    def _android_paste_button(self, target_input, text="Paste"):
        btn = Button(
            text=text,
            size_hint_y=None,
            height=dp(40),
        )
        btn.bind(on_release=lambda _x: self._paste_from_clipboard(target_input))
        return btn
            
    #------------ END ANDROID ADAPTATION -----------------
    
    #------------ IMPORT / EXPORT KEYS -----------------
    def _desktop_exchange_dir(self) -> Path:
        return Path.home() / "elipticsigner" / "exported_keys"

    def _android_exchange_dir(self) -> Path:
        try:
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            activity = PythonActivity.mActivity
            ext_dir = activity.getExternalFilesDir(None)
            if ext_dir:
                return Path(str(ext_dir.getAbsolutePath())) / "exported_keys"
        except Exception:
            pass

        # fallback
        return Path(MY_PRIVATE_KEY_FILE.parent) / "exported_keys"

    def _exchange_dir(self) -> Path:
        if self.is_android:
            return self._android_exchange_dir()
        return self._desktop_exchange_dir()
    
    def on_export_keys(self, _instance=None):
        if not MY_PRIVATE_KEY_FILE.exists():
            self._popup("Export keys", "No saved private key found.")
            return

        try:
            target_dir = self._exchange_dir()
            target_dir.mkdir(parents=True, exist_ok=True)

            private_dst = target_dir / "my_private_key.pem"
            public_dst = target_dir / "my_public_key.pem"

            shutil.copy2(MY_PRIVATE_KEY_FILE, private_dst)

            if MY_PUBLIC_KEY_FILE.exists():
                shutil.copy2(MY_PUBLIC_KEY_FILE, public_dst)
            elif self.public_key is not None:
                CryptoManager.save_public_key(self.public_key, public_dst)
            else:
                self._popup("Export keys", "Private key exported, but no public key was available.")
                return

            self._popup(
                "Export keys",
                f"Keys exported to:\n\n{target_dir}\n\nFiles:\nmy_private_key.pem\nmy_public_key.pem"
            )

        except Exception as exc:
            self._popup("Export keys", f"Export failed:\n{exc}")


    def on_import_keys(self, _instance=None):
        if self.is_android:
            self._import_keys_android_fixed()
            return

        def do_import(source_dir: Path):
            try:
                private_src = source_dir / "my_private_key.pem"
                public_src = source_dir / "my_public_key.pem"

                if not private_src.exists():
                    self._popup(
                        "Import keys",
                        f"The selected folder does not contain:\n{private_src.name}"
                    )
                    return

                password = self.import_password_input.text.strip() or None

                imported_private = CryptoManager.load_private_key(private_src, password)
                imported_public = imported_private.public_key()

                if public_src.exists():
                    file_public = CryptoManager.load_public_key_from_file(public_src)

                    imported_b64 = CryptoManager.public_key_to_base64(imported_public)
                    file_b64 = CryptoManager.public_key_to_base64(file_public)

                    if imported_b64 != file_b64:
                        self._popup(
                            "Import keys",
                            "The public key does not match the private key."
                        )
                        return

                ensure_app_dirs()

                shutil.copy2(private_src, MY_PRIVATE_KEY_FILE)
                CryptoManager.save_public_key(imported_public, MY_PUBLIC_KEY_FILE)

                self.private_key = imported_private
                self.public_key = imported_public
                self.public_key_output.text = CryptoManager.public_key_to_base64(imported_public)
                self.status_label.text = "Private/public key imported successfully."
                self.import_password_input.text = ""
                self.import_show_password_checkbox.active = False

                self._popup(
                    "Import keys",
                    f"Keys imported from:\n{source_dir}"
                )

            except Exception as exc:
                self._popup("Import keys", f"Import failed:\n{exc}")

        self._choose_import_directory(do_import)


    def _import_keys_android_fixed(self):
        try:
            source_dir = self._exchange_dir()

            private_src = source_dir / "my_private_key.pem"
            public_src = source_dir / "my_public_key.pem"

            if not private_src.exists():
                self._popup(
                    "Import keys",
                    f"Private key not found in:\n{source_dir}"
                )
                return

            password = self.import_password_input.text.strip() or None

            imported_private = CryptoManager.load_private_key(private_src, password)
            imported_public = imported_private.public_key()

            if public_src.exists():
                file_public = CryptoManager.load_public_key_from_file(public_src)

                imported_b64 = CryptoManager.public_key_to_base64(imported_public)
                file_b64 = CryptoManager.public_key_to_base64(file_public)

                if imported_b64 != file_b64:
                    self._popup(
                        "Import keys",
                        "The public key does not match the private key."
                    )
                    return

            ensure_app_dirs()

            shutil.copy2(private_src, MY_PRIVATE_KEY_FILE)
            CryptoManager.save_public_key(imported_public, MY_PUBLIC_KEY_FILE)

            self.private_key = imported_private
            self.public_key = imported_public
            self.public_key_output.text = CryptoManager.public_key_to_base64(imported_public)
            self.status_label.text = "Private/public key imported successfully."
            self.import_password_input.text = ""
            self.import_show_password_checkbox.active = False

            self._popup(
                "Import keys",
                f"Keys imported from:\n{source_dir}"
            )

        except Exception as exc:
            self._popup("Import keys", f"Import failed:\n{exc}")
    
    
    def _default_import_path(self) -> str:
        if self.is_android:
            try:
                from android.storage import primary_external_storage_path
                return primary_external_storage_path()
            except Exception:
                return str(Path.home())
        return str(Path.home())


    def _choose_import_directory(self, on_selected):
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))

        chooser = FileChooserListView(
            path=self._default_import_path(),
            dirselect=True,
            size_hint=(1, 1),
        )

        buttons = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(48),
            spacing=dp(10),
        )

        btn_cancel = Button(text="Cancel")
        btn_select = Button(text="Select folder")

        buttons.add_widget(btn_cancel)
        buttons.add_widget(btn_select)

        content.add_widget(chooser)
        content.add_widget(buttons)

        popup = Popup(
            title="Import keys from folder",
            content=content,
            size_hint=(0.95, 0.9),
            auto_dismiss=False,
        )

        def do_select(_btn):
            selected = chooser.selection[0] if chooser.selection else chooser.path
            popup.dismiss()
            on_selected(Path(selected))

        btn_cancel.bind(on_release=popup.dismiss)
        btn_select.bind(on_release=do_select)

        popup.open()


    def _build_import_export_tab(self):
        tab = TabbedPanelItem(text="Import/Export")

        page = BoxLayout(orientation="vertical", padding=0, spacing=dp(6))

        scroll = ScrollView()
        layout = BoxLayout(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(10),
            size_hint_y=None,
        )
        layout.bind(minimum_height=layout.setter("height"))

        # PASSWORD INPUT (compartido entre import/export)
        self.import_password_input = TextInput(
            hint_text="Password (if private key is protected)",
            multiline=False,
            password=True,
            size_hint_y=None,
            height=dp(40),
        )
        self.import_show_password_checkbox = CheckBox(
            active=False,
            size_hint=(None, None),
            size=(dp(40), dp(40)),
        )
        self.import_show_password_checkbox.bind(
            active=self.on_toggle_import_password_visibility
        )
        lbl_show_pw = Label(
            text="Show password",
            size_hint_x=None,
            width=dp(150),
            halign="left",
            valign="middle",
        )
        lbl_show_pw.bind(size=lambda instance, value: setattr(instance, "text_size", value))
        password_box = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(40),
            spacing=dp(10),
        )
        password_box.add_widget(self.import_show_password_checkbox)
        password_box.add_widget(lbl_show_pw)

        if self.is_android:
            # ---- LAYOUT ANDROID ----
            layout.add_widget(self._android_tab_header("Import / Export"))

            # --- EXPORT ---
            lbl_export = Label(
                text="EXPORT",
                bold=True,
                size_hint_y=None,
                height=dp(30),
                halign="left",
                valign="middle",
            )
            lbl_export.bind(size=lambda i, v: setattr(i, "text_size", v))

            lbl_export_info = Label(
                text=(
                    "Share keys via any app (WhatsApp, email, Drive…) "
                    "or save a copy to your device."
                ),
                size_hint_y=None,
                halign="left",
                valign="top",
            )
            lbl_export_info.bind(
                width=lambda i, v: setattr(i, "text_size", (v, None))
            )
            lbl_export_info.bind(
                texture_size=lambda i, v: setattr(i, "height", v[1])
            )

            btn_export_share = Button(
                text="Share keys (WhatsApp, email, Drive…)",
                size_hint_y=None,
                height=dp(52),
            )
            btn_export_share.bind(on_release=self._android_export_share_keys)

            btn_export_file = Button(
                text="Save keys to device storage",
                size_hint_y=None,
                height=dp(48),
            )
            btn_export_file.bind(on_release=self.on_export_keys)

            # --- IMPORT ---
            lbl_import = Label(
                text="IMPORT",
                bold=True,
                size_hint_y=None,
                height=dp(30),
                halign="left",
                valign="middle",
            )
            lbl_import.bind(size=lambda i, v: setattr(i, "text_size", v))

            lbl_import_info = Label(
                text=(
                    "Paste the private key PEM text you received/exported, "
                    "or import from the saved file on this device."
                ),
                size_hint_y=None,
                halign="left",
                valign="top",
            )
            lbl_import_info.bind(
                width=lambda i, v: setattr(i, "text_size", (v, None))
            )
            lbl_import_info.bind(
                texture_size=lambda i, v: setattr(i, "height", v[1])
            )

            self.import_pem_input = TextInput(
                hint_text="Paste private key PEM here (-----BEGIN PRIVATE KEY-----...)",
                size_hint_y=None,
                height=dp(120),
            )

            btn_paste_pem = self._android_paste_button(
                self.import_pem_input, "Paste key text"
            )

            btn_import_text = Button(
                text="Import from pasted text",
                size_hint_y=None,
                height=dp(52),
            )
            btn_import_text.bind(on_release=self._import_from_pasted_pem)

            btn_import_file = Button(
                text="Browse and pick key file...",
                size_hint_y=None,
                height=dp(48),
            )
            btn_import_file.bind(on_release=self._android_pick_private_key_file)

            layout.add_widget(self.import_password_input)
            layout.add_widget(password_box)
            layout.add_widget(lbl_export)
            layout.add_widget(lbl_export_info)
            layout.add_widget(btn_export_share)
            layout.add_widget(btn_export_file)
            layout.add_widget(lbl_import)
            layout.add_widget(lbl_import_info)
            layout.add_widget(self.import_pem_input)
            layout.add_widget(btn_paste_pem)
            layout.add_widget(btn_import_text)
            layout.add_widget(btn_import_file)

        else:
            # ---- LAYOUT ESCRITORIO ----
            info = Label(
                text="Import or export your private/public key files.",
                size_hint_y=None,
                height=dp(40),
                halign="left",
                valign="middle",
            )
            info.bind(size=lambda instance, value: setattr(instance, "text_size", value))

            btn_import = Button(
                text="Import keys",
                size_hint_y=None,
                height=dp(48),
            )
            btn_export = Button(
                text="Export keys",
                size_hint_y=None,
                height=dp(48),
            )
            btn_import.bind(on_release=self.on_import_keys)
            btn_export.bind(on_release=self.on_export_keys)

            layout.add_widget(info)
            layout.add_widget(btn_import)
            layout.add_widget(btn_export)
            layout.add_widget(self.import_password_input)
            layout.add_widget(password_box)

        scroll.add_widget(layout)
        page.add_widget(scroll)

        if self.is_android:
            tab.add_widget(page)
        else:
            tab.add_widget(self._wrap_with_footer_links(page))

        self.tabs.add_widget(tab)


    def _wrap_with_footer_links(self, main_widget):
        outer = BoxLayout(orientation="vertical", padding=0, spacing=dp(6))
        outer.add_widget(main_widget)

        footer = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(38),
            padding=(dp(8), 0, dp(8), 0),
        )

        left_link = Label(
            text='[ref=import_export][color=3aa3ff]Import / Export keys[/color][/ref]',
            markup=True,
            size_hint=(1, None),
            height=dp(32),
            halign="left",
            valign="middle",
        )
        left_link.bind(size=lambda instance, value: setattr(instance, "text_size", value))

        right_link = Label(
            text='[ref=about][color=3aa3ff]About[/color][/ref]',
            markup=True,
            size_hint=(None, None),
            size=(dp(90), dp(32)),
            halign="right",
            valign="middle",
        )
        right_link.bind(size=lambda instance, value: setattr(instance, "text_size", value))

        left_link.bind(on_ref_press=lambda instance, ref: self._switch_tab("Import/Export"))
        right_link.bind(on_ref_press=lambda instance, ref: self.show_about_popup())

        footer.add_widget(left_link)
        footer.add_widget(right_link)

        outer.add_widget(footer)
        return outer

    def on_toggle_import_password_visibility(self, checkbox, active):
        self.import_password_input.password = not active

    # ---- Android: compartir claves como texto via intent ----

    def _android_share_text(self, text: str, title: str = "Share"):
        """Lanza el share sheet de Android para compartir texto."""
        try:
            from jnius import autoclass
            Intent = autoclass("android.content.Intent")
            String = autoclass("java.lang.String")
            PythonActivity = autoclass("org.kivy.android.PythonActivity")

            intent = Intent()
            intent.setAction(Intent.ACTION_SEND)
            intent.putExtra(Intent.EXTRA_TEXT, String(text))
            intent.putExtra(Intent.EXTRA_SUBJECT, String(title))
            intent.setType("text/plain")
            chooser = Intent.createChooser(intent, String(title))
            PythonActivity.mActivity.startActivity(chooser)
        except Exception as exc:
            self._popup("Share error", f"Could not open share dialog:\n{exc}")

    def _android_export_share_keys(self, _instance=None):
        """Exporta las claves compartiendolas como texto (share sheet Android)."""
        if not MY_PRIVATE_KEY_FILE.exists():
            self._popup("Export keys", "No saved private key found. Generate and save a key first.")
            return
        try:
            private_pem = MY_PRIVATE_KEY_FILE.read_text(encoding="utf-8")
            public_pem = (
                MY_PUBLIC_KEY_FILE.read_text(encoding="utf-8")
                if MY_PUBLIC_KEY_FILE.exists()
                else ""
            )
            combined = (
                "=== ELIPTIC SIGNER - PRIVATE KEY ===\n"
                f"{private_pem}\n"
                "=== PUBLIC KEY ===\n"
                f"{public_pem}"
            )
            self._android_share_text(combined, "Export Eliptic Signer Keys")
        except Exception as exc:
            self._popup("Export keys", f"Export failed:\n{exc}")

    def _import_from_pasted_pem(self, _instance=None):
        """Importa la clave privada desde texto PEM pegado directamente."""
        pem_text = self.import_pem_input.text.strip()
        if not pem_text:
            self._popup("Import keys", "Paste the private key PEM text first.")
            return

        # Si el usuario pego el bloque completo exportado, extraer solo la clave privada
        if "=== ELIPTIC SIGNER - PRIVATE KEY ===" in pem_text:
            raw_lines = pem_text.splitlines()
            private_lines = []
            in_private = False
            for line in raw_lines:
                if "=== ELIPTIC SIGNER - PRIVATE KEY ===" in line:
                    in_private = True
                    continue
                if "===" in line and in_private:
                    break
                if in_private:
                    private_lines.append(line)
            pem_text = "\n".join(private_lines).strip()

        password = self.import_password_input.text.strip() or None
        try:
            imported_private = CryptoManager.load_private_key_from_pem_text(pem_text, password)
            imported_public = imported_private.public_key()

            ensure_app_dirs()
            CryptoManager.save_private_key(imported_private, MY_PRIVATE_KEY_FILE, password)
            CryptoManager.save_public_key(imported_public, MY_PUBLIC_KEY_FILE)

            self.private_key = imported_private
            self.public_key = imported_public
            self.public_key_output.text = CryptoManager.public_key_to_base64(imported_public)
            self.status_label.text = "Keys imported from pasted text."
            self.import_password_input.text = ""
            self.import_show_password_checkbox.active = False
            self.import_pem_input.text = ""

            self._popup("Import keys", "Keys imported successfully from pasted text!")
        except Exception as exc:
            self._popup("Import keys", f"Import failed:\n{exc}")

    # ---- Android: selector de archivos nativo (SAF) ----

    _IMPORT_REQUEST_CODE = 9001

    def _android_pick_private_key_file(self, _instance=None):
        if not self.is_android:
            self._choose_import_directory(
                lambda p: self._do_desktop_import_from_dir(p)
            )
            return
        try:
            from android.activity import bind as activity_bind
            from jnius import autoclass

            Intent = autoclass("android.content.Intent")
            PythonActivity = autoclass("org.kivy.android.PythonActivity")

            activity_bind(on_activity_result=self._on_import_file_result)

            intent = Intent(Intent.ACTION_OPEN_DOCUMENT)
            intent.addCategory(Intent.CATEGORY_OPENABLE)
            intent.setType("*/*")

            PythonActivity.mActivity.startActivityForResult(
                intent, self._IMPORT_REQUEST_CODE
            )
        except Exception as exc:
            self._popup("Import keys", f"Could not open file picker:\n{exc}")

    def _on_import_file_result(self, requestCode, resultCode, data):
        try:
            from android.activity import unbind as activity_unbind
            activity_unbind(on_activity_result=self._on_import_file_result)
        except Exception:
            pass

        if requestCode != self._IMPORT_REQUEST_CODE:
            return

        RESULT_OK = -1
        if resultCode != RESULT_OK or data is None:
            return

        def do_import(dt):
            try:
                from jnius import autoclass
                PythonActivity = autoclass("org.kivy.android.PythonActivity")
                BufferedReader = autoclass("java.io.BufferedReader")
                InputStreamReader = autoclass("java.io.InputStreamReader")

                uri = data.getData()
                content_resolver = PythonActivity.mActivity.getContentResolver()
                input_stream = content_resolver.openInputStream(uri)

                reader = BufferedReader(InputStreamReader(input_stream))
                lines = []
                line = reader.readLine()
                while line is not None:
                    lines.append(str(line))
                    line = reader.readLine()
                reader.close()

                pem_text = "\n".join(lines).strip()
                password = self.import_password_input.text.strip() or None

                imported_private = CryptoManager.load_private_key_from_pem_text(
                    pem_text, password
                )
                imported_public = imported_private.public_key()

                ensure_app_dirs()
                CryptoManager.save_private_key(imported_private, MY_PRIVATE_KEY_FILE, password)
                CryptoManager.save_public_key(imported_public, MY_PUBLIC_KEY_FILE)

                self.private_key = imported_private
                self.public_key = imported_public
                self.public_key_output.text = CryptoManager.public_key_to_base64(imported_public)
                self.status_label.text = "Keys imported from file."
                self.import_password_input.text = ""
                self.import_show_password_checkbox.active = False

                self._popup("Import keys", "Keys imported successfully from file!")

            except Exception as exc:
                self._popup("Import keys", f"Import failed:\n{exc}")

        Clock.schedule_once(do_import, 0)

    def _do_desktop_import_from_dir(self, source_dir):
        try:
            private_src = source_dir / "my_private_key.pem"
            public_src = source_dir / "my_public_key.pem"

            if not private_src.exists():
                self._popup(
                    "Import keys",
                    f"The selected folder does not contain:\n{private_src.name}"
                )
                return

            password = self.import_password_input.text.strip() or None
            imported_private = CryptoManager.load_private_key(private_src, password)
            imported_public = imported_private.public_key()

            if public_src.exists():
                file_public = CryptoManager.load_public_key_from_file(public_src)
                if (CryptoManager.public_key_to_base64(imported_public) !=
                        CryptoManager.public_key_to_base64(file_public)):
                    self._popup("Import keys", "The public key does not match the private key.")
                    return

            ensure_app_dirs()
            shutil.copy2(private_src, MY_PRIVATE_KEY_FILE)
            CryptoManager.save_public_key(imported_public, MY_PUBLIC_KEY_FILE)

            self.private_key = imported_private
            self.public_key = imported_public
            self.public_key_output.text = CryptoManager.public_key_to_base64(imported_public)
            self.status_label.text = "Keys imported successfully."
            self.import_password_input.text = ""
            self.import_show_password_checkbox.active = False

            self._popup("Import keys", f"Keys imported from:\n{source_dir}")

        except Exception as exc:
            self._popup("Import keys", f"Import failed:\n{exc}")

    #------------ END IMPORT / EXPORT KEYS -----------------
