from django.shortcuts import render,redirect,reverse
from . import forms,models
from django.http import HttpResponseRedirect,HttpResponse
from django.core.mail import send_mail
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required,user_passes_test
from django.contrib import messages
from django.conf import settings
from django.shortcuts import render, redirect
from .models import Product 
from django.shortcuts import get_object_or_404
from webpush import send_group_notification

from webpush import send_group_notification
def home_view(request):
    products=models.Product.objects.all()
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        counter=product_ids.split('|')
        product_count_in_cart=len(set(counter))
    else:
        product_count_in_cart=0
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'ecom/index.html',{'products':products,'product_count_in_cart':product_count_in_cart})




def process_order(request):
    if request.method == "POST":
        # ... ບັນທຶກອໍເດີ ...

        payload = {
            "title": "🥤 ມີອໍເດີໃໝ່ເຂົ້າມາ!",
            "body": f"ອໍເດີຈາກ: {request.user.username} ລາຄາ {total_price} ກີບ",
            "url": "/admin-view-booking/" # Link ໄປໜ້າຈັດການ
        }
        
        # ສົ່ງແຈ້ງເຕືອນ
        send_group_notification(group_name="admins", payload=payload, ttl=1000)

        return render(request, 'payment_success.html')


#for showing login button for admin(by sumit)
def adminclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return HttpResponseRedirect('adminlogin')


def customer_signup_view(request):
    userForm=forms.CustomerUserForm()
    customerForm=forms.CustomerForm()
    mydict={'userForm':userForm,'customerForm':customerForm}
    if request.method=='POST':
        userForm=forms.CustomerUserForm(request.POST)
        customerForm=forms.CustomerForm(request.POST,request.FILES)
        if userForm.is_valid() and customerForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            customer=customerForm.save(commit=False)
            customer.user=user
            customer.save()
            my_customer_group = Group.objects.get_or_create(name='CUSTOMER')
            my_customer_group[0].user_set.add(user)
        return HttpResponseRedirect('customerlogin')
    return render(request,'ecom/customersignup.html',context=mydict)

#-----------for checking user iscustomer
def is_customer(user):
    return user.groups.filter(name='CUSTOMER').exists()



#---------AFTER ENTERING CREDENTIALS WE CHECK WHETHER USERNAME AND PASSWORD IS OF ADMIN,CUSTOMER
def afterlogin_view(request):
    if is_customer(request.user):
        return redirect('customer-home')
    else:
        return redirect('admin-dashboard')

#---------------------------------------------------------------------------------
#------------------------ ADMIN RELATED VIEWS START ------------------------------
#---------------------------------------------------------------------------------
@login_required(login_url='adminlogin')
def admin_dashboard_view(request):
    # ສໍາລັບ Cards ສະຖິຕິ
    customercount = models.Customer.objects.all().count()
    productcount = models.Product.objects.all().count()
    ordercount = models.Orders.objects.all().count()

    # ສໍາລັບກາບວົງມົນ (Status Chart) - ດຶງຂໍ້ມູນຈິງມາແຍກສະຖານະ
    delivered_count = models.Orders.objects.filter(status='Delivered').count()
    pending_count = models.Orders.objects.filter(status='Pending').count()
    other_count = ordercount - (delivered_count + pending_count)

    # ສໍາລັບກາບເສັ້ນ (Sales Chart) - ຕົວເລກສົມມຸດ 7 ວັນ (ສາມາດຂຽນ Query ເພີ່ມໄດ້)
    sales_data = [10, 25, 15, 30, 45, 35, 55] 

    # ສໍາລັບຕາຕະລາງ Recent Orders (ດຶງພຽງ 10 ລາຍການຫຼ້າສຸດເພື່ອໃຫ້ໂຫຼດໄວ)
    orders = models.Orders.objects.all().order_by('-id')[:10]
    ordered_products = []
    ordered_bys = []
    for order in orders:
        ordered_product = models.Product.objects.filter(id=order.product.id)
        ordered_by = models.Customer.objects.filter(id=order.customer.id)
        ordered_products.append(ordered_product)
        ordered_bys.append(ordered_by)

    mydict = {
        'customercount': customercount,
        'productcount': productcount,
        'ordercount': ordercount,
        'data': zip(ordered_products, ordered_bys, orders),
        'delivered_count': delivered_count,
        'pending_count': pending_count,
        'other_count': other_count,
        'sales_data': sales_data,
    }
    return render(request, 'ecom/admin_dashboard.html', context=mydict)



# admin view customer table
@login_required(login_url='adminlogin')
def view_customer_view(request):
    customers=models.Customer.objects.all()
    return render(request,'ecom/view_customer.html',{'customers':customers})

# admin delete customer
@login_required(login_url='adminlogin')
def delete_customer_view(request,pk):
    customer=models.Customer.objects.get(id=pk)
    user=models.User.objects.get(id=customer.user_id)
    user.delete()
    customer.delete()
    return redirect('view-customer')


@login_required(login_url='adminlogin')
def update_customer_view(request,pk):
    customer=models.Customer.objects.get(id=pk)
    user=models.User.objects.get(id=customer.user_id)
    userForm=forms.CustomerUserForm(instance=user)
    customerForm=forms.CustomerForm(request.FILES,instance=customer)
    mydict={'userForm':userForm,'customerForm':customerForm}
    if request.method=='POST':
        userForm=forms.CustomerUserForm(request.POST,instance=user)
        customerForm=forms.CustomerForm(request.POST,instance=customer)
        if userForm.is_valid() and customerForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            customerForm.save()
            return redirect('view-customer')
    return render(request,'ecom/admin_update_customer.html',context=mydict)

# admin view the product
@login_required(login_url='adminlogin')
def admin_products_view(request):
    products=models.Product.objects.all()
    return render(request,'ecom/admin_products.html',{'products':products})


# admin add product by clicking on floating button
@login_required(login_url='adminlogin')
def admin_add_product_view(request):
    productForm=forms.ProductForm()
    if request.method=='POST':
        productForm=forms.ProductForm(request.POST, request.FILES)
        if productForm.is_valid():
            productForm.save()
        return HttpResponseRedirect('admin-products')
    return render(request,'ecom/admin_add_products.html',{'productForm':productForm})


@login_required(login_url='adminlogin')
def delete_product_view(request,pk):
    product=models.Product.objects.get(id=pk)
    product.delete()
    return redirect('admin-products')


@login_required(login_url='adminlogin')
def update_product_view(request,pk):
    product=models.Product.objects.get(id=pk)
    productForm=forms.ProductForm(instance=product)
    if request.method=='POST':
        productForm=forms.ProductForm(request.POST,request.FILES,instance=product)
        if productForm.is_valid():
            productForm.save()
            return redirect('admin-products')
    return render(request,'ecom/admin_update_product.html',{'productForm':productForm})


@login_required(login_url='adminlogin')
def admin_view_booking_view(request):
    orders=models.Orders.objects.all()
    ordered_products=[]
    ordered_bys=[]
    for order in orders:
        ordered_product=models.Product.objects.all().filter(id=order.product.id)
        ordered_by=models.Customer.objects.all().filter(id = order.customer.id)
        ordered_products.append(ordered_product)
        ordered_bys.append(ordered_by)
    return render(request,'ecom/admin_view_booking.html',{'data':zip(ordered_products,ordered_bys,orders)})


@login_required(login_url='adminlogin')
def delete_order_view(request,pk):
    order=models.Orders.objects.get(id=pk)
    order.delete()
    return redirect('admin-view-booking')

# for changing status of order (pending,delivered...)
@login_required(login_url='adminlogin')
def update_order_view(request,pk):
    order=models.Orders.objects.get(id=pk)
    orderForm=forms.OrderForm(instance=order)
    if request.method=='POST':
        orderForm=forms.OrderForm(request.POST,instance=order)
        if orderForm.is_valid():
            orderForm.save()
            return redirect('admin-view-booking')
    return render(request,'ecom/update_order.html',{'orderForm':orderForm})


# admin view the feedback
@login_required(login_url='adminlogin')
def view_feedback_view(request):
    feedbacks=models.Feedback.objects.all().order_by('-id')
    return render(request,'ecom/view_feedback.html',{'feedbacks':feedbacks})



#---------------------------------------------------------------------------------
#------------------------ PUBLIC CUSTOMER RELATED VIEWS START ---------------------
#---------------------------------------------------------------------------------


def search_view(request):
    # whatever user write in search box we get in query
    query = request.GET['query']
    products=models.Product.objects.all().filter(name__icontains=query)
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        counter=product_ids.split('|')
        product_count_in_cart=len(set(counter))
    else:
        product_count_in_cart=0

    # word variable will be shown in html when user click on search button
    word="ຜົນການຄົ້ນຫາສີນຄ້າ :"

    if request.user.is_authenticated:
        return render(request,'ecom/customer_home.html',{'products':products,'word':word,'product_count_in_cart':product_count_in_cart})
    return render(request,'ecom/index.html',{'products':products,'word':word,'product_count_in_cart':product_count_in_cart})




# 💡 1. ຟັງຊັນເພີ່ມຈຳນວນ (+)
def add_qty(request, pk):
    cart = request.session.get('cart', {})
    product_id = str(pk)
    
    if product_id in cart:
        cart[product_id] += 1
    
    request.session['cart'] = cart
    # 💡 ຕ້ອງມີບັນທັດນີ້ເພື່ອບັງຄັບໃຫ້ Save ລົງ Database/Session
    request.session.modified = True 
    
    return redirect(request.META.get('HTTP_REFERER', '/'))

# 💡 2. ຟັງຊັນລົບຈຳນວນ (-)
def remove_qty(request, pk):
    cart = request.session.get('cart', {})
    product_id = str(pk)
    
    if product_id in cart:
        if cart[product_id] > 1:
            cart[product_id] -= 1  # ຫຼຸດລົງ 1
        else:
            del cart[product_id]  # ຖ້າເຫຼືອ 1 ແລ້ວກົດລົບ ໃຫ້ລຶບອອກເລີຍ
            
    request.session['cart'] = cart
    request.session.modified = True
    return redirect(request.META.get('HTTP_REFERER', 'cart'))


# 💡 2. ຟັງຊັນລົບຈຳນວນ (-) ຈຳນວນຫຼາຍໆກວ່າ1ຂື້ນໄປ
def remove_qty_more(request, pk):
      # ດຶງຂໍ້ມູນ cart ຈາກ session
    cart = request.session.get('cart', {})
    product_id = str(pk)
    
    if product_id in cart:
        # ລຶບ product_id ອອກຈາກ dictionary ທັນທີ
        del cart[product_id]
        
        # ບັນທຶກການປ່ຽນແປງລົງໃນ session
        request.session['cart'] = cart
        request.session.modified = True
        
    return redirect(request.META.get('HTTP_REFERER', 'cart'))





# --- ຟັງຊັນຊ່ວຍຈັດການ Cookie ---
def get_response_with_cookie(request, product_id_list):
    response = HttpResponseRedirect(request.META.get('HTTP_REFERER', '/cart/'))
    if not product_id_list:
        response.delete_cookie('product_ids', path='/')
    else:
        new_value = "|".join(product_id_list)
        response.set_cookie('product_ids', new_value, path='/', max_age=3600*24*7)
    return response

# 1. ປຸ່ມບວກ (+) - ເພີ່ມຈຳນວນ
def add_qty_view(request, pk):
    product_ids = request.COOKIES.get('product_ids', "")
    product_id_list = [i for i in product_ids.split('|') if i != ""]
    product_id_list.append(str(pk))
    return get_response_with_cookie(request, product_id_list)

    

# 2. ປຸ່ມລົບ (-) - ລົດຈຳນວນລົງ 1
def remove_from_cart_view(request, pk):
    # 1. ດຶງຂໍ້ມູນ Cookie
    product_ids = request.COOKIES.get('product_ids', "")
    str_pk = str(pk)
    
    if product_ids:
        # 2. 💡 ໃຊ້ List Comprehension ເພື່ອ "ເອົາທຸກຕົວອອກ" ທີ່ເປັນ ID ນີ້
        # (ຖ້າມີ ID '5' ຢູ່ 10 ໂຕ ມັນຈະຖືກລຶບອອກທັງ 10 ໂຕເລີຍ)
        product_id_list = [i for i in product_ids.split('|') if i != str_pk and i != ""]
        
        # 3. ກຽມ Response (ກັບໄປໜ້າເດີມ)
        response = HttpResponseRedirect(request.META.get('HTTP_REFERER', '/cart/'))
        
        # 4. 💡 ສິ່ງສຳຄັນ: ຕ້ອງໃສ່ path='/' ທັງຕອນຕັ້ງ ແລະ ຕອນລຶບ
        if not product_id_list:
            response.delete_cookie('product_ids', path='/')
        else:
            new_value = "|".join(product_id_list)
            response.set_cookie('product_ids', new_value, path='/', max_age=3600*24*7)
            
        return response
    return redirect('cart')



# any one can add product to cart, no need of signin
def add_to_cart_view(request, pk):
    # 1. ດຶງຈຳນວນຈາກ URL (?quantity=5) ຖ້າບໍ່ມີໃຫ້ເປັນ 1
    quantity = int(request.GET.get('quantity', 1))
    
    # 2. ດຶງຂໍ້ມູນກະຕ່າຈາກ Session (Dictionary)
    cart = request.session.get('cart', {})

    # 3. ບວກຈຳນວນໃໝ່ໃສ່ຈຳນວນເກົ່າ
    product_id = str(pk)
    if product_id in cart:
        cart[product_id] += quantity
    else:
        cart[product_id] = quantity

    # 4. ບັນທຶກ ແລະ ນັບຈຳນວນທັງໝົດ
    request.session['cart'] = cart
    request.session.modified = True
    product_count_in_cart = sum(cart.values())

    return redirect(request.META.get('HTTP_REFERER', '/'))

    

def update_cart_qty(request, p_id, delta):
    cart = request.session.get('cart', {})
    p_id_str = str(p_id)
    
    if p_id_str in cart:
        cart[p_id_str] += int(delta)
        if cart[p_id_str] < 1:
            del cart[p_id_str]
            
    request.session['cart'] = cart
    request.session.modified = True

    # --- ຄິດໄລ່ລາຄາໃໝ່ທັງໝົດ ---
    grand_total = 0
    current_subtotal = 0
    for id, qty in cart.items():
        product = Product.objects.get(id=id)
        sub = product.price * qty
        grand_total += sub
        if id == p_id_str:
            current_subtotal = sub

    return JsonResponse({
        'status': 'success',
        'product_qty': cart.get(p_id_str, 0),
        'subtotal': "{:,}".format(current_subtotal),
        'grand_total': "{:,}".format(grand_total),
        'total_items': sum(cart.values())
    })

# for checkout of cart

def cart_view(request):
    cart = request.session.get('cart', {})
    products_list = [] # 💡 ສ້າງ List ໃໝ່ເພື່ອເກັບຂໍ້ມູນຈາກ Session
    total = 0

    for p_id, item_qty in cart.items():
        try:
            product = Product.objects.get(id=p_id)
            subtotal = product.price * item_qty
            total += subtotal
            
            # 💡 ປ້ອນຂໍ້ມູນໃສ່ List ໃໝ່ (ໃຊ້ qty ຈາກ Session)
            products_list.append({
                'id': product.id,
                'name': product.name,
                'price': product.price,
                'qty': item_qty,      # <--- ເລກ 2 ຈະມາຈາກບ່ອນນີ້
                'subtotal': subtotal,
                'product_image': product.product_image
            })
        except Product.DoesNotExist:
            continue

    return render(request, 'ecom/cart.html', {
        'products': products_list, # 💡 ສົ່ງ List ໃໝ່ນີ້ໄປໃຫ້ HTML
        'total': total
        
    })



def remove_from_cart_view(request, pk):
    # 1. ກວດເບິ່ງ Cookies ວ່າສິນຄ້າມີຢູ່ບໍ່
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        product_id_list = product_ids.split('|')
        
        # 2. Logic ການລຶບ: ລຶບ ID ທີ່ກົງກັບ pk ອອກພຽງ 1 ຕົວ (ເພື່ອໃຫ້ເຫຼືອຕົວຊ້ຳໄວ້)
        if str(pk) in product_id_list:
            product_id_list.remove(str(pk))
        
        # 3. ສ້າງສາຍ String ໃໝ່ເພື່ອເກັບລົງ Cookies
        value = "|".join(product_id_list)
        
        # 4. ຄິດໄລ່ສິນຄ້າທີ່ເຫຼືອເພື່ອສະແດງຜົນ
        products = models.Product.objects.filter(id__in=product_id_list)
        
        # ຄິດໄລ່ລາຄາລວມ (Total) ຕາມຈຳນວນທີ່ເຫຼືອແທ້
        total = 0
        for p in products:
            # ນັບວ່າ ID ນີ້ເຫຼືອຈັກອັນໃນ list ແລ້ວຄູນລາຄາ
            count = product_id_list.count(str(p.id))
            total += (p.price * count)
        
        # ນັບຈຳນວນສິນຄ້າທັງໝົດໃນກະຕ່າ (Counter)
        product_count_in_cart = len(product_id_list)
        
        # 5. ສ້າງ Response ແລະ ອັບເດດ Cookies ໃໝ່
        response = render(request, 'ecom/cart.html', {
            'products': products,
            'total': total,
            'product_count_in_cart': product_count_in_cart
        })
        
        if value == "":
            response.delete_cookie('product_ids')
        else:
            response.set_cookie('product_ids', value)
            
        return response
    
    return redirect('cart') # ຖ້າບໍ່ມີ Cookies ໃຫ້ກັບໄປໜ້າ Cart
    
    

def send_feedback_view(request):
    feedbackForm=forms.FeedbackForm()
    if request.method == 'POST':
        feedbackForm = forms.FeedbackForm(request.POST)
        if feedbackForm.is_valid():
            feedbackForm.save()
            return render(request, 'ecom/feedback_sent.html')
    return render(request, 'ecom/send_feedback.html', {'feedbackForm':feedbackForm})


#---------------------------------------------------------------------------------
#------------------------ CUSTOMER RELATED VIEWS START ------------------------------
#---------------------------------------------------------------------------------
@login_required(login_url='customerlogin')
@user_passes_test(is_customer)
def customer_home_view(request):
    products=models.Product.objects.all()
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        counter=product_ids.split('|')
        product_count_in_cart=len(set(counter))
    else:
        product_count_in_cart=0
    return render(request,'ecom/customer_home.html',{'products':products,'product_count_in_cart':product_count_in_cart})



# shipment address before placing order
@login_required(login_url='customerlogin')
def customer_address_view(request):
    # this is for checking whether product is present in cart or not
    # if there is no product in cart we will not show address form
    product_in_cart=False
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        if product_ids != "":
            product_in_cart=True
    #for counter in cart
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        counter=product_ids.split('|')
        product_count_in_cart=len(set(counter))
    else:
        product_count_in_cart=0

    addressForm = forms.AddressForm()
    if request.method == 'POST':
        addressForm = forms.AddressForm(request.POST)
        if addressForm.is_valid():
            # here we are taking address, email, mobile at time of order placement
            # we are not taking it from customer account table because
            # these thing can be changes
            email = addressForm.cleaned_data['Email']
            mobile=addressForm.cleaned_data['Mobile']
            address = addressForm.cleaned_data['Address']
            #for showing total price on payment page.....accessing id from cookies then fetching  price of product from db
            total=0
            if 'product_ids' in request.COOKIES:
                product_ids = request.COOKIES['product_ids']
                if product_ids != "":
                    product_id_in_cart=product_ids.split('|')
                    products=models.Product.objects.all().filter(id__in = product_id_in_cart)
                    for p in products:
                        total=total+p.price

            response = render(request, 'ecom/payment.html',{'total':total})
            response.set_cookie('email',email)
            response.set_cookie('mobile',mobile)
            response.set_cookie('address',address)
            return response
    return render(request,'ecom/customer_address.html',{'addressForm':addressForm,'product_in_cart':product_in_cart,'product_count_in_cart':product_count_in_cart})




# here we are just directing to this view...actually we have to check whther payment is successful or not
#then only this view should be accessed
@login_required(login_url='customerlogin')
def payment_success_view(request):
    customer = models.Customer.objects.get(user_id=request.user.id)
    cart = request.session.get('cart', {}) # ດຶງຂໍ້ມູນ {'product_id': quantity}

    if cart:
        product_ids = cart.keys()
        products = models.Product.objects.filter(id__in=product_ids)

        for product in products:
            # ດຶງຈຳນວນສິນຄ້າຈາກ Session ໂດຍໃຊ້ ID ຂອງ Product
            qty = cart.get(str(product.id), 1)
            
            # ຄິດໄລ່ລາຄາລວມ (ລາຄາສິນຄ້າ x ຈຳນວນ)
            total_amount = product.price * qty

            models.Orders.objects.create(
                customer=customer,
                product=product,
                quantity=qty,        # ບັນທຶກຈຳນວນ
                amount=total_amount, # ບັນທຶກຍອດເງິນ
                status='Pending',
                email=request.COOKIES.get('email', customer.user.email),
                mobile=request.COOKIES.get('mobile', customer.mobile),
                address=request.COOKIES.get('address', customer.address)
            )

        # ລຶບ Cart ຫຼັງຈາກບັນທຶກສຳເລັດ
        request.session['cart'] = {}
        request.session.modified = True
        
    return render(request, 'ecom/payment_success.html')



@login_required(login_url='customerlogin')
@user_passes_test(is_customer)
def my_order_view(request):
    customer=models.Customer.objects.get(user_id=request.user.id)
    orders=models.Orders.objects.all().filter(customer_id = customer)
    ordered_products=[]
    for order in orders:
        ordered_product=models.Product.objects.all().filter(id=order.product.id)
        ordered_products.append(ordered_product)

    return render(request,'ecom/my_order.html',{'data':zip(ordered_products,orders)})




#--------------for discharge patient bill (pdf) download and printing
import io
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.template import Context
from django.http import HttpResponse


def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return

@login_required(login_url='customerlogin')
@user_passes_test(is_customer)
def download_invoice_view(request,orderID,productID):
    order=models.Orders.objects.get(id=orderID)
    product=models.Product.objects.get(id=productID)
    mydict={
        'orderDate':order.order_date,
        'customerName':request.user,
        'customerEmail':order.email,
        'customerMobile':order.mobile,
        'shipmentAddress':order.address,
        'orderStatus':order.status,

        'productName':product.name,
        'productImage':product.product_image,
        'productPrice':product.price,
        'productDescription':product.description,


    }
    return render_to_pdf('ecom/download_invoice.html',mydict)






@login_required(login_url='customerlogin')
@user_passes_test(is_customer)
def my_profile_view(request):
    customer=models.Customer.objects.get(user_id=request.user.id)
    return render(request,'ecom/my_profile.html',{'customer':customer})


@login_required(login_url='customerlogin')
@user_passes_test(is_customer)
def edit_profile_view(request):
    customer=models.Customer.objects.get(user_id=request.user.id)
    user=models.User.objects.get(id=customer.user_id)
    userForm=forms.CustomerUserForm(instance=user)
    customerForm=forms.CustomerForm(request.FILES,instance=customer)
    mydict={'userForm':userForm,'customerForm':customerForm}
    if request.method=='POST':
        userForm=forms.CustomerUserForm(request.POST,instance=user)
        customerForm=forms.CustomerForm(request.POST,instance=customer)
        if userForm.is_valid() and customerForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            customerForm.save()
            return HttpResponseRedirect('my-profile')
    return render(request,'ecom/edit_profile.html',context=mydict)



#---------------------------------------------------------------------------------
#------------------------ ABOUT US AND CONTACT US VIEWS START --------------------
#---------------------------------------------------------------------------------
def aboutus_view(request):
    return render(request,'ecom/aboutus.html')

from django.shortcuts import render, redirect
from . import forms
import urllib.parse

from django.shortcuts import render, redirect
from . import forms, models

def contactus_view(request):
    sub = forms.ContactusForm()
    
    if request.method == 'POST':
        sub = forms.ContactusForm(request.POST)
        
        if sub.is_valid():
            # --- 1. ບັນທຶກລົງ Database (ແກ້ Error 'save') ---
            if hasattr(sub, 'save'):
                # ໃຊ້ວິທີນີ້ຖ້າທ່ານປ່ຽນເປັນ ModelForm ແລ້ວ
                sub.save()
            else:
                # ໃຊ້ວິທີນີ້ຖ້າທ່ານຍັງໃຊ້ forms.Form (ແບບເກົ່າ)
                name = sub.cleaned_data.get('Name')
                message = sub.cleaned_data.get('Message')
                models.Feedback.objects.create(name=name, feedback=message)
            
            # --- 2. ປ່ຽນລິ້ງ: ສົ່ງລູກຄ້າໄປຫາໜ້າສຳເລັດ (Success Page) ---
            # ໃຫ້ແນ່ໃຈວ່າທ່ານມີໄຟລ໌ ecom/contactussuccess.html ຢູ່ໃນ templates
            return render(request, 'ecom/contactussuccess.html')
            
    return render(request, 'ecom/contactus.html', {'form': sub})

