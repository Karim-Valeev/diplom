from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, DetailView, FormView, TemplateView, View
)

from app.forms import LoginForm, RegistrationForm, VideoForm
from app.mixins import OwnershipRequiredMixin
from app.models import Video
from app.tasks import check_celery


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

    def get(self, request, *args, **kwargs):
        check_celery.delay('TEST')
        return super().get(request, *args, **kwargs)


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
    # TODO: Как-то сюда еще статус задачи по распознаванию...


class VideoDeleteView(LoginRequiredMixin, OwnershipRequiredMixin, DeleteView):
    pk_url_kwarg = 'video_id'
    model = Video
    success_url = reverse_lazy('profile')


class RecognizeActionsView(LoginRequiredMixin, CreateView):

    def post(self, request, *args, **kwargs):
        # Логика МЛ...
        # TODO: Надо кинуть на ту же страницу видео
        # return redirect('video', video_id=...)
        return redirect('video')


# noqa # class DownloadView(View):
# noqa #
# noqa #     def get(self, request, *args, **kwargs):
# noqa #         file = UploadFilesBlobStorage.objects.get(Uuid=self.kwargs['fileUUID'])
# noqa #         filename = file.Filename
# noqa #         file_type, _ = mimetypes.guess_type(filename)
# noqa #         url = file.Url
# noqa #         blob_name = url.split("/")[-1]
# noqa #         blob_content = download_from_blob(blob_name)
# noqa #
# noqa #         if blob_content:
# noqa #             response = HttpResponse(blob_content.readall(), content_type=file_type)
# noqa #             response['Content-Disposition'] = f'attachment; filename={filename}'
# noqa #             messages.success(request, f"{filename} was successfully downloaded")
# noqa #             return response
# noqa #
# noqa #         return Http404


class DownloadRecognizedVideoView(View):
    pass


class DownloadRecognitionStatisticsView(View):
    pass
