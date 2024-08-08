from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings
import sys
import uuid

def send_html_email(subject, message, recipient):
    """
    Send an HTML email.
    """
    msg = EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient])
    msg.content_subtype = "html"
    response = msg.send()
    return response

def send_email_template(subject, template_name, context, recipient):
    """
    Send an email using a template.
    """
    if 'test' in sys.argv:
        return True
    
    try:
        message = render_to_string(template_name, context)
    except TemplateDoesNotExist:
        message = None

    if message:
        return send_html_email(subject, message, recipient)
    return False

def unique_random_number(model, field='account_no'):
    """
    Generate a unique random number for a given model and field.
    """
    random_number = uuid.uuid4().hex[:12].upper()
    filter_kwargs = {field: random_number}
    
    if model.objects.filter(**filter_kwargs).exists():
        return unique_random_number(model, field)
    
    return random_number
