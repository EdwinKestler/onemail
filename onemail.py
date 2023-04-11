import sys
import poplib
import json
import socket
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QTextEdit, QLineEdit, QHBoxLayout, QFormLayout

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
        self.setWindowTitle('Simple POP3 Email Reader')
        self.setGeometry(100, 100, 600, 400)

        self.load_settings()
    
    def connect_to_email(self):
        self.email_server = self.server_input.text()
        self.email_user = self.user_input.text()
        self.email_password = self.password_input.text()

        self.save_settings()
        self.load_email() 


    def load_settings(self):
        try:
            with open('settings.json', 'r') as f:
                settings = json.load(f)
                self.server_input.setText(settings['email_server'])
                self.user_input.setText(settings['email_user'])
                self.password_input.setText(settings['email_password'])
        except FileNotFoundError:
            pass

    def save_settings(self):
        settings = {
            'email_server': self.email_server,
            'email_user': self.email_user,
            'email_password': self.email_password
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
            email_msg = server.retr(self.current_email + 1)[1]
            email_text = '\n'.join([line.decode('utf-8') for line in email_msg])

            subject = 'Subject: Not Found'
            for line in email_msg:
                if line.startswith(b'Subject:'):
                    subject = line.decode('utf-8')
                    break

            self.subject_label.setText(subject)
            self.email_body.setPlainText(email_text)

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