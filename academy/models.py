import uuid
from pathlib import Path
from django.db import models
from django.db.models.functions import Lower
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator

class User(AbstractUser):
    email = models.EmailField(unique=True)
    class Meta:
        constraints = [models.UniqueConstraint(Lower('email'),name='unique_email_case_insensitive')]

class AcademicYear(models.Model):
    number = models.PositiveSmallIntegerField(unique=True,validators=[MinValueValidator(1),MaxValueValidator(4)])
    label = models.CharField(max_length=60)
    class Meta:
        ordering = ['number']
        constraints = [models.CheckConstraint(condition=models.Q(number__gte=1,number__lte=4),name='year_range')]
    def __str__(self): return self.label

class Semester(models.Model):
    number = models.PositiveSmallIntegerField(unique=True,validators=[MinValueValidator(1),MaxValueValidator(8)])
    year = models.ForeignKey(AcademicYear,on_delete=models.PROTECT,related_name='semesters')
    class Meta: ordering = ['number']
    def clean(self):
        if self.year_id and (self.number+1)//2 != self.year.number:
            raise ValidationError('Semester must belong to its matching academic year (1–2, 3–4, 5–6, 7–8).')
    def __str__(self): return f'Semester {self.number}'

class StudentProfile(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE,related_name='profile')
    full_name = models.CharField(max_length=120)
    enrollment = models.CharField(max_length=40,unique=True)
    year = models.ForeignKey(AcademicYear,on_delete=models.PROTECT,related_name='students')
    class Meta: ordering = ['full_name']
    def __str__(self): return self.full_name

class Subject(models.Model):
    semester = models.ForeignKey(Semester,on_delete=models.PROTECT,related_name='subjects')
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=30,unique=True)
    description = models.TextField(blank=True)
    class Meta: ordering = ['semester__number','name']
    def __str__(self): return f'{self.code} · {self.name}'

def private_path(instance, filename):
    return f'documents/{uuid.uuid4().hex}{Path(filename).suffix.lower()}'

class Resource(models.Model):
    TYPES = [('notes','Notes'),('pyp','Previous-year papers'),('test','Class test papers'),('book','Reference books'),('important','Important questions'),('bank','Question bank'),('syllabus','Syllabus'),('other','Other materials')]
    subject = models.ForeignKey(Subject,on_delete=models.PROTECT,related_name='resources')
    kind = models.CharField(max_length=20,choices=TYPES)
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to=private_path)
    approved = models.BooleanField(default=True)
    status = models.CharField(max_length=20,default='pending',choices=[('pending','Pending'),('ready','Indexed'),('failed','Needs attention')])
    processing_error = models.CharField(max_length=300,blank=True)
    download_count = models.PositiveBigIntegerField(default=0)
    uploaded_by = models.ForeignKey(User,on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['-created_at']
    @property
    def file_format(self):
        return Path(self.file.name).suffix.lstrip('.').upper() if self.file else 'FILE'
    def __str__(self): return self.title

class DocumentChunk(models.Model):
    resource = models.ForeignKey(Resource,on_delete=models.CASCADE,related_name='chunks')
    text = models.TextField()
    page = models.PositiveIntegerField(default=1)
    position = models.PositiveIntegerField(default=0)
    embedding = models.JSONField(default=list)
    class Meta: ordering = ['position']

class ChatHistory(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject,on_delete=models.CASCADE)
    question = models.TextField()
    marks = models.PositiveSmallIntegerField()
    mode = models.CharField(max_length=50)
    answer = models.TextField()
    sources = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['-created_at']

class AIUsage(models.Model):
    chat = models.OneToOneField(ChatHistory,on_delete=models.CASCADE)
    provider = models.CharField(max_length=30)
    elapsed_ms = models.PositiveIntegerField(default=0)

class PromotionHistory(models.Model):
    student = models.ForeignKey(StudentProfile,on_delete=models.CASCADE,related_name='promotions')
    previous_year = models.ForeignKey(AcademicYear,on_delete=models.PROTECT,related_name='+')
    new_year = models.ForeignKey(AcademicYear,on_delete=models.PROTECT,related_name='+')
    promoted_by = models.ForeignKey(User,on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['-created_at']

class ActivityLog(models.Model):
    actor = models.ForeignKey(User,on_delete=models.SET_NULL,null=True)
    action = models.CharField(max_length=250)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['-created_at']

class RateLimit(models.Model):
    key = models.CharField(max_length=100,unique=True)
    count = models.PositiveIntegerField(default=0)
    until = models.DateTimeField()


class ResourceReading(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='reading')
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='readers')
    saved_at = models.DateTimeField(null=True, blank=True)
    viewed_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student', 'resource'], name='unique_student_resource_reading'),
        ]


class Notification(models.Model):
    year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, null=True, blank=True)
    resource = models.OneToOneField(Resource, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=180, blank=True)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at', '-pk']


class NotificationRead(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student', 'notification'], name='unique_student_notification_read'),
        ]
