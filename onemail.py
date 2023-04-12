"""
_summary_: this is onemail.py app is a demo of how to use OpenAI's ChatGPT to analyze email content and generate a suggested response. one mail a time. 
_author_: Edwin Kestler
license: GNU AFFERO GENERAL PUBLIC LICENSE

    """
    
import sys
import os
import json
import re
from email import message_from_string
from email.policy import default
import openai
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QTextEdit, QLineEdit, QTabWidget, QFormLayout, QFileDialog, QLabel, QProgressBar
from imapclient import IMAPClient
from cryptography.fernet import Fernet


class EmailReader(QWidget):
    def __init__(self):
        super().__init__()

        self.current_email = 0
        self.unread_emails = []
        self.unread_email_index = 0
        self.init_ui()
    
    def init_ui(self):
        self.layout = QVBoxLayout()
         # Create a QTabWidget to organize the UI in tabs
        self.tabs = QTabWidget()

        # Create the settings tab
        self.settings_tab = QWidget()
        self.settings_layout = QVBoxLayout()

        self.form_layout = QFormLayout()

        # Add the input fields, buttons, and other UI elements...

        # Add form_layout to settings_layout
        self.settings_layout.addLayout(self.form_layout)

        # Set the layout for the settings tab and add it to the tabs
        self.settings_tab.setLayout(self.settings_layout)
        self.tabs.addTab(self.settings_tab, "Settings")

        # Create the main tab for email display and navigation
        self.main_tab = QWidget()
        self.main_layout = QVBoxLayout()

        self.email_layout = QVBoxLayout()
        self.email_layout.addWidget(self.subject_label)
        self.email_layout.addWidget(self.email_body)
        self.email_layout.addWidget(self.prev_button)
        self.email_layout.addWidget(self.next_button)

        self.main_layout.addLayout(self.email_layout)
        self.main_tab.setLayout(self.main_layout)
        self.tabs.addTab(self.main_tab, "Main")

        # Add the tabs to the main layout
        self.layout.addWidget(self.tabs)

        self.server_input = QLineEdit()
        self.form_layout.addRow('Email Server:', self.server_input)

        self.user_input = QLineEdit()
        self.form_layout.addRow('Email User:', self.user_input)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.form_layout.addRow('Email Password:', self.password_input)

        self.openai_api_key_input = QLineEdit()
        self.openai_api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.form_layout.addRow('OpenAI API Key:', self.openai_api_key_input)

        # Add the following lines to create an input field for OpenAI Organization
        self.openai_org_input = QLineEdit()
        self.form_layout.addRow('OpenAI Organization:', self.openai_org_input)

        self.layout.addLayout(self.form_layout)

        self.connect_button = QPushButton('Connect')
        self.connect_button.clicked.connect(self.connect_to_email)
        self.layout.addWidget(self.connect_button)

        # Add CSS styles to the connect button
        self.connect_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                font-size: 16px;
                margin: 4px 2px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        # Add form_layout to settings_layout
        self.settings_layout.addLayout(self.form_layout)

        # Set the layout for the settings tab and add it to the tabs
        self.settings_tab.setLayout(self.settings_layout)
        self.tabs.addTab(self.settings_tab, "Settings")

        # Create the main tab for email display and navigation
        self.main_tab = QWidget()
        self.main_layout = QVBoxLayout()

        self.subject_label = QLabel('Subject:')
        self.layout.addWidget(self.subject_label)

        self.email_body = QTextEdit()
        self.email_body.setReadOnly(True)
        self.layout.addWidget(self.email_body)

        self.prev_button = QPushButton('Previous')
        self.prev_button.clicked.connect(self.load_previous_email)
        self.layout.addWidget(self.prev_button)

        self.next_button = QPushButton('Next')
        self.next_button.clicked.connect(self.load_next_email)
        self.layout.addWidget(self.next_button)

        # Add the following lines to style the navigation buttons
        self.prev_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: 1px solid #2980b9;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.next_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: 1px solid #2980b9;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)

        self.key_input = QLineEdit()
        self.form_layout.addRow('Key File:', self.key_input)

        self.browse_button = QPushButton('Browse')
        self.browse_button.clicked.connect(self.browse_key_file)
        self.form_layout.addRow('', self.browse_button)
              
        self.setLayout(self.layout)
        self.setWindowTitle('ONEMAIL-Simple GPT4 asisted Email analyser by Edwin Kestler')
        self.setGeometry(100, 100, 600, 400)

        self.response_panel = QTextEdit()

        self.response_panel.setReadOnly(True)
        self.layout.addWidget(self.response_panel)

        self.importance_label = QLabel('Importance Score:')
        self.layout.addWidget(self.importance_label)

        self.importance_score = QProgressBar()
        self.importance_score.setStyleSheet("""
            QProgressBar {
                border: 2px solid #5DADE2;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #5DADE2;
                width: 20px;
            }
        """)
        self.layout.addWidget(self.importance_score)

        self.next_step_label = QLabel('Next Step:')
        self.layout.addWidget(self.next_step_label)

        self.next_step_dashboard = QTextEdit()
        self.layout.addWidget(self.next_step_dashboard)

        self.load_settings()
    
    def browse_key_file(self):
        key_file_path, _ = QFileDialog.getOpenFileName(self, "Select Key File", "", "Key Files (*.key);;All Files (*)")
        if key_file_path:
            self.key_input.setText(key_file_path)
    
    def connect_to_email(self):
        self.email_server = self.server_input.text()
        self.email_user = self.user_input.text()
        self.email_password = self.password_input.text()
        openai.api_key = self.openai_api_key_input.text()
        openai.organization = self.openai_org_input.text()  # Add this line to set the OpenAI Organization ID

        self.save_settings()

        self.mailbox = IMAPClient(self.email_server, ssl=True)  # Add the ssl=True parameter for a secure connection
        self.mailbox.login(self.email_user, self.email_password)
        self.mailbox.select_folder('INBOX')

        self.load_email() 
    
    def encrypt_data(self,data):
        key = self.load_key()
        f = Fernet(key)
        return f.encrypt(data.encode()).decode()

    def decrypt_data(self,data):
        key = self.load_key()
        f = Fernet(key)
        return f.decrypt(data.encode()).decode()

    def load_settings(self):
        try:
            with open('settings.json', 'r') as f:
                settings = json.load(f)
                self.server_input.setText(settings['email_server'])
                self.user_input.setText(settings['email_user'])
                if settings['key_file'] and os.path.exists(settings['key_file']):
                    self.key_input.setText(settings['key_file'])
                    self.password_input.setText(self.decrypt_data(settings['email_password']))
                    self.openai_api_key_input.setText(self.decrypt_data(settings['openai_api_key']))
                self.openai_org_input.setText(settings.get('openai_org', ''))
                self.key_input.setText(settings.get('key_file', ''))  # Load the key file path
        except FileNotFoundError:
            pass

    def save_settings(self):
        settings = {
            'email_server': self.email_server,
            'email_user': self.email_user,
            'email_password': self.encrypt_data(self.email_password),
            'openai_api_key': self.encrypt_data(self.openai_api_key_input.text()),
            'openai_org': self.openai_org_input.text(),
            'key_file': self.key_input.text(),  # Save the key file path
        }

        with open('settings.json', 'w') as f:
            json.dump(settings, f)

    def load_email(self):
        # Fetch unread emails
        self.unread_emails = self.mailbox.search('UNSEEN') 
        if self.unread_emails and self.unread_email_index < len(self.unread_emails):
            self.current_email = self.unread_emails[self.unread_email_index]
            email_msg = self.mailbox.fetch([self.current_email], ['BODY.PEEK[]'])[self.current_email][b'BODY[]']
            parsed_email = message_from_string(email_msg.decode(), policy=default)

            subject = parsed_email['Subject']
            self.subject_label.setText(subject)

            # Extract plain text part
            plain_text = None
            for part in parsed_email.walk():
                content_type = part.get_content_type()
                if content_type == 'text/plain':
                    plain_text = part.get_content()
                    break

            if plain_text:
                self.email_body.setPlainText(plain_text)

                # Submit email content to ChatGPT for analysis and suggested response
                response = openai.Completion.create(
                    engine="text-davinci-003",
                    prompt=f"This is an email i received in my gmail, outline the main idea of the conversation, separate the following by a space, list one by one the subjects, detailing names and if possible contacts, underline those that appear to be relevant in the conversation:\n\n{plain_text}",
                    max_tokens=500,
                    n=1,
                    stop=None,
                    temperature=0.7,
                    frequency_penalty=0.0,
                    presence_penalty=1.0,
                    top_p=1.0,
                )

                suggested_response = response.choices[0].text.strip()
                self.response_panel.setPlainText(suggested_response)

                # Generate an importance score and update the importance score widget
                response = openai.Completion.create(
                    engine="text-davinci-003",
                    prompt=f"Rate the importance of the following email evaluate if its something relevant to the recipient via a quantitative score from 1 to 100, 1 being not relevant or spam and 100 being something personal that should be dealt with personally:\n\n{plain_text}",
                    max_tokens=10,
                    n=1,
                    stop=None,
                    temperature=0.5,
                ).choices[0].text.strip()

                importance_score_text = re.findall(r'\d+', response.strip())
                importance_score = int(importance_score_text[0]) if importance_score_text else 0

                self.importance_label.setText(f'Importance Score: {importance_score}')
                self.importance_score.setValue(importance_score)

                # Generate next steps and update the next step dashboard
                next_steps = openai.Completion.create(
                    engine="text-davinci-003",
                    prompt=f"analize the content, in Next steps: suggest a list of what shoud be the next steps for this conversation then leave a space and recommend one of the fallowing Actions: Delete, Archive, Respond\n\n{plain_text}",
                    max_tokens=500,
                    n=1,
                    stop=None,
                    temperature=0.5,
                ).choices[0].text.strip()

                self.next_step_dashboard.setPlainText(next_steps)

            else:
                self.email_body.setPlainText("No plain text content found in this email.")
        else:
            self.subject_label.setText("No unread emails")
            self.email_body.setPlainText("")
    
    def load_key(self):
        key_file_path = self.key_input.text()
        with open(key_file_path, "rb") as key_file:
            return key_file.read()            

    def mark_email_as_read(self):
        if self.current_email:
            self.mailbox.add_flags([self.current_email], '\\Seen')

    def load_next_email(self):
        self.mark_email_as_read()
        if self.unread_email_index < len(self.unread_emails) - 1:
            self.unread_email_index += 1
            self.current_email = self.unread_emails[self.unread_email_index]
            self.load_email()

    def load_previous_email(self):
        if self.unread_email_index > 0:
            self.unread_email_index -= 1
            self.current_email = self.unread_emails[self.unread_email_index]
            self.load_email()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    email_reader = EmailReader()
    email_reader.load_settings()
    email_reader.show()
    sys.exit(app.exec())