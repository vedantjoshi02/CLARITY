from pathlib import Path
import zipfile
import uuid

from django import forms
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.db import transaction

from .models import *


# ==========================================
# REGISTRATION FORM
# ==========================================

class RegistrationForm(forms.Form):

    full_name = forms.CharField(max_length=120)

    email = forms.EmailField()

    year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.all(),
        label='Year of study'
    )

    enrollment = forms.RegexField(
        r'^[A-Za-z0-9/-]+$',
        max_length=40,
        label='College enrollment number'
    )

    password = forms.CharField(
        widget=forms.PasswordInput,
        help_text='At least 10 characters. Avoid common or entirely numeric passwords.'
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput
    )

    def clean_email(self):

        email = self.cleaned_data['email'].strip().lower()

        if settings.STUDENT_EMAIL_DOMAINS and email.rsplit('@', 1)[-1] not in settings.STUDENT_EMAIL_DOMAINS:
            raise forms.ValidationError('Use an institutional email address from an accepted domain.')

        if User.objects.filter(email__iexact=email).exists():

            raise forms.ValidationError(
                'An account with this email already exists.'
            )

        return email

    def clean_enrollment(self):

        value = self.cleaned_data['enrollment'].strip().upper()

        if StudentProfile.objects.filter(enrollment__iexact=value).exists():

            raise forms.ValidationError(
                'This enrollment number is already registered.'
            )

        return value

    def clean(self):

        data = super().clean()

        if data.get('password') != data.get('confirm_password'):

            self.add_error(
                'confirm_password',
                'Passwords do not match.'
            )

        if data.get('password'):

            validate_password(
                data['password'],
                User(
                    username=data.get('enrollment', ''),
                    email=data.get('email', ''),
                    first_name=data.get('full_name', '')
                )
            )

        return data

    @transaction.atomic
    def save(self):

        d = self.cleaned_data

        user = User.objects.create_user(
            username='student_' + uuid.uuid4().hex,
            email=d['email'],
            password=d['password'],
            first_name=d['full_name'].split()[0],
            is_active=not settings.STUDENT_APPROVAL_REQUIRED
        )

        StudentProfile.objects.create(
            user=user,
            full_name=d['full_name'],
            enrollment=d['enrollment'],
            year=d['year']
        )

        return user


# ==========================================
# LOGIN FORM
# ==========================================

class LoginForm(forms.Form):

    identity = forms.CharField(
        label='Email address'
    )

    password = forms.CharField(
        widget=forms.PasswordInput
    )


# ==========================================
# RESOURCE UPLOAD FORM
# ==========================================

class ResourceForm(forms.ModelForm):

    # Academic year selection
    year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.all().order_by('number'),
        label='Academic Year',
        empty_label='Select Academic Year'
    )

    # Semester selection
    semester = forms.ModelChoiceField(
        queryset=Semester.objects.none(),
        label='Semester',
        empty_label='Select Semester'
    )

    class Meta:

        model = Resource

        fields = [
            'year',
            'semester',
            'subject',
            'kind',
            'title',
            'description',
            'file'
        ]

        widgets = {

            'description': forms.Textarea(
                attrs={'rows': 3}
            ),

            'file': forms.ClearableFileInput(
                attrs={
                    'accept': '.pdf,.docx,.ppt,.pptx'
                }
            ),

        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields['semester'].queryset = Semester.objects.none()

        self.fields['subject'].queryset = Subject.objects.none()

        # ==================================
        # EDITING AN EXISTING RESOURCE
        # ==================================

        if self.instance and self.instance.pk:

            current_subject = self.instance.subject

            current_semester = current_subject.semester

            current_year = current_semester.year

            # When editing, use submitted selections if available.
            if self.is_bound:

                year_id = self.data.get('year')

                semester_id = self.data.get('semester')

                if year_id and str(year_id).isdigit():

                    self.fields['semester'].queryset = Semester.objects.filter(
                        year_id=year_id
                    )

                if semester_id and str(semester_id).isdigit():

                    self.fields['subject'].queryset = Subject.objects.filter(
                        semester_id=semester_id
                    )

            else:

                self.fields['year'].initial = current_year

                self.fields['semester'].queryset = Semester.objects.filter(
                    year=current_year
                )

                self.fields['semester'].initial = current_semester

                self.fields['subject'].queryset = Subject.objects.filter(
                    semester=current_semester
                )

                self.fields['subject'].initial = current_subject

        # ==================================
        # NEW RESOURCE
        # ==================================

        else:

            year_id = self.data.get('year')

            semester_id = self.data.get('semester')

            if year_id and str(year_id).isdigit():

                self.fields['semester'].queryset = Semester.objects.filter(
                    year_id=year_id
                )

            if semester_id and str(semester_id).isdigit():

                self.fields['subject'].queryset = Subject.objects.filter(
                    semester_id=semester_id
                )

    # ==================================
    # VALIDATE YEAR, SEMESTER AND SUBJECT
    # ==================================

    def clean(self):

        cleaned_data = super().clean()

        year = cleaned_data.get('year')

        semester = cleaned_data.get('semester')

        subject = cleaned_data.get('subject')

        if year and semester:

            if semester.year_id != year.id:

                self.add_error(
                    'semester',
                    'This semester does not belong to the selected academic year.'
                )

        if semester and subject:

            if subject.semester_id != semester.id:

                self.add_error(
                    'subject',
                    'This subject does not belong to the selected semester.'
                )

        return cleaned_data

    # ==================================
    # FILE VALIDATION
    # ==================================

    def clean_file(self):

        f = self.cleaned_data.get('file')

        if not f or not hasattr(f, 'content_type'):

            return f

        return validate_resource_file(f)


def validate_resource_file(f):
    ext = Path(f.name).suffix.lower()

    allowed = [
        '.pdf',
        '.docx',
        '.ppt',
        '.pptx'
    ]

    if ext not in allowed:

        raise forms.ValidationError(
            'Upload a PDF, DOCX, PPT or PPTX file.'
        )

    if f.size > 20 * 1024 * 1024:

        raise forms.ValidationError(
            'Maximum file size is 20 MB.'
        )

    signature = f.read(8)

    f.seek(0)

    if ext == '.pdf' and not signature.startswith(b'%PDF-'):

        raise forms.ValidationError(
            'This is not a valid PDF.'
        )

    if ext in ['.docx', '.pptx']:

        try:

            with zipfile.ZipFile(f) as archive:

                names = archive.namelist()

                total_uncompressed = sum(
                    item.file_size
                    for item in archive.infolist()
                )

                expected = (
                    'word/document.xml'
                    if ext == '.docx'
                    else 'ppt/presentation.xml'
                )

                if (
                    expected not in names
                    or total_uncompressed > 60 * 1024 * 1024
                ):

                    raise ValueError()

        except (zipfile.BadZipFile, ValueError):

            label = 'DOCX' if ext == '.docx' else 'PPTX'

            raise forms.ValidationError(
                f'Invalid or excessively large {label} file.'
            )

        finally:

            f.seek(0)

    if ext == '.ppt' and signature != bytes.fromhex(
        'D0CF11E0A1B11AE1'
    ):

        raise forms.ValidationError(
            'This is not a valid legacy PPT file.'
        )

    return f

# ==========================================
# ACADEMIC FORMS
# ==========================================

class YearForm(forms.ModelForm):

    class Meta:

        model = AcademicYear

        fields = [
            'number',
            'label'
        ]


class SemesterForm(forms.ModelForm):

    class Meta:

        model = Semester

        fields = [
            'number',
            'year'
        ]


class SubjectForm(forms.ModelForm):

    class Meta:

        model = Subject

        fields = [
            'semester',
            'name',
            'code',
            'description'
        ]


# ==========================================
# AI ASSISTANT MODES
# ==========================================

MODES = [

    ('answer', 'Exam answer'),

    ('explain', 'Explain a concept'),

    ('notes', 'Short notes'),

    ('compare', 'Compare concepts'),

    ('solve', 'Solve a previous-year question'),

    ('points', 'Important points'),

    ('diagram', 'Suggest a diagram'),

    ('terms', 'Technical terminology'),

]


# ==========================================
# AI QUESTION FORM
# ==========================================

class QuestionForm(forms.Form):

    subject = forms.ModelChoiceField(
        queryset=Subject.objects.none()
    )

    marks = forms.TypedChoiceField(
        choices=[
            (x, f'{x} marks')
            for x in [2, 4, 6, 8, 10]
        ],
        coerce=int,
        initial=6
    )

    mode = forms.ChoiceField(
        choices=MODES
    )

    question = forms.CharField(
        max_length=2000,
        widget=forms.Textarea(
            attrs={
                'rows': 4,
                'placeholder': 'For example: Explain the four necessary conditions for deadlock.'
            }
        )
    )

    def __init__(self, *args, subjects, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields['subject'].queryset = subjects

class MultipleResourceInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleResourceField(forms.FileField):
    widget = MultipleResourceInput(attrs={'accept': '.pdf,.docx,.ppt,.pptx'})

    def clean(self, data, initial=None):
        files = data or []
        if not 1 <= len(files) <= 10:
            raise forms.ValidationError('Choose between 1 and 10 documents.')
        if sum(file.size for file in files) > 60 * 1024 * 1024:
            raise forms.ValidationError('The combined upload must be 60 MB or smaller.')
        cleaned = []
        for file in files:
            try:
                cleaned.append(validate_resource_file(super().clean(file)))
            except forms.ValidationError as exc:
                raise forms.ValidationError([f'{file.name}: {message}' for message in exc.messages]) from exc
        return cleaned


class BulkResourceForm(forms.Form):
    subject = forms.ModelChoiceField(queryset=Subject.objects.all())
    kind = forms.ChoiceField(label='Resource type', choices=Resource.TYPES)
    files = MultipleResourceField(label='Documents', help_text='PDF, DOCX, PPT or PPTX. Up to 10 files, 20 MB each and 60 MB combined.')



class AnnouncementForm(forms.Form):
    year = forms.ModelChoiceField(queryset=AcademicYear.objects.all(), label='Academic year')
    title = forms.CharField(max_length=180)
    message = forms.CharField(max_length=2500, widget=forms.Textarea(attrs={'rows': 5}))
