from django.shortcuts import redirect


class OwnershipRequiredMixin:
    """Making sure that only owners have access to their objects."""

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.user != self.request.user:
            return redirect('profile')
        return super().dispatch(request, *args, **kwargs)
