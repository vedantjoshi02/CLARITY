import tempfile
from io import BytesIO
from unittest.mock import patch, Mock
from django.test import TestCase, Client, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.exceptions import ValidationError
from docx import Document
from .models import *
from .forms import ResourceForm, RegistrationForm
from .rag import index_resource, retrieve, answer_question

def docx_file(text='Deadlock requires mutual exclusion, hold and wait, no preemption, and circular wait.'):
    d=Document();d.add_paragraph(text);b=BytesIO();d.save(b)
    return SimpleUploadedFile('notes.docx',b.getvalue(),content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')

class ClarityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo',verbosity=0)
        cls.admin=User.objects.create_superuser(username='owner',email='owner@example.test',password='OwnerSecure!2387')
        cls.student=User.objects.create_user(username='learner',email='student@example.test',password='LearnerSecure!2387',first_name='Omi')
        cls.profile=StudentProfile.objects.create(user=cls.student,full_name='Omi Student',enrollment='2026CSE001',year=AcademicYear.objects.get(number=2))
        cls.os=Subject.objects.get(code='CS202');cls.other=Subject.objects.get(code='CS301')
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        setting=override_settings(MEDIA_ROOT=self.temp.name,LLM_PROVIDER='disabled');setting.enable();self.addCleanup(setting.disable)
        self.client.force_login(self.student)
    def resource(self,subject=None,approved=True):
        r=Resource.objects.create(subject=subject or self.os,title='Deadlock notes',kind='notes',file=docx_file(),uploaded_by=self.admin,approved=approved)
        self.assertTrue(index_resource(r));return r
    def test_public_pages(self):
        self.client.logout()
        for url in ['/','/register/','/login/','/admin-login/']: self.assertEqual(self.client.get(url).status_code,200,url)
    def test_student_pages(self):
        r=self.resource()
        for url in ['/dashboard/','/subjects/','/subjects/?semester=3','/resources/',f'/subjects/{self.os.pk}/',f'/resources/{r.pk}/','/profile/','/assistant/']: self.assertEqual(self.client.get(url).status_code,200,url)
    def test_admin_pages(self):
        self.client.force_login(self.admin);r=self.resource()
        for url in ['/manage/','/manage/students/','/manage/students/?year=2',f'/manage/students/{self.profile.pk}/','/manage/academics/','/manage/academics/subject/new/?year=2&semester={self.os.semester_id}','/manage/resources/new/',f'/manage/resources/{r.pk}/edit/','/manage/ai/',f'/manage/students/{self.profile.pk}/promote/']: self.assertEqual(self.client.get(url).status_code,200,url)
    def test_registration_unique_email_and_hash(self):
        self.client.logout();data={'full_name':'Test Student','email':'NEW@EXAMPLE.TEST','enrollment':'2026cse009','year':self.profile.year_id,'password':'UniqueSecure!8493','confirm_password':'UniqueSecure!8493'}
        self.assertEqual(self.client.post('/register/',data).status_code,302)
        user=User.objects.get(email='new@example.test');self.assertTrue(user.check_password(data['password']));self.assertEqual(user.profile.enrollment,'2026CSE009');self.assertFalse(user.is_staff)
        data['enrollment']='OTHER';self.assertContains(self.client.post('/register/',data),'already exists')
    def test_password_and_enrollment_validation(self):
        form=RegistrationForm({'full_name':'Test','email':'other@example.test','enrollment':self.profile.enrollment,'year':self.profile.year_id,'password':'123','confirm_password':'123'})
        self.assertFalse(form.is_valid());self.assertIn('enrollment',form.errors)
    def test_separate_logins(self):
        self.client.logout();self.assertEqual(self.client.post('/login/',{'identity':'STUDENT@EXAMPLE.TEST','password':'LearnerSecure!2387'}).status_code,302)
        self.client.logout();self.assertContains(self.client.post('/admin-login/',{'identity':'learner','password':'LearnerSecure!2387'}),'incorrect')
        self.assertEqual(self.client.post('/admin-login/',{'identity':'owner','password':'OwnerSecure!2387'}).status_code,302)
    def test_student_cannot_admin(self):
        for url in ['/manage/','/manage/students/','/manage/students/?export=csv','/manage/academics/','/manage/resources/new/','/manage/ai/']: self.assertEqual(self.client.get(url).status_code,403,url)
    def test_year_scoping(self):
        good=self.resource();bad=self.resource(self.other)
        self.assertEqual(self.client.get(f'/resources/{good.pk}/download/').status_code,200)
        for url in [f'/resources/{bad.pk}/',f'/resources/{bad.pk}/download/',f'/subjects/{self.other.pk}/','/private_media/'+bad.file.name]: self.assertEqual(self.client.get(url).status_code,404)
        self.assertEqual(self.client.get('/resources/?subject='+str(self.other.pk)).context['page'].paginator.count,0)
    def test_drafts_hidden(self):
        r=self.resource(approved=False);self.assertEqual(self.client.get(f'/resources/{r.pk}/download/').status_code,404);self.assertEqual(retrieve(self.student,self.os,'deadlock'),[])
    def test_promotion_changes_access_and_replay_blocked(self):
        old=self.resource();new=self.resource(self.other);self.client.force_login(self.admin);url=f'/manage/students/{self.profile.pk}/promote/'
        self.client.get(url);self.profile.refresh_from_db();self.assertEqual(self.profile.year.number,2)
        self.client.post(url,{'expected_year':self.profile.year_id});self.client.post(url,{'expected_year':self.profile.year_id})
        self.profile.refresh_from_db();self.assertEqual(self.profile.year.number,3);self.assertEqual(PromotionHistory.objects.count(),1)
        self.client.force_login(self.student);self.assertEqual(self.client.get(f'/resources/{old.pk}/download/').status_code,404);self.assertEqual(self.client.get(f'/resources/{new.pk}/download/').status_code,200)
    def test_fourth_year_no_promotion(self):
        self.profile.year=AcademicYear.objects.get(number=4);self.profile.save();self.client.force_login(self.admin)
        self.client.post(f'/manage/students/{self.profile.pk}/promote/',{'expected_year':self.profile.year_id});self.profile.refresh_from_db();self.assertEqual(self.profile.year.number,4);self.assertFalse(PromotionHistory.objects.exists())
    def test_deactivation_invalidates_access(self):
        c=Client();c.force_login(self.admin);c.post(f'/manage/students/{self.profile.pk}/deactivate/');self.assertEqual(self.client.get('/dashboard/').status_code,302)
    def test_csv_filter_and_formula_protection(self):
        self.profile.full_name='=1+1';self.profile.save();self.client.force_login(self.admin)
        response=self.client.get('/manage/students/?year=2&export=csv');self.assertContains(response,"'=1+1");self.assertNotContains(response,'pbkdf2');self.assertNotContains(self.client.get('/manage/students/?year=1&export=csv'),self.profile.enrollment)
    def test_file_validation(self):
        data={'year':self.os.semester.year_id,'semester':self.os.semester_id,'subject':self.os.pk,'kind':'notes','title':'Test','approved':True}
        for name,body in [('attack.pdf',b'<script>'),('bad.docx',b'bad zip'),('bad.exe',b'exe'),('big.pdf',b'%PDF-'+b'0'*(20*1024*1024))]:
            form=ResourceForm(data,{'file':SimpleUploadedFile(name,body)});self.assertFalse(form.is_valid());self.assertIn('file',form.errors)
    def test_resource_form_classifies_material_by_subject(self):
        form=ResourceForm({'year':self.os.semester.year_id,'semester':self.os.semester_id,'subject':self.os.pk,'kind':'notes','title':'Subject-wide notes'}, {'file':docx_file()})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertNotIn('unit', form.fields)
        self.assertEqual(form.cleaned_data['subject'], self.os)
    def test_upload_replace_reindex_delete(self):
        self.client.force_login(self.admin)
        response=self.client.post('/manage/resources/new/',{'year':self.os.semester.year_id,'semester':self.os.semester_id,'subject':self.os.pk,'kind':'notes','title':'Uploaded','approved':'on','file':docx_file()});self.assertEqual(response.status_code,302)
        r=Resource.objects.get(title='Uploaded');self.assertEqual(r.status,'ready');self.assertGreater(r.chunks.count(),0)
        self.client.post(f'/manage/resources/{r.pk}/edit/',{'year':self.os.semester.year_id,'semester':self.os.semester_id,'subject':self.os.pk,'kind':'notes','title':'Replaced','approved':'on','file':docx_file('Memory management allocates memory to processes. Paging divides memory into frames and logical addresses into pages.')});r.refresh_from_db();self.assertNotIn('Deadlock',r.chunks.first().text)
        self.client.post(f'/manage/resources/{r.pk}/reindex/');self.assertEqual(r.chunks.count(),1)
        self.client.post(f'/manage/resources/{r.pk}/delete/');self.assertFalse(Resource.objects.filter(pk=r.pk).exists())
    def test_pdf_extraction(self):
        import pymupdf
        d=pymupdf.open();p=d.new_page();p.insert_text((72,72),'Deadlock: mutual exclusion, hold and wait, no preemption, circular wait.')
        r=Resource.objects.create(subject=self.os,title='PDF',kind='notes',file=SimpleUploadedFile('text.pdf',d.tobytes()),uploaded_by=self.admin);d.close();self.assertTrue(index_resource(r));self.assertEqual(r.chunks.first().page,1)
    def test_pptx_extraction(self):
        from pptx import Presentation
        from pptx.util import Inches
        presentation=Presentation()
        slide=presentation.slides.add_slide(presentation.slide_layouts[5])
        box=slide.shapes.add_textbox(Inches(1), Inches(1), Inches(5), Inches(1))
        box.text='CPU scheduling selects a process from the ready queue.'
        data=BytesIO();presentation.save(data)
        uploaded=SimpleUploadedFile('lecture.pptx',data.getvalue(),content_type='application/vnd.openxmlformats-officedocument.presentationml.presentation')
        form=ResourceForm({'year':self.os.semester.year_id,'semester':self.os.semester_id,'subject':self.os.pk,'kind':'notes','title':'Lecture slides'},{'file':uploaded})
        self.assertTrue(form.is_valid(),form.errors)
        resource=Resource(subject=self.os,title='Lecture slides',kind='notes',file=uploaded,uploaded_by=self.admin)
        resource.save()
        self.assertTrue(index_resource(resource))
        self.assertIn('CPU scheduling',resource.chunks.first().text)
        self.assertEqual(resource.chunks.first().page,1)

    def test_empty_document_status(self):
        r=Resource.objects.create(subject=self.os,title='Empty',kind='notes',file=docx_file(''),uploaded_by=self.admin);self.assertFalse(index_resource(r));r.refresh_from_db();self.assertEqual(r.status,'failed');self.assertIn('No readable text',r.processing_error)
    def test_rag_scope_and_insufficient(self):
        self.resource();self.resource(self.other);self.assertTrue(retrieve(self.student,self.os,'Explain deadlock conditions'));self.assertEqual(retrieve(self.student,self.other,'Explain deadlock conditions'),[]);self.assertEqual(answer_question(self.student,self.os,'Quantum chromodynamics',6,'answer')[2],'insufficient')
    def test_chat_save_and_wrong_subject(self):
        self.resource();response=self.client.post('/assistant/',{'year':self.os.semester.year_id,'semester':self.os.semester_id,'subject':self.os.pk,'marks':6,'mode':'answer','question':'Explain deadlock conditions'},follow=True);self.assertContains(response,'SOURCE EXCERPTS');self.assertEqual(ChatHistory.objects.count(),1);self.assertEqual(AIUsage.objects.count(),1)
        response=self.client.post('/assistant/',{'subject':self.other.pk,'marks':6,'mode':'answer','question':'Explain deadlock conditions'});self.assertContains(response,'Select a valid choice');self.assertEqual(ChatHistory.objects.count(),1)
    def test_history_private_and_withdrawn(self):
        r=self.resource();self.client.post('/assistant/',{'year':self.os.semester.year_id,'semester':self.os.semester_id,'subject':self.os.pk,'marks':6,'mode':'answer','question':'Explain deadlock conditions'});chat=ChatHistory.objects.first();self.client.force_login(self.admin);self.assertEqual(self.client.get(f'/assistant/?chat={chat.pk}').status_code,404)
        r.approved=False;r.save();self.client.force_login(self.student);self.assertContains(self.client.get(f'/assistant/?chat={chat.pk}'),'withdrawn')
    @override_settings(LLM_PROVIDER="gemini")
    @patch("academy.rag.get_gemini_client")
    def test_gemini_answer_from_approved_material(self, get_client):
        self.resource()
        model = get_client.return_value.__enter__.return_value.models
        model.generate_content.return_value = Mock(text="Mutual exclusion is one condition [1].", candidates=[])
        response = self.client.post("/assistant/", {
            "subject": self.os.pk, "marks": 10, "mode": "answer", "question": "Explain deadlock."
        }, follow=True)
        self.assertContains(response, "Mutual exclusion is one condition [1].")
        self.assertEqual(AIUsage.objects.get().provider, "gemini")
        prompt = model.generate_content.call_args.kwargs["contents"]
        self.assertIn("Marks: 10", prompt)
        self.assertIn("circular wait", prompt)
        model.embed_content.assert_not_called()

    @override_settings(LLM_PROVIDER="gemini")
    @patch("academy.rag.get_gemini_client")
    def test_gemini_answers_with_empty_library_and_retries_token_limit(self, get_client):
        model = get_client.return_value.__enter__.return_value.models
        model.generate_content.side_effect = [
            Mock(text=None, candidates=[Mock(finish_reason="MAX_TOKENS")]),
            Mock(text="Paging divides memory into fixed-size blocks.", candidates=[]),
        ]
        answer, sources, provider = answer_question(self.student, self.os, "Explain paging", 4, "answer")
        self.assertIn("General subject knowledge", answer)
        self.assertIn("Paging divides memory", answer)
        self.assertEqual(sources, [])
        self.assertEqual(provider, "gemini")
        first, second = model.generate_content.call_args_list
        self.assertGreater(second.kwargs["config"].max_output_tokens, first.kwargs["config"].max_output_tokens)

    @override_settings(LLM_PROVIDER="gemini")
    @patch("academy.rag.get_gemini_client")
    def test_source_specific_request_requires_a_match(self, get_client):
        _, sources, provider = answer_question(
            self.student, self.os, "Explain deadlock according to the uploaded notes.", 6, "answer"
        )
        self.assertEqual((sources, provider), ([], "insufficient"))
        get_client.assert_not_called()

    @override_settings(LLM_PROVIDER="gemini")
    @patch("academy.rag.get_gemini_client")
    def test_generation_quota_error_keeps_excerpts(self, get_client):
        self.resource()
        model = get_client.return_value.__enter__.return_value.models
        error = RuntimeError("Provider details")
        error.code = 429
        model.generate_content.side_effect = error
        answer, sources, provider = answer_question(self.student, self.os, "Explain deadlock", 4, "answer")
        self.assertIn("usage limit", answer)
        self.assertIn("SOURCE EXCERPTS", answer)
        self.assertNotIn("Provider details", answer)
        self.assertTrue(sources)
        self.assertEqual(provider, "error")

    @override_settings(LLM_PROVIDER="gemini", GEMINI_API_KEY="test-only", AI_SEMANTIC_RETRIEVAL=True)
    @patch("academy.rag.embed_texts", side_effect=TimeoutError)
    def test_embedding_error_does_not_block_indexing_or_retrieval(self, embed):
        resource = self.resource()
        self.assertEqual(resource.chunks.first().embedding, [])
        self.assertTrue(retrieve(self.student, self.os, "Explain deadlock conditions"))
        embed.assert_called_once()

    def test_csrf_and_get_safety(self):
        c=Client(enforce_csrf_checks=True);c.force_login(self.admin);self.assertEqual(c.post(f'/manage/students/{self.profile.pk}/deactivate/').status_code,403);self.assertEqual(self.client.get('/logout/').status_code,405)
    def test_semester_validation(self):
        with self.assertRaises(ValidationError): Semester(number=7,year=AcademicYear.objects.get(number=1)).full_clean()
    def test_academic_crud_is_scoped_to_selected_year_and_semester(self):
        self.client.force_login(self.admin)
        url=f'/manage/academics/subject/new/?year={self.os.semester.year_id}&semester={self.os.semester_id}'
        response=self.client.get(url)
        self.assertEqual(response.status_code,200)
        self.assertEqual(list(response.context['form'].fields['semester'].queryset), list(Semester.objects.filter(year=self.os.semester.year)))
        response=self.client.post(url,{'semester':self.os.semester_id,'name':'New subject','code':'NEW001','description':'Testing'})
        self.assertEqual(response.status_code,302)
        subject=Subject.objects.get(code='NEW001')
        self.assertEqual(subject.semester_id,self.os.semester_id)
        self.client.post(f'/manage/academics/subject/{subject.pk}/delete/')
        self.assertFalse(Subject.objects.filter(pk=subject.pk).exists())
    def test_rate_limiting(self):
        from .views import limited
        self.assertFalse(limited('testing',1,60));self.assertTrue(limited('testing',1,60))
