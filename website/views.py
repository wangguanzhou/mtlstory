from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.

def homepage(request):
	context = {}
	return render(request, 'homepage.html', context)


def adminlogin(request):
	context = {}
	return render(request, 'adminlogin.html', context)
