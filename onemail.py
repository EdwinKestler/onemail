"""
_summary_: this is onemail.py app is a demo of how to use OpenAI's ChatGPT to analyze email content and generate a suggested response. one mail a time. 
_author_: Edwin Kestler
license: GNU AFFERO GENERAL PUBLIC LICENSE

    """
import sys
import poplib
import json
import socket
import re
from email import message_from_bytes
from email.policy import default
import openai
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QTextEdit, QLineEdit, QHBoxLayout, QFormLayout, QPlainTextEdit, QLabel, QProgressBar
import base64

class EmailReader(QWidget):
    def __init__(self):
        super().__init__()

        self.current_email = 0
        self.init_ui()
    
    def init_ui(self):
        self.layout = QVBoxLayout()

        self.form_layout = QFormLayout()

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

        self.setLayout(self.layout)
        self.setWindowTitle('ONEMAIL-Simple POP3 Email Reader by Edwin Kestler')
        self.setGeometry(100, 100, 600, 400)
        
        self.response_panel = QTextEdit()
        
        self.response_panel.setReadOnly(True)
        self.layout.addWidget(self.response_panel)

        self.importance_label = QLabel('Importance Score:')
        self.layout.addWidget(self.importance_label)

        self.importance_score = QProgressBar()
        self.layout.addWidget(self.importance_score)

        self.next_step_label = QLabel('Next Step:')
        self.layout.addWidget(self.next_step_label)

        self.next_step_dashboard = QTextEdit()
        self.layout.addWidget(self.next_step_dashboard)

        self.load_settings()
    
    def connect_to_email(self):
        self.email_server = self.server_input.text()
        self.email_user = self.user_input.text()
        self.email_password = self.password_input.text()
        openai.api_key = self.openai_api_key_input.text()

        self.save_settings()
        self.load_email() 

    def load_settings(self):
        try:
            with open('settings.json', 'r') as f:
                settings = json.load(f)
                self.server_input.setText(settings['email_server'])
                self.user_input.setText(settings['email_user'])
                self.password_input.setText(settings['email_password'])
                self.openai_org_input.setText(settings.get('openai_org', ''))  # Add this line to load OpenAI Organization ID
        except FileNotFoundError:
            pass

    def save_settings(self):
        settings = {
            'email_server': self.email_server,
            'email_user': self.email_user,
            'email_password': self.email_password,
            'openai_api_key': self.openai_api_key_input.text(),
            'openai_org': self.openai_org_input.text(),  # Add this line to save OpenAI Organization ID
        }

        with open('settings.json', 'w') as f:
            json.dump(settings, f)

    def load_email(self):
        try:            
            server = poplib.POP3_SSL(self.email_server, port=995)
            server.user(self.email_user)
            server.pass_(self.email_password)
        except socket.gaierror as e:
            self.subject_label.setText("Error: Connection failed")
            self.email_body.setPlainText(f"Error connecting to the email server. Please check your settings.\n\nError details: {e}")
            return

        msg_count = len(server.list()[1])
        if 0 <= self.current_email < msg_count:
            email_msg = b'\r\n'.join(server.retr(self.current_email + 1)[1])
            parsed_email = message_from_bytes(email_msg, policy=default)

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
                    prompt=f"This is an email i reeibed in my gmail i receibed, outline the main idea of th conversation, separte the following by a space,  list one by one the subjects, detailing names and if possible contacts, undeline those that appear to be revelant  in the conversation:\n\n{plain_text}",
                    max_tokens=1000,
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
                respone = openai.Completion.create(
                    engine="text-davinci-003",
                    prompt=f"Rate the importance of the following email evaluate if its somethiing relevant to the recipient via a quantitative score from 1 to 100, 1 been no revelant or spam and 100 been somthing personal that should be dealth personally:\n\n{plain_text}",
                    max_tokens=10,
                    n=1,
                    stop=None,
                    temperature=0.5,
                ).choices[0].text.strip()
                
                importance_score_text = re.findall(r'\d+', response.choices[0].text.strip())
                importance_score = int(importance_score_text[0]) if importance_score_text else 0

                self.importance_label.setText(f'Importance Score: {importance_score}')
                self.importance_score.setValue(importance_score)

                # Generate next steps and update the next step dashboard
                next_steps = openai.Completion.create(
                    engine="text-davinci-003",
                    prompt=f"Based on the email content, suggest next steps:\n\n{plain_text}",
                    max_tokens=100,
                    n=1,
                    stop=None,
                    temperature=0.5,
                ).choices[0].text.strip()

                self.next_step_dashboard.setPlainText(next_steps)

            else:
                self.email_body.setPlainText("No plain text content found in this email.")

        server.quit()

    def load_next_email(self):
        self.current_email += 1
        self.load_email()

    def load_previous_email(self):
        self.current_email -= 1
        self.load_email()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    email_reader = EmailReader()
    email_reader.load_settings()
    email_reader.show()
    sys.exit(app.exec())