from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.

ErrMsgs = {
	'admin-login-error': '用户名或者密码错误，请重新尝试登录。',
}

def homepage(request):
	context = {}
	return render(request, 'homepage.html', context)


def adminlogin(request):
	context = {}
	if request.user.is_authenticated:
		context['authenticated'] = True
		context['heading'] = '管理员功能'
		username = request.user.username
		return render(requeset, 'adminlogin.html', context)
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
				return render(requeset, 'adminlogin.html', context)
			else: 
				context['authenticated'] = False
				context['heading'] = '管理员登录'
				context['errmsg'] = ErrMsgs['admin-login-error']
				return render(requeset, 'adminlogin.html', context)
	else:
		context['authenticated'] = False
		context['heading'] = '管理员登录'
		return render(request, 'adminlogin.html', context)
