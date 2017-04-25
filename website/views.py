from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.

def homepage(request):
	context = {}
	return HttpResponse('<html><body><p>new design</p></body></html>')
