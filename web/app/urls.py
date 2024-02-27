from django.urls import path

from app.views import MainPageView, LoginView, LogoutView

urlpatterns = [
    path("", MainPageView.as_view(), name="main"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("registration/", LogoutView.as_view(), name="registration"),
]
# path("links/", generic_page_view("links"), name="links"),
# path("about/", generic_page_view("about"), name="about"),
# path("user_agreement/", generic_page_view("user_agreement"), name="user_agreement"),
# path("contacts/", generic_page_view("contacts"), name="contacts"),
# path("personal_data_policy/", generic_page_view("personal_data_policy"), name="personal_data_policy"),
# path("registration/", UserCreateView.as_view(), name="registration"),
