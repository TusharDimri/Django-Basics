from django.shortcuts import render
from employees.models import Employee

def home(request):
    emp_data = Employee.objects.all()
    context = {
        'emp_data':emp_data,
    }
    return render(request, 'home.html', context=context)