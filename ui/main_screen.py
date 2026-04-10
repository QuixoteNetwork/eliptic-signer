from __future__ import annotations
import webbrowser

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

from core.contacts import ContactsStore
from core.crypto_utils import CryptoManager
from core.storage import (
    CONTACTS_FILE,
    MY_PRIVATE_KEY_FILE,
    MY_PUBLIC_KEY_FILE,
    ensure_app_dirs,
)


class MainScreen(TabbedPanel):
    def __init__(self, **kwargs):
        kwargs["do_default_tab"] = False
        super().__init__(**kwargs)
        
        self.private_key = None
        self.public_key = None

        ensure_app_dirs()
        self.contacts = ContactsStore(CONTACTS_FILE)
        
        self._build_identity_tab()
        self._build_sign_tab()
        self._build_verify_tab()
        self._build_contacts_tab()
        self._refresh_contacts_spinner()
        self._load_existing_keys_if_possible()
        
        Clock.schedule_once(lambda dt: self.show_about_popup(), 0.2)

    def _popup(self, title: str, message: str) -> None:
        content = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(12))

        msg = Label(
            text=message,
            halign="center",
            valign="middle",
        )
        msg.bind(size=lambda instance, value: setattr(instance, "text_size", value))

        btn = Button(text="OK", size_hint_y=None, height=dp(44))

        content.add_widget(msg)
        content.add_widget(btn)

        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.75, 0.35),
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

        layout.add_widget(btn_generate)
        layout.add_widget(self.password_input)
        layout.add_widget(password_box)
        
        layout.add_widget(btn_save)
        layout.add_widget(btn_load)
        layout.add_widget(Label(text="Public key (Base64):", size_hint_y=None, height=dp(30)))
        layout.add_widget(self.public_key_output)
        layout.add_widget(btn_copy_pub)
        layout.add_widget(self.status_label)

        scroll.add_widget(layout)
        page.add_widget(scroll)

        tab.add_widget(self._wrap_with_about_button(page))
        self.add_widget(tab)

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

        self.sign_text_input = TextInput(
            hint_text="Write text to sign",
            size_hint_y=None,
            height=dp(80),
        )

        self.signature_output = TextInput(
            readonly=True,
            size_hint_y=None,
            height=dp(60),
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

        layout.add_widget(Label(text="Text:", size_hint_y=None, height=dp(28)))
        layout.add_widget(self.sign_text_input)
        layout.add_widget(btn_sign)

        layout.add_widget(Label(text="Signature (Base64):", size_hint_y=None, height=dp(28)))
        layout.add_widget(self.signature_output)
        layout.add_widget(btn_copy_sig)

        layout.add_widget(Label(text="Hash ID:", size_hint_y=None, height=dp(28)))
        layout.add_widget(self.hash_output)
        layout.add_widget(btn_copy_hash)

        scroll.add_widget(layout)
        page.add_widget(scroll)

        tab.add_widget(self._wrap_with_about_button(page))
        self.add_widget(tab)


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

        self.verify_text_input = TextInput(
            hint_text="Text to verify",
            size_hint_y=None,
            height=dp(80),
        )

        self.verify_signature_input = TextInput(
            hint_text="Signature in Base64",
            size_hint_y=None,
            height=dp(60),
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
            height=dp(50),
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

        layout.add_widget(Label(text="Text:", size_hint_y=None, height=dp(28)))
        layout.add_widget(self.verify_text_input)

        layout.add_widget(Label(text="Signature (Base64):", size_hint_y=None, height=dp(28)))
        layout.add_widget(self.verify_signature_input)
        
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

        tab.add_widget(self._wrap_with_about_button(page))
        self.add_widget(tab)

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
        outer.add_widget(btn_add)
        outer.add_widget(title_lbl)
        outer.add_widget(top_row)
        outer.add_widget(btn_row)
        outer.add_widget(self.selected_contact_key_preview)

        scroll.add_widget(outer)
        page.add_widget(scroll)

        tab.add_widget(self._wrap_with_about_button(page))
        self.add_widget(tab)

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
    
    def _wrap_with_about_button(self, main_widget):
        outer = BoxLayout(orientation="vertical", padding=0, spacing=dp(6))

        outer.add_widget(main_widget)

        footer = AnchorLayout(
            anchor_x="right",
            anchor_y="bottom",
            size_hint_y=None,
            height=dp(38),
        )

        link = Label(
            text='[ref=about][color=3aa3ff]About[/color][/ref]',
            markup=True,
            size_hint=(None, None),
            size=(dp(90), dp(32)),
            halign="right",
            valign="middle",
        )

        link.bind(size=lambda instance, value: setattr(instance, "text_size", value))

        link.bind(on_ref_press=lambda instance, ref: self.show_about_popup())

        footer.add_widget(link)
        outer.add_widget(footer)

        return outer
    
            
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
            text="[b][size=20][color=3aa3ff]Eliptic Signer[/color][/size][/b]\n[size=14]Version 0.1.0[/size]",
            markup=True,
            halign="left",
            valign="middle",
            size_hint_y=None,
        )
        title.bind(width=lambda instance, value: setattr(instance, "text_size", (value, None)))
        title.bind(texture_size=lambda instance, value: setattr(instance, "height", value[1]))
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
            size_hint=(0.90, 0.8),
            auto_dismiss=False,
        )

        close_link.bind(on_ref_press=lambda instance, ref: popup.dismiss())
        popup.open()
    
    def _generate_new_key_now(self):
        self.private_key = CryptoManager.generate_private_key()
        self.public_key = self.private_key.public_key()
        self.public_key_output.text = CryptoManager.public_key_to_base64(self.public_key)
        self.status_label.text = "New Ed25519 key generated in memory."
