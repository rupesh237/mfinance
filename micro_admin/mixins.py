from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from micro_admin.models import User
from django.contrib.auth.mixins import LoginRequiredMixin


class UserPermissionRequiredMixin(LoginRequiredMixin):

    def dispatch(self, request, *args, **kwargs):
        user = get_object_or_404(User, id=kwargs.get('user_id'))
        if not (
            request.user.is_admin or request.user == user or
            (
                request.user.has_perm("branch_manager") and
                request.user.branch == user.branch
            )
        ):
            raise PermissionDenied
        return super(UserPermissionRequiredMixin, self).dispatch(
            request, *args, **kwargs)


class BranchAccessRequiredMixin(object):

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(self, 'object'):
            self.object = self.get_object()

        # Checking the permissions
        if not(
            request.user.is_admin or
            request.user.branch == self.object.branch
        ):
            raise PermissionDenied

        return super(BranchAccessRequiredMixin, self).dispatch(
            request, *args, **kwargs)


class BranchManagerRequiredMixin(object):

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(self, 'object'):
            self.object = self.get_object()

        # Checking the permissions
        if not(
            request.user.is_admin or
            (
                request.user.has_perm("branch_manager") and
                request.user.branch == self.object.branch
            )
        ):
            raise PermissionDenied

        return super(BranchManagerRequiredMixin, self).dispatch(
            request, *args, **kwargs)


class ContentManagerRequiredMixin(object):

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(self, 'object'):
            self.object = self.get_object()
        # Checking the permissions
        if not(
            request.user.is_admin or
            request.user.has_perm('content_manager')
        ):
            raise PermissionDenied

        return super(ContentManagerRequiredMixin, self).dispatch(
            request, *args, **kwargs)
