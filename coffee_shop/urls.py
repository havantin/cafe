from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from django.conf import settings
from django.conf.urls.static import static
from products.models import Product
from products import views

# Hàm home được định nghĩa trực tiếp để xử lý tìm kiếm
def home(request):
    query = request.GET.get('search')
    if query:
        items = Product.objects.filter(name__icontains=query)
    else:
        items = Product.objects.all()
    return render(request, 'index.html', {'products': items})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('confirm-order/', views.confirm_order, name='confirm_order'),
    
    # Sửa từ admin_panel thành admin_dashboard để khớp với views.py
    # Trong file coffee_shop/urls.py
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('admin-panel/toggle-user/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'),
    path('checkout/', views.checkout, name='checkout'),

    # Trang chủ
    path('', home, name='home'),

    # AI chat (Groq Llama 3)
    path("ai-chat/", views.ai_chat, name="ai_chat"),

    # AI detect - Nếu bạn không dùng chức năng detect cũ, 
    # hãy trỏ tạm nó về ai_chat để tránh lỗi AttributeError
    path("detect/", views.ai_chat, name="detect"),

    # Tài khoản
    path('accounts/', include('django.contrib.auth.urls')),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Giỏ hàng
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('update-cart/<int:product_id>/<str:action>/', views.update_cart, name='update_cart'),
]

# Cấu hình để hiển thị hình ảnh từ thư mục media
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)