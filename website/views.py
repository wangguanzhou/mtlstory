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


def createnotice(request, existed_notice_data):
	context = {}
	if not request.user.is_authenticated:
		return redirect('/mtlstory/admin/')
	elif request.POST:
		username = request.user.username
		district = DistrictNames[username]
		context['authenticated'] = True
		context['username'] = username
		context['district_name'] = district

		if 'publish-notice' in request.POST:
			notice_data = {}
			notice_data['story_theme'] = request.POST['story-theme']
			notice_data['story_date'] = request.POST['story-date']
			notice_data['story_time'] = request.POST['story-time']
			notice_data['story_host'] = request.POST['story-host']
			notice_data['story_maxsize'] = request.POST['story-maxsize']
			notice_data['story_site'] = request.POST['story-site']
			notice_data['story_address'] = request.POST['story-address']
			notice_data['register_date'] = request.POST['register-date']
			notice_data['register_time'] = request.POST['register-time']
			notice_data['activity_list'] = []

			validate_result = validate_notice_data(notice_data)
			if validate_result['err_num'] == 0:
				for activity_no in range(1):
					activity_name = 'activity-' + str(activity_no + 1)
					activity_info = request.POST[activity_name + '-info']
					if len(activity_info) > 0:
						this_activity['activity_name'] = activity_name;
						this_activity['activity_info'] = activity_info;
						if (activity_name + '-img') in request.FILES:
							try:
								activity_imgfile = request.FILES[activity_name + '-img']
								activity_filename = request.POST['story-date'][:10] + '-' + activity_name
								this_activity['activity_img_url'] = upload_activity_img(filename, imgfile)
							except:
								this_activity['activity_img_url'] = ''
						else:
								this_activity['activity_img_url'] = ''

						notice_data['actility_list'].append(this_activity)

				context['notice_data'] = notice_data
				context['succeeded'] = True
				return render(request, 'createnotice_result.html', context)
			else:
				context['notice_data'] = notice_data
				context['err_msgs'] = validate_result['err_msgs']
				context['succeeded'] = False
				return render(request, 'createnotice_result.html', context)

		else:
			return render(request, 'adminlogin.html', context)

	else: 
		username = request.user.username
		district = DistrictNames[username]
		context['authenticated'] = True
		context['username'] = username
		context['district_name'] = district
		context['heading'] = '创建新故事会通知'
		if existed_notice_data == None:
			notice_data = set_default_notice(district)
		else:
			notice_data = existed_notice_data	
		context.update(notice_data)
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

def validate_notice_data(notice_data):
	# check story-date
	result = {}
	err_num = 0
	err_msgs = []

	story_date = notice_data['story_date']
	story_date_err = False
	if len(story_date) < 10:
		story_date_err = True
	else:
		try:
			datetime.strptime(story_date[:10], '%Y-%m-%d')
		except:
			story_date_err = True
			
	if story_date_err:
		err_num = err_num + 1
		err_msgs.append('故事会活动日期缺失或者格式错误。')

	register_date = notice_data['register_date']
	register_date_err = False
	if len(register_date) < 10:
		register_date_err = True
	else:
		try:
			datetime.strptime(register_date[:10], '%Y-%m-%d')
		except:
			register_date_err = True
			
	if register_date_err:
		err_num = err_num + 1
		err_msgs.append('报名启动日期缺失或者格式错误。')



	result['err_num'] = err_num
	result['err_msgs'] = err_msgs
	return result


def upload_activity_img(filename, imgfile):
    fs = FileSystemStorage()
    ext = os.path.splitext(imgfile.name)[1]
    fname = fs.save(filename+ext, imgfile)
    return fs.url(fname)
