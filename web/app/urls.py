from django.urls import path

from app.views import (
    DownloadRecognitionStatisticsView, DownloadRecognizedVideoView, LoginView,
    LogoutView, MainPageView, ProfileView, RecognizeActionsView, UserCreateView,
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
    path('recognize-actions/<int:video_id>',
         RecognizeActionsView.as_view(), name='recognize_actions'),
    path('download-recognized-video/<int:rec_id>',
         DownloadRecognizedVideoView.as_view(), name='download_recognized_video'),
    path('download-recognition-statistics/<int:rec_id>',
         DownloadRecognitionStatisticsView.as_view(), name='download_recognition_statistics'),
]
