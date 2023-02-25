from django.shortcuts import render,redirect
from .forms import CreateUserForm
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from dataIngestion.models import upload_Dataset

def Register(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    else:
        form=CreateUserForm()
        if request.method=="POST":
            form=CreateUserForm(request.POST)
            if form.is_valid():
                form.save()
                user=form.cleaned_data.get('username')
                messages.success(request,"Account Successfully created:" + user)
                return redirect('login-page')

        context={"form":form}
        return render(request,'accounts/register.html',context)


def Login(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    else:
        if request.method=="POST":
            username=request.POST.get('username')
            password=request.POST.get('password')
            user= authenticate(request, username=username,password=password)
            
            if user is not None:
                login(request,user)
                return redirect('home')

            else:
                messages.info(request,"Username or Password is incorrect")

        return render(request, 'accounts/login.html')

def Logout(request):
    logout(request)
    return redirect('login-page')

@login_required(login_url='login-page')
def Home(request):
    uID= request.user.id
    context={'user_id':uID}
    return render(request,'accounts/home.html',context)

@login_required(login_url='login-page')
def change_password(request):
    context = {
        'form': PasswordChangeForm(request.user, request.POST)
    }
    form = PasswordChangeForm(request.user, request.POST)
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            password = request.POST.get('password')
            user.set_password(password)
            form.save()
            context['save_message'] = 'Password has been changed successfully. !!!'
            return render(request, 'accounts/changePassword.html', context)
        else:
            return render(request, 'accounts/changePassword.html', {'form': form})
    return render(request, 'accounts/changePassword.html', {'form': form})
