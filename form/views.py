from django.shortcuts import render,redirect
from django.conf import settings
import random
from django.core.mail import send_mail
from django.http import JsonResponse,HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import ssl
import json


verification_codes = {}
RECAPTCHA_SITE_KEY='6LfIjXorAAAAAF_-h9v731lG4X8gdOLUpwmYxzgp'
RECAPTCHA_SECRET_KEY='6LfIjXorAAAAAMGK5XwY3wAOwbD89BVvn5UgyyEm'
otp_sessions = {} 

SMTP_PORT = 587
SMTP_SERVER = "smtp.example.com"
@csrf_exempt
def submit_contact_form(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        # Extract data
        sender_email = data.get('senderEmail')  # Form builder's email
        receiver_email = data.get('receiverEmail')  # Company inbox
        form_data = data.get('formData')  # Data filled by the form user
        smtp_host = data.get('smtpHost')
        smtp_port = data.get('smtpPort', 587)  # Default port for TLS
        smtp_password = data.get('smtpPassword')
        recaptcha_token = data.get('recaptchaToken')
        mailback_enabled = data.get('mailbackEnabled', False)  # Check if mailback is enabled

        # Validate required fields
        if not sender_email or not receiver_email or not form_data:
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        # Verify reCAPTCHA token
        if recaptcha_token:
            verify_url = 'https://www.google.com/recaptcha/api/siteverify'
            response = requests.post(verify_url, data={
                'secret': RECAPTCHA_SECRET_KEY,
                'response': recaptcha_token
            })
            result = response.json()
            if not result.get("success"):
                return JsonResponse({'error': 'Failed Recaptcha Verification'}, status=400)

        # Create email content to send to the receiver (company)
        email_subject = "New Contact Form Submission"
        email_body = "You have a new contact form submission:\n\n"
        for key, value in form_data.items():
            email_body += f"{key}: {value}\n"

        try:
            # Send email to the receiver (company inbox)
            context = ssl.create_default_context()
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls(context=context)  # Secure the connection
                server.login(sender_email, smtp_password)
                
                msg = MIMEMultipart()
                msg['From'] = sender_email
                msg['To'] = receiver_email
                msg['Subject'] = email_subject
                msg.attach(MIMEText(email_body, 'plain'))

                server.sendmail(sender_email, receiver_email, msg.as_string())  # Send the email

            # If mailback is enabled, send confirmation email to the user
            if mailback_enabled:
                user_email = None
                # Find the user's email from the form data
                for key, value in form_data.items():
                    if 'email' in key.lower() and '@' in value:
                        user_email = value
                        break

                # If a valid user email is found, send a confirmation email
                if user_email:
                    try:
                        confirmation_subject = "We Received Your Submission"
                        confirmation_body = "Hi,\n\nThank you for contacting us. We’ve received your message:\n\n"
                        for key, value in form_data.items():
                            confirmation_body += f"{key}: {value}\n"
                        confirmation_body += "\nWe will get back to you shortly.\n\nBest regards,\nYour Team"

                        confirmation_msg = MIMEMultipart()
                        confirmation_msg['From'] = sender_email
                        confirmation_msg['To'] = user_email
                        confirmation_msg['Subject'] = confirmation_subject
                        confirmation_msg.attach(MIMEText(confirmation_body, 'plain'))

                        with smtplib.SMTP(smtp_host, smtp_port) as server:
                            server.starttls(context=context)
                            server.login(sender_email, smtp_password)
                            server.sendmail(sender_email, user_email, confirmation_msg.as_string())

                    except Exception as e:
                        print(f"Mailback failed: {e}")

            return JsonResponse({'message': 'Form submitted and email sent successfully!'})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid method'}, status=405)



@csrf_exempt
def recieve_contact_form(request):
    if request.method == 'POST':
        if request.content_type != 'application/json':
            return JsonResponse({'error': 'Expected application/json'}, status=400)

        try:
            data = json.loads(request.body)
            sender_email = data.get('senderEmail')
            receiver_email = data.get('receiverEmail')
            form_data = data.get('formData')
            recaptcha_token = data.get('recaptchaToken')

            if not sender_email or not receiver_email or not form_data:
                return JsonResponse({'error': 'Missing fields'}, status=400)
            
            if recaptcha_token:
                recaptcha_response = requests.post(
                    'https://www.google.com/recaptcha/api/siteverify',
                    data={
                        'secret': RECAPTCHA_SECRET_KEY,
                        'response': recaptcha_token
                    }
                )
                result = recaptcha_response.json()
                if not result.get('success'):
                    return JsonResponse({'error': 'Invalid reCAPTCHA'}, status=400)

            email_subject = "New Contact Form Submission"
            email_body = "You have a new contact form submission:\n\n"
            for key, value in form_data.items():
                email_body += f"{key}: {value}\n"

            send_mail(
                subject=email_subject,
                message=email_body,
                from_email=sender_email,
                recipient_list=[receiver_email],
                fail_silently=False,
            )

            return JsonResponse({'message': 'Form submitted successfully!'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid method'}, status=405)

def form_builder_view(request):
    return render(request, 'index.html')
