# logistics/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ColisViewSet, SuiviStatutViewSet, RetraitColisViewSet, FileUploadView

router = DefaultRouter()
router.register('colis', ColisViewSet, basename='colis')
router.register('suivi-statuts', SuiviStatutViewSet, basename='suivi-statut')
router.register('retraits', RetraitColisViewSet, basename='retrait')

# Les endpoints spécifiques sont gérés par le router
# ColisViewSet.track_colis est accessible via le router car il est marqué @action

urlpatterns = [
    # 1. PLACEZ LE CHEMIN SPÉCIFIQUE EN PREMIER !
    # Django recherche la correspondance dans l'ordre, il trouvera celui-ci avant le router.
    path('retraits/upload-identite/', FileUploadView.as_view(), name='upload_identite'), 
    
    # 2. Le Router est inclus après, il prendra tout le reste.
    path('', include(router.urls)),
]

# Les URLs générées seront de la forme :
# /api/v1/colis/
# /api/v1/colis/track/ (Action personnalisée, accessible via le router)
# /api/v1/suivi-statuts/
# /api/v1/retraits/{id}/