from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect
from django.core.files.storage import FileSystemStorage
import os.path
from datetime import datetime
import json

# Create your views here.

ErrMsgs = {
	'admin-not-logged-in': '您尚未登录。请先以管理员身份登录。',
	'admin-login-error': '用户名或者密码错误，请重新尝试登录。',
}

DistrictNames = {
	'bsdadmin': 'Brossard',
	'logadmin': 'Longueuil',
	'mtladmin': 'Montreal',
	'cdnadmin': 'CDN',
}

def homepage(request):
	context = {}
	return render(request, 'homepage.html', context)


def adminlogin(request):
	context = {}
	if request.user.is_authenticated:
		context['authenticated'] = True
		context['heading'] = '管理员功能'
		context['username'] = request.user.username
		return render(request, 'adminlogin.html', context)
	elif request.POST:
		if 'login-btn' in request.POST:
			username = request.POST['admin-name']
			password = request.POST['admin-pwd']
			user = authenticate(username=username, password=password)
			if user is not None:
				login(request, user)
				context['authenticated'] = True
				context['heading'] = '管理员功能'
				context['username'] = request.user.username
				return render(request, 'adminlogin.html', context)
			else: 
				context['authenticated'] = False
				context['heading'] = '管理员登录'
				context['login_error'] = True
				context['errmsg'] = ErrMsgs['admin-login-error']
				return render(request, 'adminlogin.html', context)
		else:
			context['authenticated'] = False
			context['heading'] = '管理员登录'
			return render(request, 'adminlogin.html', context)
	else:
		context['authenticated'] = False
		context['heading'] = '管理员登录'
		return render(request, 'adminlogin.html', context)


def adminlogout(request):
    logout(request)
    return redirect('/mtlstory/admin/')


def createnotice(request):
	context = {}
	if not request.user.is_authenticated:
		return redirect('/mtlstory/admin/')
	elif request.POST:
		if 'publish-notice' in request.POST:
			if request.FILES['activity-1-img']
				imgfile = request.FILES['activity-1-img']
				filename = 'activity-1'
				imgurl = upload_activity_img(filename, imgfile)
				return render(request, 'homepage.html', context)
			else:	
				return render(request, 'homepage.html', context)
		else:
			return render(request, 'adminlogin.html', context)

	else: 
		username = request.user.username
		district = DistrictNames[username]
		context['authenticated'] = True
		context['username'] = username
		context['district_name'] = district
		context['heading'] = '创建新故事会通知'
		default_notice = set_default_notice(district)
		context.update(default_notice)
		return render(request, 'createnotice.html', context)



def set_default_notice(district):
	places = {
		'Brossard': 'Bibliothèque de Brossard (Brossard图书馆儿童活动区)',
		'Longueuil': 'Bibliothèque Georges-Dor',
		'CDN': 'CDN图书馆儿童活动室（地下一层）',
		'Montreal': 'Montreal library'
	}
	addresses = {
		'Brossard': '7855 Ave San Francisco, Brossard J4X 2A4',
		'Longueuil': '2760 chemin de Chambly, Longueuil J4L 1M6',
		'CDN': '5290 Chemin de la Côté-des-Neiges, Montréal H3T 1Y3',
		'Montreal': '5290 Chemin de la Côté-des-Neiges, Montréal H3T 1Y3',
	}

	default_notice = {}
	default_notice['story_maxsize'] = '20' 
	default_notice['story_site'] = places[district]
	default_notice['story_address'] = addresses[district]

	return default_notice

def upload_activity_img(filename, imgfile):
    fs = FileSystemStorage()
    ext = os.path.splitext(imgfile.name)[1]
    fname = fs.save(filename+ext, imgfile)
    return fs.url(fname)
