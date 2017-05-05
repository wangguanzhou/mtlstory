from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect
from django.core.files.storage import FileSystemStorage
import os
import os.path
from datetime import datetime
import string
import random
import json

# Create your views here.

Noticefile_Path = '/opt/webapps/mtlstory/mtlstory/noticefiles/'
ErrMsgs = {
	'admin-not-logged-in': '您尚未登录。请先以管理员身份登录。',
	'admin-login-error': '用户名或者密码错误，请重新尝试登录。',
	'notice-file-not-exist': '该活动通知不存在。',
}

DistrictNames = {
	'bsdadmin': 'Brossard',
	'logadmin': 'Longueuil',
	'mtladmin': 'Montreal',
	'cdnadmin': 'CDN',
}

def homepage(request):
	context = {}
	active_notice_list = get_active_notice()
	context['num_of_active_notices'] = len(active_notice_list)
	if context['num_of_active_notices'] > 0:
		context['active_notice_list'] = active_notice_list
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
	json_data = {}
	if not request.user.is_authenticated:
		return redirect('/mtlstory/admin/')
	elif request.GET:
		username = request.user.username
		district = DistrictNames[username]
		context['authenticated'] = True
		context['username'] = username
		context['district_name'] = district

		if 'tempid' in request.GET:
			temp_id = request.GET['tempid']
			if os.path.isfile(Noticefile_Path + temp_id + '.json'):
				json_data = read_notice_file(temp_id + '.json')
				notice_data = json_data['notice_data']
			else:
				notice_data = set_default_notice(district) 
			context['notice_data'] = notice_data
			context['heading'] = '创建新故事会通知'
			return render(request, 'createnotice.html', context)
		else:
			return render(request, 'homepage.html', context)


	elif request.POST:
		username = request.user.username
		district = DistrictNames[username]
		context['authenticated'] = True
		context['username'] = username
		context['district_name'] = district

		if 'publish-notice' in request.POST:
			notice_data = {}
			notice_data['story_theme'] = request.POST['story_theme']
			notice_data['story_date'] = request.POST['story_date']
			notice_data['story_time'] = request.POST['story_time']
			notice_data['story_host'] = request.POST['story_host']
			notice_data['story_maxsize'] = request.POST['story_maxsize']
			notice_data['story_site'] = request.POST['story_site']
			notice_data['story_address'] = request.POST['story_address']
			notice_data['register_date'] = request.POST['register_date']
			notice_data['register_time'] = request.POST['register_time']
			notice_data['activity_list'] = []

			for activity_no in range(5):
				activity_name = 'activity_' + str(activity_no + 1)
				activity_name_cn = '故事会活动-' + str(activity_no + 1)
				activity_info = request.POST[activity_name + '_info']
				if (activity_name + '_img') in request.FILES:
					try:
						activity_imgfile = request.FILES[activity_name + '_img']
						activity_filename = district + '-' + request.POST['story_date'][:10] + '_' + activity_name
						activity_img_url = upload_activity_img(activity_filename, activity_imgfile)
						activity_img_exist = True
					except:
						print('Error uploading image files.')
						activity_img_exist = False
						activity_img_url = ''
				else:
					activity_img_url = ''
					activity_img_exist = False

				notice_data['activity_list'].append((activity_name, activity_name_cn, activity_info, activity_img_exist, activity_img_url))

			context['notice_data'] = notice_data

			validate_result = validate_notice_data(notice_data)
			if validate_result['err_num'] == 0:
				context['succeeded'] = True
				json_data['district'] = district
				json_data['published'] = True
				json_data['notice_data'] = notice_data
				json_filename = district + '-' + notice_data['story_date'][:10] + '.json'				
				save_notice_file(json_filename, json_data)
				return render(request, 'createnotice_result.html', context)
			else:
				context['notice_data'] = notice_data
				context['err_msgs'] = validate_result['err_msgs']
				temp_id = district + '_' + create_random_chars(8)
				context['temp_id'] = temp_id
				context['succeeded'] = False
				json_data['district'] = district
				json_data['published'] = False
				json_data['notice_data'] = notice_data
				json_filename = 'temp/' + temp_id + '.json'
				save_notice_file(json_filename, json_data)

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
		notice_data = set_default_notice(district)
		context['notice_data'] = notice_data
		return render(request, 'createnotice.html', context)

def shownotice(request):
	context = {}
	context['shownotice_error'] = False

	if request.GET:
		district = request.GET['district']
		story_date = request.GET['story_date']
		notice_filename = district + '-' + story_date + '.json'

		if os.path.isfile(Noticefile_Path + notice_filename):
			context['district'] = district
			try:
				json_data = read_notice_file(notice_filename)
				context['notice_data'] = json_data['notice_data']
			except:
				print('Error reading notice file ' + notice_filename)
		else:
			context['shownotice_error'] = True
			context['err_msgs'] = []
			context['err_msgs'].append(ErrMsgs['notice-file-not-exist'])

		return render(request, 'shownotice.html', context)
	else:
		return redirect('/mtlstory/')

def get_active_notice():
	active_notice_list = []
	for dirpath, dirnames, filenames in os.walk(Noticefile_Path, topdown=True):
		for filename in filenames:
			if os.path.splitext(filename)[1] == '.json':
				try:
					json_data = read_notice_file(filename)
					if json_data['published']:
						district = json_data['district']
						story_date = json_data['notice_data']['story_date'][:10]
						active_notice_list.append((district, story_date))
				except:
					print('Error reading notice file')
	return active_notice_list
		
	
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
	default_notice['activity_list'] = []

	activity_1_tuple = ('activity_1', '故事会活动-1', '小朋友们自我介绍； 一起唱《你好歌》。', False, '')
	default_notice['activity_list'].append(activity_1_tuple)

	for activity_no in [2, 3, 4, 5]:
		activity_name = 'activity_' + str(activity_no)
		activity_name_cn = '故事会活动-' + str(activity_no)
		activity_info = ''
		activity_img_exist = False
		activity_img_url = ''
		default_notice['activity_list'].append((activity_name, activity_name_cn, activity_info, activity_img_exist, activity_img_url))
		
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
			storyDate = datetime.strptime(story_date[:10], '%Y-%m-%d')
		except:
			story_date_err = True
			
	if story_date_err:
		err_num += 1
		err_msgs.append('故事会活动日期缺失或者格式错误。')
	elif storyDate.date() < datetime.today().date():
		err_num += 1
		err_msgs.append('故事会活动日期不能早于今天。')

	register_date = notice_data['register_date']
	register_date_err = False
	if len(register_date) < 10:
		register_date_err = True
	else:
		try:
			registerDate = datetime.strptime(register_date[:10], '%Y-%m-%d')
		except:
			register_date_err = True
			
	if register_date_err:
		err_num += 1
		err_msgs.append('报名启动日期缺失或者格式错误。')
	elif registerDate.date() < datetime.today().date():
		err_num += 1
		err_msgs.append('报名启动日期不能早于今天。')

	if not story_date_err and not register_date_err:
		if registerDate.date() > storyDate.date():
			err_num += 1
			err_msgs.append('报名启动日期不能晚于故事会活动日期。')

	result['err_num'] = err_num
	result['err_msgs'] = err_msgs
	return result


def upload_activity_img(filename, imgfile):
    fs = FileSystemStorage()
    ext = os.path.splitext(imgfile.name)[1]
    fname = fs.save(filename+ext, imgfile)
    return fs.url(fname)

def create_random_chars(size):
	return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(size))


def save_notice_file(filename, json_data):
	try:
		with open(Noticefile_Path + filename, 'w') as json_file:
			json.dump(json_data, json_file)
			json_file.close()
	except:
		print('Error writing JSON file.')

def read_notice_file(filename):
	try:
		with open(Noticefile_Path + filename, 'r') as json_file:
			json_data = json.load(json_file)
			json_file.close()
			return json_data
	except:
		print('Error reading JSON file.')

