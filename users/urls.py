# users/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuthViewSet, UtilisateurViewSet, RoleViewSet, PermissionViewSet

router = DefaultRouter()
# AuthViewSet utilise 'auth' comme base d'URL
router.register('auth', AuthViewSet, basename='auth') 
router.register('users', UtilisateurViewSet, basename='user')
router.register('roles', RoleViewSet, basename='role')
router.register('permissions', PermissionViewSet, basename='permission')

urlpatterns = [
    path('', include(router.urls)),
]