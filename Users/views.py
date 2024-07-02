
# Create your views here.
from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
import pyotp
import random

# Create your views here.
User = get_user_model()

def Registration(request):
    return render(request, 'Users/Registration.html')

def UserRegistration(request):
    us=None
    if request.method == 'POST':   
      firstname=request.POST['first-name']
      lastname=request.POST['last-name']
      email=request.POST['your_email']
      phone=request.POST['phone']
      password=request.POST['your_cpassword']
      print(firstname,password)
      suffix = random.randint(1000, 9999)  # Adjust range as needed
       # Check if the username already exists
      username = firstname + str(suffix)
      while User.objects.filter(username=username).exists():
            suffix = random.randint(1000, 9999)  # Generate new suffix
            username = firstname + str(suffix)
      us = User.objects.create_user(
            username=username,
            first_name=firstname,
            last_name=lastname,
            email=email, 
            password=password,
             # Set the role to 'CUSTOMER' by default
        )
      us.role='CUSTOMER'
      us.phone_number=phone 
      us.save()
      if(us):
         return render(request,'Users/Registration.html',{'user':us})
      else:
         return render(request,'Users/Registration.html',{'user':'not success'})
    
