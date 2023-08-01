import smtplib

server = "smtp.gmail.com"
port = 587
sender = input("Enter sender's the email ID: ")
password = input("Enter sender's Password : ")
receiver = input("Enter the email id of receiver :")

subject = input("Enter the subject :")
message = input("Enter the message :")

body = '''\
Subject: {}

{}'''.format(subject, message)

# Send email
connection = smtplib.SMTP(server, port)
connection.starttls()

connection.login(sender, password)
connection.sendmail(sender, receiver, body)

connection.close()


