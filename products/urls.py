path("detect/", views.detect_coffee),
path("ai-chat/", views.ai_chat, name="ai_chat"),
path('profile/', views.profile_view, name='dashboard'), # Để trùng với name='dashboard' trong code cũ của bạn
path('admin-panel/toggle-user/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'),