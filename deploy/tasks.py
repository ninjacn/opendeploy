from __future__ import absolute_import, unicode_literals
from opendeploy.celery import app
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

@app.task
def add(x, y):
    return x + y

@app.task
def send_mail():
    # from_email = 'service@ninjacn.com'
    subject, from_email, to = 'test', 'service@ninjacn.com', 'x@ninjacn.com'
    body = render_to_string('workflow/emails/index.html', {
        'username': 'yaoming'
    })
    msg = EmailMultiAlternatives(subject, body, from_email, [to])
    msg.attach_alternative(body, "text/html")
    return msg.send()
