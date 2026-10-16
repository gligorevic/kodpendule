import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

from decouple import Config, RepositoryEmpty
from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from apps.core.email_backends import SendGridAPIBackend
from config.settings.email import configure_email


class EmailConfigurationTests(SimpleTestCase):
    def configured(self, env):
        settings = SimpleNamespace()
        with patch.dict('os.environ', env, clear=True):
            configure_email(settings, Config(RepositoryEmpty()))
        return settings

    def test_existing_key_uses_https_without_smtp(self):
        settings = self.configured({'SENDGRID_API_KEY': 'test-key'})
        self.assertEqual(settings.EMAIL_BACKEND, 'apps.core.email_backends.SendGridAPIBackend')
        self.assertEqual(settings.EMAIL_HOST, '')
        self.assertEqual(settings.EMAIL_TIMEOUT, 10)

    def test_smtp_can_be_used_without_sendgrid(self):
        settings = self.configured({'EMAIL_HOST':'smtp.example.com','EMAIL_HOST_USER':'shop@example.com','EMAIL_HOST_PASSWORD':'test-password','EMAIL_USE_SSL':'True','EMAIL_PORT':'465'})
        self.assertEqual(settings.EMAIL_BACKEND, 'django.core.mail.backends.smtp.EmailBackend')
        self.assertTrue(settings.EMAIL_USE_SSL)
        self.assertFalse(settings.EMAIL_USE_TLS)
        self.assertEqual(settings.EMAIL_PORT, 465)

    def test_no_credentials_disables_mail_instead_of_connecting_to_localhost(self):
        settings = self.configured({})
        self.assertEqual(settings.EMAIL_BACKEND,'django.core.mail.backends.dummy.EmailBackend')
        self.assertEqual(settings.EMAIL_HOST,'')


@override_settings(SENDGRID_API_KEY='secret-test-key', EMAIL_TIMEOUT=10)
class SendGridBackendTests(SimpleTestCase):
    def message(self):
        return EmailMessage('Test čćš', 'Body', 'Kod Pendule <info@kodpendule.com>', ['customer@example.com'], reply_to=['shop@example.com'])

    @patch('apps.core.email_backends.urlopen')
    def test_accepted_message_posts_correct_json_with_timeout(self, open_url):
        open_url.return_value.__enter__.return_value.status = 202
        self.assertEqual(SendGridAPIBackend().send_messages([self.message()]),1)
        request=open_url.call_args.args[0]
        payload=json.loads(request.data)
        self.assertEqual(request.full_url,'https://api.sendgrid.com/v3/mail/send')
        self.assertEqual(payload['from'],{'name':'Kod Pendule','email':'info@kodpendule.com'})
        self.assertEqual(payload['personalizations'][0]['to'],[{'email':'customer@example.com'}])
        self.assertEqual(payload['reply_to_list'],[{'email':'shop@example.com'}])
        self.assertEqual(open_url.call_args.kwargs['timeout'],10)

    @patch('apps.core.email_backends.urlopen', side_effect=HTTPError('https://api.sendgrid.com/v3/mail/send',403,'Forbidden',{},None))
    def test_rejection_is_not_success_and_is_not_retried(self, open_url):
        with self.assertRaisesRegex(RuntimeError,'HTTP 403'):
            SendGridAPIBackend().send_messages([self.message()])
        self.assertEqual(open_url.call_count,1)
        self.assertEqual(SendGridAPIBackend(fail_silently=True).send_messages([self.message()]),0)

    @patch('apps.core.email_backends.urlopen', side_effect=TimeoutError('network'))
    def test_timeout_is_not_retried(self, open_url):
        with self.assertRaises(TimeoutError):
            SendGridAPIBackend().send_messages([self.message()])
        self.assertEqual(open_url.call_count,1)

    def test_html_cc_bcc_and_attachment_are_preserved(self):
        message=EmailMultiAlternatives('Test','Text','sender@example.com',['to@example.com'],cc=['cc@example.com'],bcc=['bcc@example.com'])
        message.attach_alternative('<p>HTML</p>','text/html')
        message.attach('note.txt','Test','text/plain')
        payload=SendGridAPIBackend.payload(message)
        self.assertEqual(payload['content'][1]['type'],'text/html')
        self.assertEqual(payload['personalizations'][0]['bcc'],[{'email':'bcc@example.com'}])
        self.assertEqual(payload['attachments'][0]['content'],'VGVzdA==')


class EmailDiagnosticsTests(TestCase):
    def test_only_superusers_can_read_diagnostics(self):
        path=reverse('admin:email_diagnostics')
        self.assertEqual(self.client.get(path).status_code,302)
        user=get_user_model().objects.create_user(username='mail-staff',email='staff@example.com',password='local-test',is_staff=True)
        self.client.force_login(user)
        self.assertEqual(self.client.get(path).status_code,403)
        user.is_superuser=True;user.save()
        with override_settings(EMAIL_HOST_PASSWORD='never-show-this',SENDGRID_API_KEY='never-show-key'):
            response=self.client.get(path)
        self.assertEqual(response.status_code,200)
        self.assertNotContains(response,'never-show-this')
        self.assertNotContains(response,'never-show-key')
        self.assertEqual(self.client.post(path).status_code,405)
