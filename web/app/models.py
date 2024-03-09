from os.path import splitext

from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    The user model for the project.
    """
    email = models.EmailField(_('электронная почта'), unique=True, blank=False)

    # Because of how django.contrib.auth.backends.ModelBackend works.
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        ordering = ('username',)
        verbose_name = _('пользователь')
        verbose_name_plural = _('пользователи')

    def __str__(self):
        return self.email


def upload_video_to(instance, filename):
    root, ext = splitext(filename)
    return f'users/{instance.user_id}/{root}{ext.lower()}'


class Video(models.Model):
    """
    A model of user video.
    """

    title = models.CharField(_('название'), max_length=256, blank=False)
    file = models.FileField(
        _('файл'),
        upload_to=upload_video_to,
        null=False, blank=False,
        validators=[FileExtensionValidator(allowed_extensions=['mp4'])],
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=False,
        verbose_name=_('пользователь'),
        related_name='videos',
    )
    uploaded = models.DateTimeField(
        _('загружено'), auto_now_add=True, db_index=True
    )
    updated = models.DateTimeField(
        _('обновлёно'), auto_now=True, db_index=True
    )

    class Meta:
        ordering = ('id',)
        verbose_name = _('видео')
        verbose_name_plural = _('видео')


def upload_recognized_video_to(instance, filename):
    return f'users/{instance.video.user_id}/recognized_{filename}'


class Recognition(models.Model):
    """
    A model of user video recognition data.
    """

    video = models.ForeignKey(
        Video,
        on_delete=models.CASCADE,
        null=False, blank=False,
        verbose_name=_('видео'),
        related_name='recognitions',
    )
    recognized_file = models.FileField(
        _('распознанный файл'),
        upload_to=upload_recognized_video_to,
        null=True, blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['mp4'])],
    )
    task_id = models.CharField(_('celery задача'), max_length=36, blank=True)
    # TODO: statistics ???

    created = models.DateTimeField(
        _('создано'), auto_now_add=True, db_index=True)
    updated = models.DateTimeField(_('обновлёно'), auto_now=True, db_index=True)

    class Meta:
        ordering = ('id',)
        verbose_name = _('распознавание')
        verbose_name_plural = _('распознавания')
