import json
import requests
import urllib3
import base64
import io
from PIL import Image

from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.db.models import Sum

# Import các model của bạn
from .models import Product, Category, Order, OrderItem

# Tắt cảnh báo SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# --- HELPER FUNCTIONS ---
def encode_image_optimized(image_path):
    with Image.open(image_path) as img:
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.thumbnail((800, 800))
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=80)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

# --- USER VIEWS ---
@login_required
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        email = request.POST.get('email')
        full_name = request.POST.get('name', '').strip()
        user.email = email
        name_parts = full_name.split()
        if len(name_parts) > 0:
            user.first_name = name_parts[0]
            user.last_name = " ".join(name_parts[1:])
        user.save()
        messages.success(request, "Thông tin cá nhân đã được cập nhật thành công! ☕")
        return redirect('dashboard')
    return render(request, 'profile.html')

def dashboard(request): 
    return render(request, 'profile.html')

def home(request):
    query = request.GET.get('search')
    products = Product.objects.filter(name__icontains=query) if query else Product.objects.all()
    return render(request, "index.html", {"products": products})

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tài khoản đã được tạo! Đăng nhập ngay thôi nào.')
            return redirect('login')
    else: 
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

# --- SHOPPING CART ---
@login_required
def add_to_cart(request, product_id):
    cart = request.session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    request.session['cart'] = cart
    return redirect('home')

def cart_detail(request):
    cart = request.session.get('cart', {})
    items = []
    total = 0
    for p_id, qty in cart.items():
        try:
            p = Product.objects.get(id=p_id)
            sub = p.price * qty
            total += sub
            items.append({"product": p, "quantity": qty, "subtotal": sub})
        except Product.DoesNotExist:
            continue
    return render(request, "cart.html", {"cart_items": items, "total_price": total})

def update_cart(request, product_id, action):
    cart = request.session.get('cart', {})
    p_id = str(product_id)
    if p_id in cart:
        if action == "plus": cart[p_id] += 1
        elif action == "minus":
            cart[p_id] -= 1
            if cart[p_id] <= 0: del cart[p_id]
        elif action == "remove": del cart[p_id]
    request.session['cart'] = cart
    request.session.modified = True
    return redirect("cart_detail")

@login_required
def checkout(request):
    cart = request.session.get('cart', {})
    if not cart: return redirect('home')
    total_price = 0
    temp_items = []
    for p_id, qty in cart.items():
        product = get_object_or_404(Product, id=p_id)
        total_price += product.price * qty
        temp_items.append((product, qty))
    order = Order.objects.create(user=request.user, total_price=total_price)
    for product, qty in temp_items:
        OrderItem.objects.create(order=order, product=product, quantity=qty, price=product.price)
    request.session['cart'] = {}
    messages.success(request, f"Đặt hàng thành công! Mã đơn: #{order.id} ☕")
    return redirect('home')

# --- ADMIN PANEL ---

@staff_member_required 
def admin_panel(request):
    total_users = User.objects.count()
    total_products = Product.objects.count()
    total_revenue = Order.objects.aggregate(Sum('total_price'))['total_price__sum'] or 0
    all_users = User.objects.all().order_by('-date_joined')
    all_orders = Order.objects.all().order_by('-created_at')
    all_products = Product.objects.all()
    all_categories = Category.objects.all()
    return render(request, 'admin_panel.html', locals())

# ĐÂY LÀ HÀM BỊ THIẾU GÂY RA LỖI:
@staff_member_required
def toggle_user_status(request, user_id):
    if not request.user.is_superuser:
        messages.error(request, "Chỉ Superuser mới có quyền đổi vai trò!")
        return redirect('admin_panel')
    
    target_user = get_object_or_404(User, id=user_id)
    if target_user != request.user:
        target_user.is_staff = not target_user.is_staff
        target_user.save()
        messages.success(request, f"Đã cập nhật vai trò cho {target_user.username}.")
    return redirect('admin_panel')

# --- AI CHAT ---
@csrf_exempt
def ai_chat(request):
    if request.method == "POST":
        try:
            user_message = request.POST.get("message", "").strip()
            user_image = request.FILES.get("image") 
            user_name = request.user.username.upper() if request.user.is_authenticated else "BẠN"

            products = Product.objects.all()
            product_list = [f"- {p.name} | Giá: {p.price} VNĐ | Ảnh: {request.build_absolute_uri(p.image.url) if p.image else ''}" for p in products]
            menu_str = "\n".join(product_list)

            system_prompt = (
    f"Bạn là một Barista chuyên nghiệp, tinh tế và giàu cảm xúc tại 'Coffee House'. "
    f"Bạn không chỉ bán đồ uống, mà còn mang đến trải nghiệm thư giãn và cảm xúc cho khách hàng.\n\n"

    f"Bạn đang phục vụ khách tên {user_name}.\n\n"

    f"📋 DANH SÁCH MENU:\n{menu_str}\n\n"

    "☕ PHONG CÁCH GIAO TIẾP:\n"
    "- Thân thiện, tự nhiên như người thật, không robot.\n"
    "- Trò chuyện như một người hiểu cà phê, có gu và tinh tế.\n"
    "- Có thể mô tả hương vị (đắng nhẹ, hậu ngọt, thơm caramel, chua thanh...).\n"
    "- Gợi ý dựa trên cảm xúc khách: mệt → cà phê mạnh, thư giãn → trà, ngọt ngào → đá xay.\n"
    "- Thỉnh thoảng thêm 1 câu cảm xúc nhẹ: 'món này rất hợp để chill buổi tối'...\n\n"

    "🔥 NGUYÊN TẮC QUAN TRỌNG:\n"

    "1. TỪ CHỐI KHÉO LÉO:\n"
    "Nếu khách hỏi món không có, trả lời tự nhiên:\n"
    "'Dạ, bên mình chưa có [món đó] ạ. Nhưng nếu bạn đang tìm cảm giác tương tự, mình có thể gợi ý một vài món rất hợp gu cho bạn ☕'\n\n"

    "2. GỬI ẢNH SẢN PHẨM:\n"
    "- Khi khách hỏi xem hình, giá hoặc bạn đang tư vấn món → bắt buộc gửi dạng:\n"
    "'Dạ đây là món mình gợi ý cho bạn:'\n"
    "[PRODUCT: tên món | giá | link ảnh]\n\n"

    "3. KHÔNG ĐƯỢC nói không gửi được ảnh. Luôn dùng [PRODUCT:...]\n\n"

    "4. TƯ VẤN THÔNG MINH:\n"
    "- Nếu khách nói chung chung như 'uống gì ngon', phải hỏi lại hoặc gợi ý theo tình huống.\n"
    "- Ví dụ: sáng → cà phê, tối → nhẹ nhàng, nóng → trà mát...\n\n"

    "5. UPSELL TỰ NHIÊN:\n"
    "- Có thể gợi ý thêm topping, size lớn hoặc món đi kèm.\n"
    "- Nhưng phải tự nhiên, không ép mua.\n\n"

    "6. CHUYÊN GIA CÀ PHÊ:\n"
    "- Có thể so sánh các loại cà phê.\n"
    "- Gợi ý combo (ví dụ: bánh + cafe).\n"
    "- Hiểu rõ khẩu vị (đắng, chua, ngọt, béo).\n\n"

    "7. NGẮN GỌN NHƯNG CHẤT:\n"
    "- Tránh lan man.\n"
    "- Mỗi câu trả lời nên rõ ràng, dễ đọc, có cảm xúc.\n"
)

            messages_list = [{"role": "system", "content": system_prompt}]

            if user_image:
                fs = FileSystemStorage()
                filename = fs.save(user_image.name, user_image)
                base64_str = encode_image_optimized(fs.path(filename))
                messages_list.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_message or "Đây là gì?"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_str}"}}
                    ]
                })
                model_name = "llama-3.2-90b-vision-preview"
                fs.delete(filename)
            else:
                messages_list.append({"role": "user", "content": user_message})
                model_name = "llama-3.3-70b-versatile"

            response = requests.post(
                GROQ_URL, 
                headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                json={"model": model_name, "messages": messages_list, "temperature": 0.6},
                timeout=30, verify=False
            )
            
            if response.status_code == 200:
                reply = response.json()['choices'][0]['message']['content']
                return JsonResponse({"reply": reply})
            
            return JsonResponse({"reply": "☕ Có lỗi kết nối AI, thử lại sau nhé!"})
        except Exception as e:
            return JsonResponse({"reply": f"Lỗi hệ thống: {str(e)}"})
    return JsonResponse({"error": "Invalid request"}, status=400)

# --- XỬ LÝ THANH TOÁN VÀ CẬP NHẬT ADMIN ---

@login_required
def confirm_order(request):
    """
    Hàm xử lý khi khách nhấn 'XÁC NHẬN ĐÃ CHUYỂN KHOẢN'
    """
    cart = request.session.get('cart', {})
    
    if not cart:
        messages.warning(request, "Giỏ hàng của bạn đang trống.")
        return redirect('home')

    total_price = 0
    temp_items = []

    # 1. Tính toán tổng tiền và kiểm tra sản phẩm
    for p_id, qty in cart.items():
        product = get_object_or_404(Product, id=p_id)
        total_price += product.price * qty
        temp_items.append((product, qty))

    # 2. Tạo đơn hàng trong database (Sẽ hiện lên trang Quản trị)
    # Trạng thái mặc định thường là 'Pending' hoặc 'Chờ xác nhận' tùy vào Model của bạn
    order = Order.objects.create(
        user=request.user, 
        total_price=total_price
    )

    # 3. Tạo chi tiết từng món trong đơn hàng
    for product, qty in temp_items:
        OrderItem.objects.create(
            order=order, 
            product=product, 
            quantity=qty, 
            price=product.price
        )

    # 4. Xóa giỏ hàng trong session sau khi đã đặt hàng thành công
    request.session['cart'] = {}
    request.session.modified = True

    # 5. Gửi thông báo thành công
    messages.success(request, f"Đặt hàng thành công! Đơn hàng #{order.id} đã được gửi tới quản trị viên. ☕")
    
    return redirect('home')