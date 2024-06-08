from django.shortcuts import render,get_object_or_404
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth import authenticate,logout,login as auth_login
from .models import User,Feedback,Profile
from django.contrib.auth.decorators import login_required

# Create your views here.
def register(request):
    if request.method == 'POST':
        username= request.POST.get('username')
        email=request.POST.get('email')
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        referral_code = request.POST.get('referral_code','')
        if password == confirm_password:
            if User.objects.filter(username=username).exists():
                messages.info(request,'Username  Already Registered')
                return render(request,'register.html')
            elif User.objects.filter(email=email).exists():
                messages.info(request,'Email Taken')
                return render(request,'register.html')
            elif len(password) <8:
                messages.info(request,'ATLEAST 8 CHARACTER PASSWORD NEEDED')
                return render(request,'register.html')
            else:
                entry=User(username=username,email=email)
                entry.set_password(password)
                entry.save()
                if referral_code != '':
                    user=Profile.objects.filter(referral_code__exact=referral_code).first()
                    if not user:
                        messages.warning(request,"Invalid Referral Code")
                    else:
                        user.total_referrals+=1
                        user.save()
                messages.success(request,'Done')
                return HttpResponseRedirect(reverse('users:login'))
        else:
            messages.info(request,'Password and confirm password didn"t match')
            return render(request,'register.html')
    return render(request,'register.html')


def login(request):
    if request.method == 'POST':
        username= request.POST.get('username')
        password= request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            auth_login(request, user)
            messages.success(request,'Redirected')
            return HttpResponseRedirect(reverse('main:parity'))
        else:
            messages.error(request,'Wrong Username or Password! ')
            return render(request,'login.html')
    return render(request,'login.html')

#LOGIN,SIGNUP,LOGOUT
@login_required
def my_logout(request):
    logout(request)
    return HttpResponseRedirect('home:main')


@login_required
def profile(request,id):
    user= get_object_or_404(User,id=id)
    if request.method == 'POST':
        avatar= request.FILES.get('avatar')
        phone_number= request.POST.get('phone_number')
        entry = Profile(avatar=avatar,phone_number=phone_number)
        entry.save()
        messages.success(request,'Response Sent!, Team will get back to you within 24 hours.')
        return HttpResponseRedirect(reverse('home:index'))
    return render(request,'profile.html',{'user':user})