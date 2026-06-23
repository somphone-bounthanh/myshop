from django import forms
from django.contrib.auth.models import User
from . import models
from .models import Feedback


class CustomerUserForm(forms.ModelForm):
    class Meta:
        model=User
        fields=['first_name','last_name','username','password']
        widgets = {
        'password': forms.PasswordInput()
        }
        
class CustomerForm(forms.ModelForm):
    class Meta:
        model=models.Customer
        fields=['address','mobile','profile_pic']

class ProductForm(forms.ModelForm):
    class Meta:
        model=models.Product
        fields=['name','price','description','product_image']

#address of shipment
class AddressForm(forms.Form):
    Email = forms.EmailField()
    Mobile= forms.IntegerField()
    Address = forms.CharField(max_length=500)

class FeedbackForm(forms.ModelForm):
    class Meta:
        model=models.Feedback
        fields=['name','feedback']

#for updating status of order
class OrderForm(forms.ModelForm):
    class Meta:
        model=models.Orders
        fields=['status']

#for contact us page
class ContactusForm(forms.ModelForm): # ຕ້ອງເປັນ ModelForm ເທົ່ານັ້ນ ຈຶ່ງຈະມີຄຳສັ່ງ .save()
    class Meta:
        model = Feedback
        fields = ['name', 'feedback']
        labels = {
            'name': 'ຊື່ຂອງທ່ານ',
            'feedback': 'ຄຳຕິຊົມ/ຂໍ້ຄວາມ',
        }
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'ກະລຸນາໃສ່ຊື່ຂອງທ່ານ', 'class': 'form-control'}),
            'feedback': forms.Textarea(attrs={'placeholder': 'ຂຽນຄຳຕິຊົມຂອງທ່ານຢູ່ນີ້...', 'class': 'form-control', 'rows': 4}),
        }