from io import BytesIO

from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.db import transaction

from docx import Document

from academy.models import *
from academy.rag import index_resource


class Command(BaseCommand):

    help = (
        'Create the 4-year/8-semester academic structure '
        'and optional original sample resources.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--resources',
            action='store_true'
        )

    @transaction.atomic
    def handle(self, *args, **options):

        # ==========================================
        # STEP 1: CREATE FOUR ACADEMIC YEARS
        # ==========================================

        academic_years = [
            'First Year',
            'Second Year',
            'Third Year',
            'Fourth Year'
        ]

        for number, label in enumerate(academic_years, 1):

            year, created = AcademicYear.objects.get_or_create(
                number=number,
                defaults={
                    'label': label
                }
            )

            # Correct an existing academic year label
            if year.label != label:
                year.label = label
                year.save(update_fields=['label'])

            self.stdout.write(
                f'Academic year ready: {year.label}'
            )

        # ==========================================
        # STEP 2: CREATE ALL EIGHT SEMESTERS
        # ==========================================

        for year_number in range(1, 5):

            year = AcademicYear.objects.get(
                number=year_number
            )

            semester_numbers = [
                (year_number * 2) - 1,
                year_number * 2
            ]

            for semester_number in semester_numbers:

                semester, created = Semester.objects.get_or_create(
                    number=semester_number,
                    defaults={
                        'year': year
                    }
                )

                # Correct semester-year association
                if semester.year_id != year.id:

                    semester.year = year

                    semester.save(
                        update_fields=['year']
                    )

                self.stdout.write(
                    f'  Semester {semester_number} '
                    f'belongs to {year.label}'
                )

        # ==========================================
        # STEP 3: CREATE SAMPLE SUBJECTS
        # ==========================================

        subjects = [

            (
                1,
                'MA101',
                'Engineering Mathematics I',
                'Build a foundation in mathematical thinking.'
            ),

            (
                2,
                'CS102',
                'Programming Fundamentals',
                'From first principles to your first program.'
            ),

            (
                3,
                'CS201',
                'Data Structures',
                'Organize data. Think through better solutions.'
            ),

            (
                3,
                'CS202',
                'Operating Systems',
                'Explore what happens behind every process.'
            ),

            (
                3,
                'EC201',
                'Digital Electronics',
                'Connect logic, circuits, and computation.'
            ),

            (
                3,
                'MA201',
                'Mathematics III',
                'Find patterns in probability and statistics.'
            ),

            (
                4,
                'CS203',
                'Database Management',
                'Understand how information comes together.'
            ),

            (
                4,
                'CS204',
                'Computer Networks',
                'Learn how connected systems communicate.'
            ),

            (
                5,
                'CS301',
                'Algorithms',
                'Design efficient approaches to complex problems.'
            ),

            (
                6,
                'CS302',
                'Machine Learning',
                'Explore how systems learn from data.'
            ),

            (
                7,
                'CS401',
                'Distributed Systems',
                'Reason about systems working together.'
            ),

            (
                8,
                'CS402',
                'Project & Research',
                'Bring your ideas into the world.'
            ),
        ]

        for semester_number, code, name, description in subjects:

            semester = Semester.objects.get(
                number=semester_number
            )

            Subject.objects.get_or_create(
                code=code,
                defaults={
                    'semester': semester,
                    'name': name,
                    'description': description
                }
            )

        self.stdout.write(
            self.style.SUCCESS(
                'Sample subjects checked successfully.'
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                'Academic structure initialized successfully!'
            )
        )

        # ==========================================
        # STEP 4: OPTIONAL SAMPLE RESOURCES
        # ==========================================

        if options['resources']:

            admin = User.objects.filter(
                is_superuser=True
            ).first()

            if not admin:

                self.stderr.write(
                    'Create an administrator using createsuperuser first.'
                )

                return

            examples = [

                (
                    'CS202',
                    'notes',
                    'Deadlocks: the four necessary conditions',
                    'A deadlock is a situation in which a set of processes '
                    'is blocked because each process is waiting for a '
                    'resource held by another process in the set. Four '
                    'conditions are necessary for deadlock: mutual '
                    'exclusion, hold and wait, no preemption, and '
                    'circular wait.'
                ),

                (
                    'CS201',
                    'notes',
                    'Arrays & linked lists: a comparison',
                    'An array stores elements in contiguous memory '
                    'locations. Indexed access takes O(1) time. A linked '
                    'list stores nodes in noncontiguous memory. Each '
                    'node contains data and a link to another node.'
                ),

                (
                    'CS201',
                    'important',
                    'Practice questions: data structures',
                    'Original sample practice questions, not official '
                    'previous-year papers. Compare arrays and linked '
                    'lists. Explain linked list traversal. Define a '
                    'stack and explain push and pop operations.'
                ),

                (
                    'CS202',
                    'syllabus',
                    'Sample course outline: operating systems',
                    'Illustrative course outline covering processes and threads, '
                    'CPU scheduling, memory management, deadlocks, and file systems.'
                ),

            ]

            for code, kind, title, content in examples:

                if Resource.objects.filter(
                    title=title
                ).exists():

                    continue

                subject = Subject.objects.get(
                    code=code
                )

                doc = Document()

                doc.add_heading(title, 0)

                doc.add_paragraph(
                    'CLARITY - Original demonstration resource'
                )

                doc.add_paragraph(content)

                buffer = BytesIO()

                doc.save(buffer)

                resource = Resource(
                    subject=subject,
                    kind=kind,
                    title=title,
                    description=(
                        'Original sample for testing CLARITY. '
                        'Replace with approved college material.'
                    ),
                    uploaded_by=admin
                )

                resource.file.save(
                    'sample.docx',
                    ContentFile(buffer.getvalue()),
                    save=True
                )

                index_resource(resource)

            self.stdout.write(
                self.style.SUCCESS(
                    'Original sample resources created and indexed.'
                )
            )