from django.urls import path

from app.views import (
    LoginView, LogoutView, MainPageView, ProfileView, UserCreateView,
    VideoCreateView, VideoDeleteView, VideoDetailView
)

urlpatterns = [
    path('', MainPageView.as_view(), name='main'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('registration/', UserCreateView.as_view(), name='registration'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('upload-video/', VideoCreateView.as_view(), name='upload_video'),
    path('profile/videos/<int:video_id>',
         VideoDetailView.as_view(), name='video'),
    path('profile/videos/<int:video_id>/delete/',
         VideoDeleteView.as_view(), name='delete_video'),

    # TODO: Implement
    path('recognize-actions/<int:video_id>',
         MainPageView.as_view(), name='recognize_actions'),
]
