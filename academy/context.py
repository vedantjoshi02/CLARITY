from .models import AcademicYear

def navigation(request):
    return {'academic_years':AcademicYear.objects.all(),'site_name':'CLARITY'}
