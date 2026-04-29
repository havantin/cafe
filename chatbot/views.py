from django.shortcuts import render
from django.http import JsonResponse
import google.generativeai as genai
from django.views.decorators.csrf import csrf_exempt


# Cấu hình Gemini với Key của bạn
genai.configure(api_key="AIzaSyCr6eJRBVofOI5TQv0s2ZxV_MTIM7ojU5o")

@csrf_exempt
def chat_api(request):
    if request.method == "POST":
        user_message = request.POST.get('message', '')
        
        if not user_message:
            return JsonResponse({'error': 'Tin nhắn trống'}, status=400)

        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            # Cấu hình ngữ cảnh cho Bot cafe
            chat = model.start_chat(history=[])
            prompt = f"Bạn là nhân viên hỗ trợ của cửa hàng Coffee Shop. Hãy trả lời ngắn gọn, thân thiện về các loại cafe và dịch vụ. Câu hỏi khách hàng: {user_message}"
            
            response = chat.send_message(prompt)
            return JsonResponse({'reply': response.text})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
            
    return render(request, 'chatbot/chat.html') # Trả về giao diện chat
    