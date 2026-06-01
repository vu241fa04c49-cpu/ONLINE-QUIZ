from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from django.views.generic import TemplateView

from accounts import views


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("about/", TemplateView.as_view(template_name="quiz/about.html"), name="about"),
    path("api-docs/", TemplateView.as_view(template_name="api_docs.html"), name="api_docs"),
    path("signup/", views.register_page, name="signup"),
    path("login/", views.login_page, name="login"),
    path("register/", views.register_page, name="register"),
    path("forgot-password/", views.forgot_password_page, name="forgot_password"),
    path("api/health/", views.api_health, name="api_health"),
    path("api/auth/me/", views.api_me, name="api_me"),
    path("api/auth/register/", views.api_register, name="api_register"),
    path("api/auth/login/", views.api_login, name="api_login"),
    path("api/auth/logout/", views.api_logout, name="api_logout"),
    path("api/auth/forgot-password/", views.api_forgot_password, name="api_forgot_password"),
    path("api/auth/verify-otp/", views.api_verify_otp, name="api_verify_otp"),
    path("api/auth/reset-password/", views.api_reset_password, name="api_reset_password"),
    path("api/quizzes/", views.api_quiz_list, name="api_quiz_list"),
    path("api/quizzes/<int:pk>/", views.api_quiz_detail, name="api_quiz_detail"),
    path("api/quizzes/<int:pk>/questions/", views.api_quiz_questions, name="api_quiz_questions"),
    path("api/questions/<int:pk>/", views.api_question_detail, name="api_question_detail"),
    path("api/quizzes/<int:pk>/start/", views.api_start_quiz, name="api_start_quiz"),
    path("api/quizzes/<int:pk>/submit/", views.api_submit_quiz, name="api_submit_quiz"),
    path("api/results/", views.api_results, name="api_results"),
    path("api/leaderboard/", views.api_leaderboard, name="api_leaderboard"),
    path("api/dashboard/", views.api_dashboard, name="api_dashboard"),
    path("api/profile/", views.api_profile, name="api_profile"),
    path("api/contact/", views.api_contact, name="api_contact"),
    path("api/newsletter/", views.api_newsletter, name="api_newsletter"),
    path("password-reset/email-sent/", TemplateView.as_view(template_name="auth/email_sent.html"), name="email_sent"),
    path("password-reset/success/", TemplateView.as_view(template_name="auth/password_reset_success.html"), name="password_reset_success"),
    path("verify-otp/", views.verify_otp_page, name="verify_otp"),
    path("reset-password/", views.reset_password_page, name="reset_password"),
    path("logout/", views.logout_page, name="logout"),
    path("dashboard/", views.student_dashboard, name="student_dashboard"),
    path("dashboard/admin-ui/", views.admin_dashboard, name="admin_dashboard"),
    path("quiz/", views.quiz_page, name="quiz"),
    path("quizzes/", views.quiz_list_page, name="quiz_list"),
    path("quiz/<int:pk>/", views.quiz_detail_page, name="quiz_detail"),
    path("quiz/<int:pk>/start/", views.start_quiz_page, name="start_quiz"),
    path("quiz/<int:pk>/question/", views.quiz_question_page, name="quiz_question"),
    path("result/", views.result_page, name="result"),
    path("leaderboard/", views.leaderboard_page, name="leaderboard"),
    path("profile/", views.profile_page, name="profile"),
    path("profile/edit/", views.edit_profile_page, name="edit_profile"),
    path("contact/", TemplateView.as_view(template_name="contact.html"), name="contact"),
    path("api/accounts/", views.serializer_view, name="api_accounts"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = "accounts.views.error_404"
handler500 = "accounts.views.error_500"
