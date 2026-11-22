import json
import re
import tempfile
from shutil import which
from unittest import skipUnless
from unittest.mock import Mock, patch
from urllib.parse import urlsplit

import pymupdf
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import AcademicYear, Notification, NotificationRead, Resource, ResourceReading, Semester, StudentProfile, Subject, User
from .rag import index_resource, retrieve
from .tests import docx_file


class EnhancementTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.year = AcademicYear.objects.create(number=2, label='Second Year')
        cls.other_year = AcademicYear.objects.create(number=3, label='Third Year')
        semester = Semester.objects.create(number=3, year=cls.year)
        other_semester = Semester.objects.create(number=5, year=cls.other_year)
        cls.subject = Subject.objects.create(semester=semester, name='Operating Systems', code='OS')
        cls.other_subject = Subject.objects.create(semester=other_semester, name='Networks', code='CN')
        cls.admin = User.objects.create_superuser(username='owner', email='admin@example.test', password='UnusualAdmin!721')
        cls.student = User.objects.create_user(username='student', email='student@example.test', password='InitialPassword!647')
        cls.profile = StudentProfile.objects.create(
            user=cls.student, year=cls.year, enrollment='CSE204', full_name='Student Name',
        )
        cls.peer = User.objects.create_user(username='peer', email='peer@example.test', password='InitialPassword!647')
        StudentProfile.objects.create(user=cls.peer, year=cls.year, enrollment='CSE205', full_name='Another Student')

    def setUp(self):
        storage = tempfile.TemporaryDirectory()
        self.addCleanup(storage.cleanup)
        self.enterContext(override_settings(MEDIA_ROOT=storage.name, LLM_PROVIDER='disabled'))
        self.client.force_login(self.student)

    def resource(self, title='Deadlock notes', *, subject=None, approved=True, file=None):
        subject = subject or self.subject
        return Resource.objects.create(
            title=title, subject=subject,
            approved=approved, kind='notes', file=file or docx_file(),
            uploaded_by=self.admin,
        )

    def test_bookmarks_history_and_downloads_are_private_and_year_scoped(self):
        resource = self.resource()
        other = self.resource('Other year material', subject=self.other_subject)
        another = Client()
        another.force_login(self.peer)
        details = reverse('resource_detail', args=[resource.pk])
        save = reverse('save_resource', args=[resource.pk])
        download = reverse('download', args=[resource.pk])
        library = reverse('personal_library')
        self.assertEqual(self.client.get(save).status_code, 405)
        self.assertEqual(self.client.post(reverse('save_resource', args=[other.pk])).status_code, 404)
        self.assertEqual(self.client.get(details).status_code, 200)
        self.client.post(save, {'action': 'save'})
        self.client.post(save, {'action': 'save'})
        self.assertEqual(ResourceReading.objects.filter(student=self.profile, resource=resource).count(), 1)
        self.assertContains(self.client.get(library), resource.title)
        self.assertNotContains(another.get(library), resource.title)
        self.assertContains(self.client.get(library, {'tab': 'recent'}), resource.title)
        self.assertNotContains(another.get(library, {'tab': 'recent'}), resource.title)
        self.client.post(save, {'action': 'remove'})
        self.assertNotContains(self.client.get(library), resource.title)
        self.assertContains(self.client.get(library, {'tab': 'recent'}), resource.title)
        self.assertEqual(self.client.get(download).status_code, 200)
        resource.refresh_from_db()
        self.assertEqual(resource.download_count, 1)
        resource.approved = False
        resource.save(update_fields=['approved'])
        self.assertNotContains(self.client.get(library, {'tab': 'recent'}), resource.title)
        self.assertEqual(self.client.get(download).status_code, 404)
        self.assertEqual(self.client.get(reverse('analytics')).status_code, 403)
        another.force_login(self.admin)
        self.assertContains(another.get(reverse('analytics')), resource.title)

    def test_review_and_notification_workflow(self):
        self.client.force_login(self.admin)
        upload = self.client.post(reverse('resource_new'), {
            'year': self.year.pk, 'semester': self.subject.semester_id, 'subject': self.subject.pk,
            'kind': 'notes', 'title': 'New textbook notes', 'file': docx_file(), 'approved': 'on',
        })
        self.assertEqual(upload.status_code, 302)
        resource = Resource.objects.get(title='New textbook notes')
        self.assertFalse(resource.approved)
        self.assertContains(self.client.get(reverse('review_resources')), resource.title)
        publish = reverse('resource_action', args=[resource.pk, 'publish'])
        self.assertEqual(self.client.get(publish).status_code, 405)
        for _ in range(2):
            self.assertEqual(self.client.post(publish).status_code, 302)
        self.assertEqual(Notification.objects.filter(resource=resource).count(), 1)

        for year, title in [(self.year, 'Future examination'), (self.other_year, 'Private announcement')]:
            self.client.post(reverse('announcement'), {'year': year.pk, 'title': title, 'message': 'Read the updated academic calendar.'})
        self.client.force_login(self.student)
        feed = reverse('notifications')
        self.assertContains(self.client.get(feed), resource.title)
        self.assertContains(self.client.get(feed), 'Future examination')
        self.assertNotContains(self.client.get(feed), 'Private announcement')
        foreign = Notification.objects.get(title='Private announcement')
        self.assertEqual(self.client.post(reverse('read_notification', args=[foreign.pk])).status_code, 404)
        notice = Notification.objects.get(resource=resource)
        self.client.post(reverse('read_notification', args=[notice.pk]))
        self.assertTrue(NotificationRead.objects.filter(student=self.profile, notification=notice).exists())
        self.assertEqual(self.client.post(publish).status_code, 403)
        self.client.force_login(self.admin)
        self.client.post(reverse('resource_action', args=[resource.pk, 'withdraw']))
        self.client.force_login(self.student)
        self.assertNotContains(self.client.get(feed), resource.title)

    def test_subject_only_admin_routes_and_upload_forms(self):
        self.client.force_login(self.admin)
        for route in ['resource_new', 'bulk_resources']:
            self.assertNotContains(self.client.get(reverse(route)), 'name="unit"')
        self.assertEqual(self.client.get('/manage/ajax/units/').status_code, 404)
        self.assertEqual(self.client.get(reverse('academic_new', args=['unit'])).status_code, 404)

    def test_bulk_validates_every_file_and_creates_drafts(self):
        self.client.force_login(self.admin)
        url = reverse('bulk_resources')
        data = {'subject': self.subject.pk, 'kind': 'notes'}
        invalid = self.client.post(url, {**data, 'files': [docx_file(), SimpleUploadedFile('bad.pdf', b'bad')]})
        self.assertContains(invalid, 'bad.pdf')
        self.assertFalse(Resource.objects.exists())
        result = self.client.post(url, {**data, 'files': [docx_file(), docx_file()]})
        self.assertRedirects(result, reverse('review_resources'))
        self.assertEqual(Resource.objects.filter(approved=False, status='pending', subject=self.subject).count(), 2)
        draft = Resource.objects.first()
        self.assertEqual(self.client.post(reverse('resource_action', args=[draft.pk, 'reindex'])).status_code, 302)
        draft.refresh_from_db()
        self.assertEqual(draft.status, 'ready')

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', PUBLIC_BASE_URL='https://clarity.example.test')
    def test_password_reset_email_link_changes_password_and_is_single_use(self):
        self.client.logout()
        reset = reverse('password_reset')
        for email in ('wrong@example.test', self.admin.email, self.student.email.upper()):
            response = self.client.post(reset, {'email': email})
            self.assertRedirects(response, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.student.email])
        link = re.search(r'https://[^\s]+', mail.outbox[0].body).group()
        self.assertEqual(urlsplit(link).hostname, 'clarity.example.test')
        path = urlsplit(link).path
        next_path = self.client.get(path).url
        password = 'NewStrongPassword!188'
        self.assertRedirects(self.client.post(next_path, {'new_password1': password, 'new_password2': password}),
                             reverse('password_reset_complete'))
        self.student.refresh_from_db()
        self.assertTrue(self.student.check_password(password))
        self.assertContains(self.client.get(path), 'expired or been used')

    @override_settings(STUDENT_APPROVAL_REQUIRED=True, STUDENT_EMAIL_DOMAINS={'college.test'})
    def test_registration_can_require_institutional_domain_and_admin_activation(self):
        self.client.logout()
        data = {'full_name': 'New Student', 'email': 'new@example.test', 'enrollment': 'CSE209',
                'year': self.year.pk, 'password': 'UniqueStudent!0041', 'confirm_password': 'UniqueStudent!0041'}
        self.assertContains(self.client.post(reverse('register'), data), 'Use an institutional email address')
        data['email'] = 'new@college.test'
        self.assertRedirects(self.client.post(reverse('register'), data), reverse('login'))
        student = User.objects.get(email=data['email'])
        self.assertFalse(student.is_active)
        self.client.force_login(self.admin)
        self.client.post(reverse('student_action', args=[student.profile.pk, 'activate']))
        student.refresh_from_db()
        self.assertTrue(student.is_active)

    @override_settings(LLM_PROVIDER='gemini', GEMINI_API_KEY='fixture-key')
    @patch('academy.study_tools.get_gemini_client')
    def test_quiz_generation_grading_and_withdrawal(self, get_client):
        resource = self.resource()
        second = self.resource('More operating systems notes')
        draft = self.resource('Unpublished study handout', approved=False)
        other = self.resource('Out-of-year networking handout', subject=self.other_subject)
        for material in (resource, second, draft, other):
            self.assertTrue(index_resource(material))
        model = get_client.return_value.__enter__.return_value.models
        model.generate_content.return_value = Mock(candidates=[], text=json.dumps([{
            'question': 'Which condition requires exclusive access?',
            'options': ['Mutual exclusion', 'Paging', 'Scheduling', 'Buffering'],
            'correct': 0, 'topic': 'Deadlock conditions', 'explanation': 'Exclusive access is the defining property.',
            'source': 1, 'evidence': 'Deadlock requires mutual exclusion',
        }]))
        quiz_url = reverse('quiz')
        data = {'subject': self.subject.pk, 'difficulty': 'medium', 'questions': 1}
        self.assertNotContains(self.client.get(quiz_url), 'name="unit"')
        self.assertContains(self.client.post(quiz_url, {**data, 'subject': self.other_subject.pk}), 'valid choice')
        self.assertRedirects(self.client.post(quiz_url, data), quiz_url)
        prompt = model.generate_content.call_args.kwargs['contents']
        self.assertIn(resource.title, prompt)
        self.assertIn(second.title, prompt)
        self.assertNotIn(draft.title, prompt)
        self.assertNotIn(other.title, prompt)
        session = self.client.session
        session['study_quiz'] = {
            **session['study_quiz'], 'unit': 10, 'label': 'Operating Systems · Legacy unit title',
        }
        session.save()
        page = self.client.get(quiz_url)
        self.assertContains(page, '<h2>Operating Systems</h2>', html=True)
        self.assertNotContains(page, 'Legacy unit title')
        self.assertContains(page, 'Submit answers')
        self.assertNotContains(page, 'Exclusive access is the defining property.')
        quiz = page.context['quiz']
        self.assertContains(self.client.post(quiz_url, {'action': 'grade', 'quiz_id': quiz['id']}), 'Answer every question')
        wrong_option = (quiz['questions'][0]['correct'] + 1) % 4
        grade = {'action': 'grade', 'quiz_id': quiz['id'], 'answer_1': str(wrong_option)}
        self.assertRedirects(self.client.post(quiz_url, grade), quiz_url)
        page = self.client.get(quiz_url)
        self.assertContains(page, '0 / 1')
        self.assertContains(page, 'Deadlock conditions')
        self.assertContains(page, 'Correct answer: Mutual exclusion')
        resource.approved = False
        resource.save(update_fields=['approved'])
        self.assertNotContains(self.client.get(quiz_url), 'Which condition requires exclusive access?')

    @override_settings(LLM_PROVIDER='gemini', GEMINI_API_KEY='fixture-key')
    @patch('academy.study_tools.get_gemini_client')
    def test_summary_and_answer_evaluation_use_authorized_text(self, get_client):
        with pymupdf.open() as document:
            document.new_page().insert_text((72, 72), 'First page: Deadlock conditions include mutual exclusion.')
            document.new_page().insert_text((72, 72), 'Second page: Deadlock avoidance requires a safe state.')
            resource = self.resource('Deadlock PDF', file=SimpleUploadedFile('deadlock.pdf', document.tobytes()))
        self.assertTrue(index_resource(resource))
        model = get_client.return_value.__enter__.return_value.models
        model.generate_content.return_value = Mock(candidates=[], text='Practice text from AI.')
        summary = reverse('summary')
        self.assertContains(self.client.post(summary, {'resource': resource.pk, 'first_page': 2, 'last_page': 2}), 'Practice text from AI.')
        prompt = model.generate_content.call_args.kwargs['contents']
        self.assertIn('[Page 2]', prompt)
        self.assertNotIn('First page', prompt)
        self.assertContains(self.client.post(summary, {'resource': resource.pk, 'first_page': 9}), 'No indexed text')
        self.assertContains(self.client.post(reverse('evaluation'), {
            'subject': self.subject.pk, 'question': 'Explain deadlock conditions.', 'marks': 6,
            'answer': 'My answer describes mutual exclusion.',
        }), 'Practice feedback')
        prompt = model.generate_content.call_args.kwargs['contents']
        self.assertIn('My answer describes mutual exclusion.', prompt)
        self.assertIn('Deadlock PDF', prompt)

    @skipUnless(which('tesseract'), 'Tesseract is not installed')
    @override_settings(OCR_ENABLED=True, TESSERACT_COMMAND='tesseract', OCR_LANGUAGES='eng')
    def test_scanned_pdf_ocr_reaches_retrieval_with_original_page_number(self):
        phrase = 'The circular wait condition can cause deadlock.'
        with pymupdf.open() as original, pymupdf.open() as scan:
            page = original.new_page(width=640, height=280)
            page.insert_text((34, 120), phrase, fontsize=24)
            raster = page.get_pixmap()
            scan.new_page(width=640, height=280)
            page = scan.new_page(width=640, height=280)
            page.insert_image(page.rect, pixmap=raster)
            self.assertFalse(page.get_text())
            data = scan.tobytes()
        resource = self.resource('Scanned notes', file=SimpleUploadedFile('scan.pdf', data))
        self.assertTrue(index_resource(resource))
        hit = retrieve(self.student, self.subject, 'circular wait')[0]
        self.assertEqual(hit['page'], 2)
        self.assertIn('circular wait', hit['text'].lower())
