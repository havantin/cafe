from django.db import models
from django.contrib.auth.models import User

# Bảng 1: Danh mục sản phẩm
class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Tên danh mục")

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

# Bảng 2: Sản phẩm cà phê
class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Danh mục")
    name = models.CharField(max_length=200, verbose_name="Tên sản phẩm")
    description = models.TextField(verbose_name="Mô tả", blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Giá tiền")
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# --- PHẦN THÊM MỚI ĐỂ QUẢN LÝ ĐƠN HÀNG ---

# Bảng 3: Đơn hàng (Lưu thông tin chung)
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Khách hàng")
    total_price = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Tổng tiền")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày đặt")
    status = models.CharField(max_length=50, default="Hoàn thành", verbose_name="Trạng thái")

    def __str__(self):
        return f"Đơn hàng #{self.id} - {self.user.username}"

# Bảng 4: Chi tiết đơn hàng (Lưu từng món trong đơn hàng đó)
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Sản phẩm")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Số lượng")
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Giá lúc mua")

    def __str__(self):
        return f"{self.product.name} (x{self.quantity})"