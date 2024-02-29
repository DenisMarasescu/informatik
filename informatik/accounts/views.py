from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from .forms import BaseRegisterForm, CustomAuthenticationForm, ProfesorRegisterForm

def register(request):
    if request.user.is_authenticated:
        # Redirect to a different page, like the homepage
        return redirect('my_courses')

    if request.method == 'POST':
        form = ProfesorRegisterForm(request.POST) if 'is_profesor' in request.POST else BaseRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            if 'is_profesor' in request.POST:
                user.is_profesor = True
                user.school = form.cleaned_data.get('school', None)
            user.save()
            # Log the user in, redirect, or return a success response
            return redirect('/accounts/login')  # Adjust as necessary
    else:
        form = BaseRegisterForm()  # Default to student registration form
    return render(request, 'accounts/register.html', {'form': form})


def user_login(request):
    if request.user.is_authenticated:
        # Redirect to a different page, like the homepage
        return redirect('my_courses')

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                # Redirect to a success page.
                return redirect("/my_courses")  # Adjust the redirect as necessary
            else:
                # Return an 'invalid login' error message.
                form.add_error(None, "Invalid username or password.")
    else:
        form = CustomAuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})