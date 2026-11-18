# CLARITY

### AI-Powered Academic Resource & Examination Preparation Platform

**Project Category:** Python Full-Stack Web Application\
**Project Type:** Academic Mini-Project\
**Target Users:** Engineering College Students and Administrators\
**Primary Department:** Computer Science and Engineering (CSE)\
**Backend:** Python Django\
**Database:** SQLite\
**Frontend:** HTML, CSS, Bootstrap and JavaScript &#x20;

---

# 1. Introduction to CLARITY

CLARITY is an AI-powered academic resource management and examination preparation web application designed to help engineering students prepare effectively for their college examinations.

During examination periods, students often face difficulties finding authentic previous-year question papers, properly organized notes, reference materials, subject syllabi and important questions.

Even after collecting these resources, another problem remains: students often don't know how to write examination-oriented answers.

For example:

- How much should they write for a 4-mark question?
- Which important points should they include?
- Should they include diagrams?
- Which technical keywords are important?
- How should they structure a 6-mark or 10-mark answer?

CLARITY aims to address these problems through a centralized academic platform integrated with an AI-powered academic assistant.

The platform will provide two types of access:

1. **User (Student):** Access academic resources according to their academic year and use AI assistance for examination preparation.
2. **Admin (Administrator):** Manage students, academic years, subjects, semesters and academic resources.

The AI assistant will generate examination-oriented answers using the academic resources uploaded and approved by the administrator.

## 2. Main Objectives

The primary objectives of CLARITY are:

1. Provide a centralized platform for academic resources.
2. Organize study materials according to academic year, semester and subject.
3. Provide easy access to previous-year question papers.
4. Reduce the time students spend collecting study materials.
5. Provide AI-generated examination-oriented answers.
6. Help students understand how to structure answers according to marks.
7. Restrict academic resources according to students' registered academic years.
8. Provide administrators with centralized student management.
9. Allow administrators to promote students between academic years.
10. Improve students' examination preparation through AI-based academic assistance.

---

# 3. User Roles and Authentication System

CLARITY will have two separate login options on its homepage.

### A. User Login

This option is intended for college students.

Students who don't already have an account must register before accessing the platform.

**Registration Form**

The registration form will contain the following fields:

| Field                     | Description                         |
| ------------------------- | ----------------------------------- |
| Full Name                 | Student's complete name             |
| Email Address             | Student's valid email address       |
| Year of Study             | First, Second, Third or Fourth Year |
| College Enrollment Number | Unique college enrollment number    |
| Password                  | Password created by the student     |
| Confirm Password          | Password confirmation               |

**Registration validations:**

- Email addresses must be unique.
- Enrollment numbers must be unique.
- All fields must be compulsory.
- Passwords must satisfy security requirements.
- Passwords must be securely stored using Django's password hashing.

After successful registration, the student can log in using their email address and password.

### B. Admin Login

The administrator will have a separate login interface.

Unlike student registration, administrator accounts will not have a public registration facility.

Admin accounts will be created exclusively through the PowerShell terminal using Django's management command.

```
python manage.py createsuperuser
```

The terminal will request:

- Username
- Email address
- Password
- Password confirmation

The admin login page will contain:

| Field    | Description            |
| -------- | ---------------------- |
| Username | Administrator username |
| Password | Administrator password |

Initially, CLARITY will have only one administrator.

The administrator will have access to all academic years and all registered student records.

---

# 4. Student Dashboard

After successful login, students will be redirected to their personalized dashboard.

The dashboard will display academic information according to the year selected during registration or subsequently assigned by the administrator.

### Example: Second-Year Student

Suppose a student registers with the following details:

- Name: Rahul Sharma
- Email: [rahul@gmail.com](mailto:rahul@gmail.com)
- Enrollment Number: 2026CSE001
- Academic Year: Second Year

After login, the dashboard will display:

**Welcome, Rahul!**

Your Academic Information:

| Information         | Details                          |
| ------------------- | -------------------------------- |
| Academic Year       | Second Year                      |
| Available Semesters | Semester 3 and 4                 |
| Department          | Computer Science and Engineering |

The dashboard will contain the following sections:

1. My Subjects
2. Study Materials
3. Previous-Year Papers
4. Important Questions
5. Reference Materials
6. AI Academic Assistant
7. My Profile

Students will only see academic resources belonging to their assigned academic year.

---

# 5. Year-Wise Academic Resource Management

This is one of the most important functionalities of CLARITY.

All academic resources will be organized according to four academic years and eight semesters.

### Academic Year Structure

| Academic Year | Available Semesters       |
| ------------- | ------------------------- |
| First Year    | Semester 1 and Semester 2 |
| Second Year   | Semester 3 and Semester 4 |
| Third Year    | Semester 5 and Semester 6 |
| Fourth Year   | Semester 7 and Semester 8 |

Each semester will contain multiple subjects.

Each subject will contain different types of academic resources.

### Example Structure

```
CLARITY
  |
  |--- FIRST YEAR
  |       |
  |       |--- Semester 1
  |       |       |--- Subject 1
  |       |       |--- Subject 2
  |       |       |--- Subject 3
  |       |
  |       |--- Semester 2
  |
  |--- SECOND YEAR
  |       |
  |       |--- Semester 3
  |       |       |--- Data Structures
  |       |       |--- Digital Electronics
  |       |       |--- Discrete Mathematics
  |       |
  |       |--- Semester 4
  |               |--- Operating Systems
  |               |--- DBMS
  |
  |--- THIRD YEAR
  |       |
  |       |--- Semester 5
  |       |--- Semester 6
  |
  |--- FOURTH YEAR
          |
          |--- Semester 7
          |--- Semester 8
```

The subject names above are illustrative. Actual subjects will be entered according to the college syllabus.

### Student Access Restriction

The system must enforce academic-year restrictions through Django's backend.

For example:

- First-year students can access only semesters 1 and 2.
- Second-year students can access only semesters 3 and 4.
- Third-year students can access only semesters 5 and 6.
- Fourth-year students can access only semesters 7 and 8.

A student must not be able to access another year's resources by manually changing a URL or modifying frontend elements.

This restriction will also apply to the AI assistant's academic knowledge retrieval.

---

# 6. Administrator Dashboard

The administrator will have a separate dashboard with complete control over academic data and student management.

The admin dashboard will have five major sections:

1. Dashboard Overview
2. Student Management
3. Academic Management
4. Resource Management
5. AI Management

## 6.1 Dashboard Overview

The dashboard will provide an overall summary of CLARITY.

For example:

| Dashboard Information     | Example |
| ------------------------- | ------- |
| Total Registered Students | 250     |
| First-Year Students       | 65      |
| Second-Year Students      | 70      |
| Third-Year Students       | 60      |
| Fourth-Year Students      | 55      |
| Total Subjects            | 32      |
| Total Uploaded Resources  | 450     |

These figures will be calculated dynamically from the database.

The administrator should also be able to see recent registrations and recent resource uploads.

---

# 7. Student Management System

This is an important module that we added to the project.

The administrator must be able to access the complete information of all students registered on CLARITY.

However, student information will be organized according to academic year.

### 7.1 Year-Wise Student Directory

The Student Management section will contain four selectable options.

- First Year Students
- Second Year Students
- Third Year Students
- Fourth Year Students

Each option will display the student records belonging to that particular academic year.

### Example: Selecting Second Year

Suppose the administrator selects Second Year.

The application will display:

**SECOND YEAR STUDENTS**

Total Students: 70

| Sr. No. | Full Name    | Enrollment Number | Email                                     |
| ------- | ------------ | ----------------- | ----------------------------------------- |
| 1       | Rahul Sharma | 2026CSE001        | [rahul@gmail.com](mailto:rahul@gmail.com) |
| 2       | Amit Patil   | 2026CSE002        | [amit@gmail.com](mailto:amit@gmail.com)   |
| 3       | Priya Patil  | 2026CSE003        | [priya@gmail.com](mailto:priya@gmail.com) |
| 4       | Sneha Joshi  | 2026CSE004        | [sneha@gmail.com](mailto:sneha@gmail.com) |

The above records are illustrative.

### 7.2 Student Management Functionalities

The administrator will have the following options:

| Functionality      | Description                                         |
| ------------------ | --------------------------------------------------- |
| View Students      | Display all students belonging to the selected year |
| Search Students    | Search by name or enrollment number                 |
| View Profile       | View individual student information                 |
| Promote Student    | Promote a student to the next academic year         |
| Activate Account   | Allow a student to access CLARITY                   |
| Deactivate Account | Temporarily restrict student access                 |
| Export Records     | Download the selected year's student list as CSV    |

The administrator will also be able to see registration dates and last login information.

Student passwords will never be visible to the administrator.

---

# 8. Student Promotion System

CLARITY will include an administrator-controlled academic promotion system.

This means students will not automatically change their academic year when a new academic session begins.

The administrator will manually promote students.

### 8.1 Promote Option

Each student record will have a Promote button.

For example, when the administrator opens the Second Year student directory:

| Student Name | Enrollment Number | Action  |
| ------------ | ----------------- | ------- |
| Rahul Sharma | 2026CSE001        | Promote |
| Amit Patil   | 2026CSE002        | Promote |
| Priya Patil  | 2026CSE003        | Promote |

When the administrator clicks Promote, a confirmation message will appear.

**Example:**

```
          PROMOTE STUDENT

Student Name: Rahul Sharma

Current Academic Year: Second Year

Promote To: Third Year

Are you sure you want to
promote this student?

       [ CANCEL ]

       [ CONFIRM PROMOTION ]
```

### 8.2 Promotion Rules

| Current Academic Year | Next Academic Year   |
| --------------------- | -------------------- |
| First Year            | Second Year          |
| Second Year           | Third Year           |
| Third Year            | Fourth Year          |
| Fourth Year           | No further promotion |

### 8.3 What Happens After Promotion?

Suppose Rahul is promoted from Second Year to Third Year.

The following changes will happen automatically:

1. His academic year will change in the database.
2. He will disappear from the Second Year student directory.
3. He will appear in the Third Year student directory.
4. His accessible semesters will change from 3 and 4 to 5 and 6.
5. Third-year subjects and resources will become available.
6. Second-year resources will no longer be accessible through his normal student account.
7. His email, enrollment number and account history will remain unchanged.

### 8.4 Promotion History

I recommend maintaining a promotion history.

| Student      | Previous Year | New Year    | Promotion Date |
| ------------ | ------------- | ----------- | -------------- |
| Rahul Sharma | Second Year   | Third Year  | 10 Nov 2027    |
| Amit Patil   | First Year    | Second Year | 10 Nov 2027    |

This will help administrators track academic promotions.

---

# 9. Academic Management

The administrator will have the ability to manage academic information.

This section will contain:

- Academic year management.
- Semester management.
- Subject management.
- Unit management.

### Example

The administrator selects:

```
Academic Year: Second Year

Semester: Semester 3

Subject: Data Structures
```

The administrator can then add or edit the subject information.

Each subject can have multiple units.

For example:

```
DATA STRUCTURES

Unit 1: Introduction to Data Structures

Unit 2: Linked Lists

Unit 3: Stacks and Queues

Unit 4: Trees

Unit 5: Graphs
```

The actual units will be based on the approved syllabus.

This academic structure will also help the AI assistant retrieve relevant information more accurately.

---

# 10. Resource Management System

This module allows administrators to upload and manage academic materials.

It is the foundation of the academic resource repository.

### 10.1 Resource Categories

The administrator will be able to upload:

| Resource Type        | Description                           |
| -------------------- | ------------------------------------- |
| Notes                | Subject-wise and unit-wise notes      |
| Previous-Year Papers | University examination papers         |
| Class Test Papers    | Internal examination papers           |
| Reference Books      | Approved academic reference materials |
| Important Questions  | Important examination questions       |
| Question Bank        | Collection of subject-wise questions  |
| Syllabus             | Official subject syllabus             |
| Other Materials      | Additional academic documents         |

### 10.2 Resource Upload Form

Whenever the administrator uploads a resource, the following details will be required:

| Field           | Example                        |
| --------------- | ------------------------------ |
| Academic Year   | Second Year                    |
| Semester        | Semester 3                     |
| Subject         | Data Structures                |
| Unit            | Unit 2                         |
| Resource Type   | Notes                          |
| Resource Title  | Linked Lists                   |
| Description     | Complete notes on linked lists |
| Upload Document | linked_lists.pdf               |

**Supported file formats:**

- PDF
- DOCX

The application will validate uploaded file extensions and sizes.

### 10.3 Resource Visibility

Once the administrator uploads a resource, it will become available to eligible students.

For example:

An administrator uploads:

```
Year: Second Year

Semester: 3

Subject: Data Structures

Resource: Unit 2 Notes

File: linked_lists.pdf
```

The resource will appear in the Data Structures section of second-year students.

It will not be available to first-year, third-year or fourth-year students.

The same rule will apply to all uploaded academic resources.

---

# 11. AI Academic Assistant

This is the intelligent component of CLARITY.

The application will have one common AI chatbot with subject selection.

Instead of creating separate chatbots for every subject, students will use a common interface and select the subject they want assistance with.

### 11.1 How It Will Work

Suppose a second-year student wants help with Operating Systems.

The student:

1. Opens the AI Academic Assistant.
2. Selects Operating Systems.
3. Enters a question.
4. Specifies the required marks.
5. Receives an examination-oriented answer.

Example:

**Question:**

"Explain the four necessary conditions for deadlock."

**Maximum Marks:** 6

The AI assistant will retrieve relevant information from the Operating Systems resources uploaded by the administrator.

It will then generate an answer appropriate for a six-mark university examination question.

### 11.2 Examination-Oriented Answer Generation

The AI should understand that different questions require different answer lengths and structures.

| Marks    | Expected Answer Structure                                                         |
| -------- | --------------------------------------------------------------------------------- |
| 2 Marks  | Definition and important points                                                   |
| 4 Marks  | Definition, explanation and example                                               |
| 6 Marks  | Detailed explanation, important points and example                                |
| 8 Marks  | Comprehensive explanation with diagrams where relevant                            |
| 10 Marks | Detailed answer with introduction, explanation, diagrams, examples and conclusion |

The answer structure will also depend on the actual question and subject.

For example, a mathematical problem may require step-by-step calculations rather than a long theoretical explanation.

### 11.3 Additional AI Functionalities

The chatbot can also support:

- Explain a difficult concept.
- Generate short notes.
- Explain differences between two concepts.
- Solve previous-year questions.
- Generate important points.
- Suggest diagrams.
- Explain technical terminology.
- Generate answers according to marks.

### 11.4 Resource-Based AI Responses

One of the most important requirements is that the AI assistant should use the academic resources uploaded to CLARITY.

For this, I recommend implementing **RAG (Retrieval-Augmented Generation)**.

RAG will work as follows:

```
        ADMIN UPLOADS PDF/DOCX
                  |
                  v
          DOCUMENT PROCESSING
                  |
                  v
           TEXT EXTRACTION
                  |
                  v
             TEXT CHUNKING
                  |
                  v
             EMBEDDINGS
                  |
                  v
          VECTOR DATABASE
                  |
                  |
          STUDENT ASKS QUESTION
                  |
                  v
         SUBJECT/YEAR VALIDATION
                  |
                  v
          RELEVANT CONTENT SEARCH
                  |
                  v
             AI LANGUAGE MODEL
                  |
                  v
         EXAM-ORIENTED ANSWER
                  |
                  v
            STUDENT RESPONSE
```

This approach has several advantages:

- The AI can refer to uploaded academic materials.
- New resources can be added without retraining an AI model.
- Responses can include references to source documents.
- Subject-specific answers become more relevant.
- The system can restrict retrieval according to academic-year permissions.

**Important:** RAG does not guarantee that every answer will be correct. CLARITY should display supporting document references and indicate when the uploaded materials do not contain sufficient information.

---

# 12. Student Profile

Every student will have an individual profile.

The profile will display:

| Information         | Description               |
| ------------------- | ------------------------- |
| Full Name           | Student's registered name |
| Email Address       | Registered email          |
| Enrollment Number   | College enrollment number |
| Academic Year       | Current assigned year     |
| Available Semesters | Based on academic year    |
| Account Created     | Registration date         |
| Last Login          | Last successful login     |

Students will be able to view their profile information.

Academic-year changes will remain under administrator control.

---

# 13. AI Management

The administrator will also have a basic AI Management section.

It can display:

- Total AI queries.
- Number of students using the AI assistant.
- Most frequently selected subjects.
- AI usage statistics.
- Document processing status.
- Recently indexed academic documents.

This will help the administrator understand how students are using the AI functionality.

The administrator will not need to manage the AI model itself.

---

# 14. Complete Technology Stack

I recommend using the following technologies.

| Component           | Technology            | Purpose                       |
| ------------------- | --------------------- | ----------------------------- |
| Frontend            | HTML                  | Website structure             |
| Styling             | CSS                   | Website design                |
| UI Framework        | Bootstrap             | Responsive interface          |
| Interactivity       | JavaScript            | Dynamic functionality         |
| Backend             | Python Django         | Application logic             |
| Database            | SQLite                | Store application data        |
| Authentication      | Django Authentication | Secure login                  |
| File Upload         | Django FileField      | PDF/DOCX uploads              |
| PDF Processing      | PyMuPDF               | Extract PDF text              |
| DOCX Processing     | python-docx           | Extract DOCX text             |
| AI Integration      | LLM API               | Generate answers              |
| Knowledge Retrieval | RAG                   | Retrieve academic information |
| Vector Storage      | FAISS or ChromaDB     | Store document embeddings     |
| Development         | VS Code               | Coding environment            |
| Terminal            | PowerShell            | Project execution             |

### Why Django?

Django is suitable because it provides:

- Built-in authentication.
- Database management through ORM.
- File upload functionality.
- Admin management.
- Security features.
- URL routing.
- Template rendering.

It allows us to develop the complete application without creating separate frontend and backend projects.

### Why SQLite?

SQLite is sufficient for the initial mini-project.

It does not require a separate database server and is easy to configure.

We can migrate to PostgreSQL if the application grows.

---

# 15. Proposed Database Design

The following database models will be used.

| Model            | Purpose                                  |
| ---------------- | ---------------------------------------- |
| User             | Student and administrator authentication |
| StudentProfile   | Student information and academic year    |
| AcademicYear     | Four academic years                      |
| Semester         | Semester information                     |
| Subject          | Subject information                      |
| Unit             | Subject units                            |
| Resource         | Uploaded PDF/DOCX documents              |
| DocumentChunk    | Extracted content for AI retrieval       |
| ChatHistory      | Student-AI conversations                 |
| AIUsage          | AI usage statistics                      |
| PromotionHistory | Academic promotion records               |

### Important Database Relationships

```
                  USER
                    |
                    |
              STUDENT PROFILE
                    |
                    |
               ACADEMIC YEAR
                    |
                    |
                 SEMESTER
                    |
                    |
                  SUBJECT
                    |
                    |
                   UNIT
                    |
                    |
                 RESOURCE
                    |
                    |
              DOCUMENT CHUNKS
                    |
                    |
               AI ASSISTANT
```

Additional relationships will connect students to their chat history and academic promotion records.

---

# 16. Complete Website Page Structure

The proposed website will contain the following pages.

| No. | Page                        | Access        |
| --- | --------------------------- | ------------- |
| 1   | Home Page                   | Everyone      |
| 2   | User Registration           | Students      |
| 3   | User Login                  | Students      |
| 4   | Admin Login                 | Administrator |
| 5   | Student Dashboard           | Students      |
| 6   | Subject Selection           | Students      |
| 7   | Semester Dashboard          | Students      |
| 8   | Subject Resource Page       | Students      |
| 9   | AI Academic Assistant       | Students      |
| 10  | Student Profile             | Students      |
| 11  | Admin Dashboard             | Administrator |
| 12  | Student Management          | Administrator |
| 13  | Year-Wise Student Directory | Administrator |
| 14  | Individual Student Profile  | Administrator |
| 15  | Academic Management         | Administrator |
| 16  | Resource Upload             | Administrator |
| 17  | Resource Management         | Administrator |
| 18  | AI Management               | Administrator |

---

# 17. Complete Project Workflow

Let's understand the entire working of CLARITY.

### Student Workflow

```
              OPEN CLARITY
                    |
                    v
             SELECT USER LOGIN
                    |
                    v
             CREATE ACCOUNT
                    |
                    v
           ENTER REGISTRATION DATA
                    |
                    v
             SELECT ACADEMIC YEAR
                    |
                    v
              STUDENT LOGIN
                    |
                    v
             STUDENT DASHBOARD
                    |
                    v
            VIEW AVAILABLE SEMESTERS
                    |
                    v
              SELECT SUBJECT
                    |
              +-----+------+
              |            |
              v            v
          RESOURCES    AI ASSISTANT
              |            |
              v            v
          OPEN NOTES   ASK QUESTION
              |            |
              v            v
          DOWNLOAD     SELECT MARKS
              |            |
              |            v
              |       AI RETRIEVES
              |       RELEVANT NOTES
              |            |
              |            v
              |       GENERATES ANSWER
              |            |
              +------------+
                    |
                    v
              EXAM PREPARATION
```

### Administrator Workflow

```
             OPEN CLARITY
                   |
                   v
              ADMIN LOGIN
                   |
                   v
             ADMIN DASHBOARD
                   |
          +--------+---------+
          |        |         |
          v        v         v
       STUDENTS SUBJECTS  RESOURCES
          |        |         |
          v        v         v
      SELECT YEAR ADD/EDIT  UPLOAD
          |      SUBJECTS   PDF/DOCX
          v                  |
      VIEW STUDENTS          v
          |              SELECT YEAR
          v                  |
       PROMOTE                v
          |              SELECT SEMESTER
          v                  |
     CONFIRM PROMOTION       v
          |              SELECT SUBJECT
          v                  |
     UPDATE ACADEMIC YEAR    v
                         PUBLISH RESOURCE
```

---

# 18. Development Roadmap

We should develop CLARITY in a systematic sequence.

I recommend dividing development into ten phases.

| Phase    | Development Work                                     |
| -------- | ---------------------------------------------------- |
| Phase 1  | Django project setup and folder structure            |
| Phase 2  | Homepage and login selection                         |
| Phase 3  | Student registration and authentication              |
| Phase 4  | Admin creation and authentication                    |
| Phase 5  | Database design and academic management              |
| Phase 6  | Student management and promotion system              |
| Phase 7  | PDF/DOCX resource upload and management              |
| Phase 8  | Year-wise student dashboards and access restrictions |
| Phase 9  | AI assistant and RAG integration                     |
| Phase 10 | Testing, security and UI improvements                |

### Development Strategy

We will follow one important rule:

**Every module must work properly before we move to the next module.**

For example:

- First, complete registration and login.
- Test student and admin authentication.
- Then implement academic-year management.
- Test student promotion.
- Then implement resource uploads.
- Finally, integrate AI.

This will make debugging easier.

---

# 19. Important Security and Reliability Considerations

Since CLARITY will store student information and academic documents, we should implement the following precautions:

1. Secure password hashing through Django.
2. Unique email and enrollment number validation.
3. Backend-based academic-year access restrictions.
4. Admin-only access to student records.
5. File extension and size validation.
6. Protection against unauthorized resource downloads.
7. Admin activity logs for important changes.
8. Confirmation before promoting or deactivating students.
9. AI retrieval restricted to authorized academic resources.
10. Source references for AI-generated answers.

Also, reference books should only be uploaded when the college has permission to distribute them. Faculty-provided notes and institution-approved materials are preferable.

---

# 20. Final Scope of CLARITY Version 1.0

To make the project achievable as an academic mini-project, I recommend freezing the following features for the first version.

| Module                 | Features                                            |
| ---------------------- | --------------------------------------------------- |
| Authentication         | Student registration, student login, admin login    |
| Student Dashboard      | Personalized academic dashboard                     |
| Academic Management    | Four years, eight semesters, subjects and units     |
| Resource Management    | Notes, PYPs, reference materials and question banks |
| Student Management     | Year-wise student directory                         |
| Promotion System       | Manual student promotion                            |
| AI Assistant           | Common chatbot with subject selection               |
| Answer Generation      | Examination-oriented answers                        |
| AI Knowledge Retrieval | Answers grounded in uploaded academic resources     |
| Admin Dashboard        | Statistics and management controls                  |

### Features for Future Versions

These are useful but should not delay the first working version:

- Handwritten answer evaluation.
- AI-based mock examinations.
- Automatic repeated-question analysis.
- Detailed student performance analytics.
- Advanced answer presentation evaluation.
- Mobile application.
- Multi-administrator support.

---

# 21. What Makes CLARITY Different?

CLARITY is not simply a website where students download notes.

Its main strength is the integration of three important functionalities:

**1. Centralized Academic Resources**

Students can access notes, previous-year papers, syllabi, reference materials and important questions from one location.

**2. Academic-Year-Based Access Control**

Students see only the academic resources relevant to their current year. Administrators can manage student records and promote students when they progress academically.

**3. AI-Powered Examination Assistance**

Students can ask subject-specific questions and receive answers generated using the academic resources available on the platform, with answer structures appropriate for university examinations.

Together, these functionalities create a centralized academic preparation environment.

---

# 22. Final Project Abstract

The following abstract can be used in your mini-project documentation.

**Project Title: CLARITY – AI-Powered Academic Resource and Examination Preparation Platform**

CLARITY is an AI-powered web application designed to simplify academic resource management and examination preparation for engineering students. The project addresses common problems faced by students during examination periods, including difficulty accessing previous-year question papers, properly organized notes, reference materials, syllabi and examination-oriented guidance.

The proposed system provides a centralized platform where students can register and access academic resources according to their respective academic years, semesters and subjects. The application includes separate user and administrator authentication systems. Administrators can manage student accounts, organize academic information, upload academic resources in PDF and DOCX formats, and promote students from one academic year to another.

An integrated AI-powered academic assistant allows students to select a subject, ask academic questions and receive examination-oriented answers according to the required marks. The AI assistant uses information retrieved from administrator-approved academic resources to generate relevant responses, helping students understand concepts and structure their answers effectively.

The application will be developed using Python Django, HTML, CSS, Bootstrap, JavaScript and SQLite, with AI integration and Retrieval-Augmented Generation (RAG) for academic knowledge retrieval.

The primary objective of CLARITY is to reduce the time students spend collecting study materials, improve access to academic resources and provide intelligent assistance for effective examination preparation.

---

# 23. My Final Recommendation

I consider this a well-defined and achievable CSE academic mini-project, provided we implement it in phases.

There is no need to start with complicated AI features or advanced infrastructure.

Our first target should be a fully functional academic resource management website with:

- Separate student and admin authentication.
- Year-wise student management.
- Student promotion.
- Subject and semester management.
- PDF/DOCX uploads.
- Year-based resource access.

Once this foundation works correctly, we will integrate the AI assistant.

**One architectural decision I strongly recommend:** Build CLARITY as a single Django application with properly separated modules. Avoid React, microservices and unnecessary technologies in Version 1.0.

This will keep development manageable and make it easier to explain the complete application during your project demonstration and viva.

**The next development milestone should be the complete Django folder structure, database schema and application architecture, followed by Phase 1 implementa**