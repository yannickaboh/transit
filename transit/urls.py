"""
URL configuration for transit project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

# urls.py (projet principal)
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions

# ⚠️ NOUVEL IMPORT NÉCESSAIRE ⚠️
from rest_framework_simplejwt.authentication import JWTAuthentication # Importez JWTAuthentication

from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Configuration du schéma Swagger
schema_view = get_schema_view(
   openapi.Info(
      title="API Plateforme Portuaire Intelligente (PPPI)",
      default_version='v1',
      description="Documentation de l'API REST pour la gestion et le suivi des colis au port de Libreville/Owendo.",
      contact=openapi.Contact(email="contact@transit241.com"),
      license=openapi.License(name="Licence Propriétaire"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # ... autres chemins ...
    path("admin/", admin.site.urls),
    
    # Chemins de l'API
    path('api/v1/', include('users.urls')),
    path('api/v1/', include('logistics.urls')),
    path('api/v1/', include('payments.urls')),
    path('api/v1/', include('audit.urls')),
    
    # Chemins Swagger/Redoc
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# transit/urls.py (À la toute fin du fichier)

# S'assurer que le mode DEBUG est activé (ce qui est le cas dans votre configuration)
if settings.DEBUG:
    # Ceci est CRITIQUE en développement pour servir les fichiers médias
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
# Si vous servez aussi des fichiers statiques en développement (pas obligatoire)
# urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Assurez-vous d'utiliser un routeur (Router) dans chaque module pour enregistrer les ViewSets :
# users/urls.py
# from rest_framework.routers import DefaultRouter
# router = DefaultRouter()
# router.register('auth', AuthViewSet, basename='auth')
# ...
# urlpatterns = router.urls