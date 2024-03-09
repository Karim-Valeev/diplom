from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, DetailView, FormView, TemplateView, View
)

from app.forms import LoginForm, RegistrationForm, VideoForm
from app.logic import (
    get_recognition_stats_response, get_recognized_video_response
)
from app.mixins import OwnershipRequiredMixin
from app.models import Video
from app.tasks import recognize_actions


class MainPageView(TemplateView):
    template_name = 'main.html'


class LoginView(FormView):
    form_class = LoginForm
    template_name = 'login.html'

    def form_valid(self, form):
        """Security check complete. Log the user in."""
        request = self.request
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        user = authenticate(request, email=email, password=password)
        if user is None:
            form.add_error('email', 'Неправильный логин или пароль')
        else:
            login(request, user)
            return redirect('profile')
        return render(request, 'login.html', {'form': form})


class LogoutView(LoginRequiredMixin, DjangoLogoutView):
    next_page = reverse_lazy('main')


class UserCreateView(CreateView):
    form_class = RegistrationForm
    template_name = 'registration.html'
    success_url = reverse_lazy('login')


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'profile.html'


class VideoCreateView(CreateView):
    form_class = VideoForm
    template_name = 'uploadVideo.html'

    def form_valid(self, form):
        video = form.save(commit=False)
        video.user = self.request.user
        video.save()
        return redirect('profile')


class VideoDetailView(LoginRequiredMixin, OwnershipRequiredMixin, DetailView):
    pk_url_kwarg = 'video_id'
    model = Video
    context_object_name = 'video'
    template_name = 'video.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # TODO: Достать статус нужной celery задачи

        context['recognition_task_status'] = ''

    # TODO: Как-то сюда еще статус задачи по распознаванию...


class VideoDeleteView(LoginRequiredMixin, OwnershipRequiredMixin, DeleteView):
    pk_url_kwarg = 'video_id'
    model = Video
    success_url = reverse_lazy('profile')


class RecognizeActionsView(LoginRequiredMixin, CreateView):

    def post(self, request, *args, **kwargs):
        video_id = self.kwargs['video_id']
        # По сути еще здесь стоит создать связанный с видосом
        # обьект распознавания и дать ему статус таски
        # task = recognize_actions.delay(video_id)
        recognize_actions.delay(video_id)

        return redirect('video', video_id=video_id)


# TODO: Надо как-то это ускорить,
#  с дефолтным веб серваком очень медленно идет загрузка с сервера
class DownloadRecognizedVideoView(View):

    def get(self, request, *args, **kwargs):
        rec_id = self.kwargs['rec_id']
        response = get_recognized_video_response(rec_id)
        return response


class DownloadRecognitionStatisticsView(View):

    def get(self, request, *args, **kwargs):
        rec_id = self.kwargs['rec_id']
        response = get_recognition_stats_response(rec_id)
        return response
