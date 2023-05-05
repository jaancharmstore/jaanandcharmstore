from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
import json
import datetime
from .models import *
from .utils import cookieCart, cartData, guestOrder
from django.contrib.auth.forms import UserCreationForm
from django.core import serializers
from django.core.files.storage import FileSystemStorage


def landingPage(request):
    return render(request, 'store/landingpage.html')


def detailProduct(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    context = {'product': product}
    return render(request, 'store/details.html', context)


def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = User.objects.get(email=email)
        if user.check_password(password):
            request.session['user'] = user.id
            print('login success', user.id)
            return redirect('landing_page')
        else:
            print('error')
            return redirect('login')
    return render(request, 'store/login.html')


def logout(request):
    request.session.clear()
    return redirect('login')


def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        if User.objects.filter(username=username).exists():
            print('username taken')
            return redirect('register')
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            cus = Customer.objects.create(user=user, name=username, email=email)

            user.save()
            cus.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'store/register.html', {'form': form})


def about(request):
    return render(request, 'store/about.html')


def shop(request):
    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    products = Product.objects.all()
    context = {'products': products, 'cartItems': cartItems}
    return render(request, 'store/shop.html', context)


def store(request , category=None):
    data = cartData(request)

    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    if category is not None:
        # filter products by category
        products = Product.objects.filter(category=category)
    else:
        # no category specified, show all products
        if request.method == 'POST':
            search = request.POST['search']
            products = Product.objects.filter(name__icontains=search)
        else:
            products = Product.objects.all()
    context = {'products': products, 'cartItems': cartItems}
    return render(request, 'store/shop.html', context)

def refund(request):
    if request.GET:
        order_id = request.GET['order_id']
        order = Order.objects.get(id=order_id)
        order.complete = False
        order.save()
        return redirect('history')

def history(request):
    if request.session.has_key('user'):
        user = request.session['user']
        user = User.objects.get(id=user)
        cus = Customer.objects.get(user=user)
        shipping = ShippingAddress.objects.filter(customer=cus)
        order = Order.objects.filter(customer=cus, complete=True)

        context = {'items': shipping, 'orders': order}
        print(order)
        return render(request, 'store/history.html', context)
    else:
        return redirect('login')

def check_login(request):
    if request.session.has_key('user'):
        user = request.session['user']
        return JsonResponse({'success': 'true', 'user': user})
    else:
        return JsonResponse({'success': 'false'})
    
def add_to_cart(request):
    if request.session.has_key('user'):
        user = request.session['user']
        product_id = request.GET['product_id']
        qty = request.GET['qty']
        product = Product.objects.get(id=product_id)
        user = User.objects.get(id=user)
        cart = Cart.objects.create(user=user, product=product, quantity=qty)
        cart.save()
        return JsonResponse({'success': 'true'})
    else:
        return JsonResponse({'success': 'false'})

def get_cart(request):
    if request.session.has_key('user'):
        user = request.session['user']
        user = User.objects.get(id=user)
        data = Cart.objects.filter(user=user)
        total = 0
        item_len = len(data)
        data_product = []
        for i in data:
            total += i.product.price * i.quantity
            data_product.append(i.product)

        data_product = json.loads(serializers.serialize('json', data_product))
        data = json.loads(serializers.serialize('json', data))
        return JsonResponse({'items': data, 'total': total, 'item_len': item_len, 'data_product': data_product})
    else:
        return JsonResponse({'items': "", 'total': "", 'item_len': ""})


def remove_cart(request):
    if request.session.has_key('user'):
        user = request.session['user']
        user = User.objects.get(id=user)
        Cart_id = request.GET['cart_id']
        cart = Cart.objects.get(user=user, pk=Cart_id)
        cart.delete()
        return JsonResponse({'success': 'true'})
    else:
        return JsonResponse({'success': 'false'})


def cart(request):
    data = cartData(request)

    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    context = {'items': items, 'order': order, 'cartItems': cartItems}
    return render(request, 'store/cart.html', context)


def checkout(request):
    if request.session.has_key('user'):
        user = request.session['user']
        data = Cart.objects.filter(user=user)
        total = 0
        item_len = len(data)
        for i in data:
            total += i.product.price * i.quantity
        context = {'items': data, 'total': total, 'item_len': item_len}
        return render(request, 'store/checkout.html', context)
    else:
        return redirect('login')


def updateItem(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']
    print('Action:', action)
    print('Product:', productId)

    customer = request.user.customer
    product = Product.objects.get(id=productId)
    order, created = Order.objects.get_or_create(
        customer=customer, complete=False)

    orderItem, created = OrderItem.objects.get_or_create(
        order=order, product=product)

    if action == 'add':
        orderItem.quantity = (orderItem.quantity + 1)
    elif action == 'remove':
        orderItem.quantity = (orderItem.quantity - 1)

    orderItem.save()

    if orderItem.quantity <= 0:
        orderItem.delete()

    return JsonResponse('Item was added', safe=False)


def processOrder(request):
    if request.method == 'POST':
        print(request.FILES)
        transaction_id = datetime.datetime.now().timestamp()
        total = request.POST['total']
        user = request.session['user']
        cus = Customer.objects.get(user=user)
        order, created = Order.objects.get_or_create(customer=cus, complete=False)

        order.transaction_id = transaction_id

        address = request.POST['address']
        city = request.POST['city']
        state = request.POST['state']
        zipcode = request.POST['zipcode']
        name = request.POST['name']
        email = request.POST['email']


        order.complete = True
        order.save()

        file_slip = request.FILES['myfile']
        fs = FileSystemStorage()
        filename = fs.save(file_slip.name, file_slip)
        uploaded_file_url = fs.url(filename)
        

        uuser = User.objects.get(id=request.session['user'])
        payment = Payment.objects.create(
            user=uuser,
            file_slip=file_slip.name,
            amount=total,
            date_added=datetime.datetime.now()
        )
        payment.save()

            


        ship = ShippingAddress.objects.create(
                customer=cus,
                order=order,
                address=address,
                city=city,
                state=state,
                zipcode=zipcode,
                name=name,
                email=email
            )
        ship.save()
            
        Cart.objects.filter(user=request.session['user']).delete()

        return redirect('store')
