import random

from django.core.mail import get_connection, send_mail
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render

from attempts.models import Question
from quiz.models import Quiz
from results.models import Result

from .forms import ForgotPasswordForm, LoginForm, OTPForm, ProfileUpdateForm, RegisterForm, ResetPasswordForm
from .models import UserProfile
from .serializers import (
    AccountSerializer,
    ContactSerializer,
    ForgotPasswordRequestSerializer,
    LoginAPISerializer,
    NewsletterSerializer,
    OTPVerifySerializer,
    PasswordResetSerializer,
    ProfileAPISerializer,
    QuestionSerializer,
    QuestionWriteSerializer,
    QuizSerializer,
    QuizSubmitSerializer,
    QuizWriteSerializer,
    RegisterAPISerializer,
    ResultSerializer,
)
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

@api_view(['GET'])
def serializer_view(request):
    accounts = User.objects.all().order_by("username")
    serializer = AccountSerializer(accounts, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def api_health(request):
    return Response({"ok": True, "service": "QuizForge API", "version": "1.0"})


@api_view(["GET"])
@permission_classes([AllowAny])
def api_me(request):
    if not request.user.is_authenticated:
        return Response({"authenticated": False, "user": None})
    return Response({"authenticated": True, "user": AccountSerializer(request.user).data})


@api_view(["POST"])
@permission_classes([AllowAny])
def api_register(request):
    serializer = RegisterAPISerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    return Response(
        {
            "ok": True,
            "detail": "Account created successfully.",
            "user": AccountSerializer(user).data,
        },
        status=201,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def api_login(request):
    serializer = LoginAPISerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    username = serializer.validated_data["username"]
    if "@" in username:
        user_match = User.objects.filter(email__iexact=username).first()
        if user_match:
            username = user_match.username
    user = authenticate(
        request,
        username=username,
        password=serializer.validated_data["password"],
    )
    if not user:
        return Response({"ok": False, "detail": "Invalid username or password."}, status=400)
    login(request, user)
    if not serializer.validated_data.get("remember_me"):
        request.session.set_expiry(0)
    return Response({"ok": True, "detail": "Logged in successfully.", "user": AccountSerializer(user).data})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_logout(request):
    logout(request)
    return Response({"ok": True, "detail": "Logged out successfully."})


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def api_quiz_list(request):
    if request.method == "POST":
        denied = _staff_required_response(request)
        if denied:
            return denied
        serializer = QuizWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        quiz = serializer.save()
        return Response({"ok": True, "quiz": QuizSerializer(quiz).data}, status=201)

    quizzes = Quiz.objects.all().order_by("title")
    return Response({"count": quizzes.count(), "results": QuizSerializer(quizzes, many=True).data})


@api_view(["GET", "PUT", "PATCH", "DELETE"])
@permission_classes([AllowAny])
def api_quiz_detail(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    if request.method == "DELETE":
        denied = _staff_required_response(request)
        if denied:
            return denied
        quiz.delete()
        return Response(status=204)

    if request.method in {"PUT", "PATCH"}:
        denied = _staff_required_response(request)
        if denied:
            return denied
        serializer = QuizWriteSerializer(
            quiz,
            data=request.data,
            partial=request.method == "PATCH",
        )
        serializer.is_valid(raise_exception=True)
        quiz = serializer.save()
        return Response({"ok": True, "quiz": QuizSerializer(quiz).data})

    questions = Question.objects.filter(quiz=quiz).order_by("id")
    return Response(
        {
            "quiz": QuizSerializer(quiz).data,
            "questions": QuestionSerializer(questions, many=True).data,
        }
    )


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def api_quiz_questions(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    if request.method == "POST":
        denied = _staff_required_response(request)
        if denied:
            return denied
        serializer = QuestionWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = serializer.save(quiz=quiz)
        return Response({"ok": True, "question": QuestionSerializer(question).data}, status=201)

    questions = Question.objects.filter(quiz=quiz).order_by("id")
    return Response({"count": questions.count(), "results": QuestionSerializer(questions, many=True).data})


@api_view(["GET", "PUT", "PATCH", "DELETE"])
@permission_classes([AllowAny])
def api_question_detail(request, pk):
    question = get_object_or_404(Question, pk=pk)
    if request.method == "DELETE":
        denied = _staff_required_response(request)
        if denied:
            return denied
        question.delete()
        return Response(status=204)

    if request.method in {"PUT", "PATCH"}:
        denied = _staff_required_response(request)
        if denied:
            return denied
        serializer = QuestionWriteSerializer(
            question,
            data=request.data,
            partial=request.method == "PATCH",
        )
        serializer.is_valid(raise_exception=True)
        question = serializer.save()
        return Response({"ok": True, "question": QuestionSerializer(question).data})

    return Response({"question": QuestionSerializer(question).data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_start_quiz(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    questions = Question.objects.filter(quiz=quiz).order_by("id")
    return Response(
        {
            "ok": True,
            "quiz": QuizSerializer(quiz).data,
            "timer_seconds": 900,
            "anti_cheating": {
                "enabled": True,
                "signals": ["tab_hidden", "window_blur"],
                "message": "Tab switches and focus loss are counted in the final report.",
            },
            "questions": QuestionSerializer(questions, many=True).data,
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_submit_quiz(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    serializer = QuizSubmitSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    answers = serializer.validated_data["answers"]
    suspicious_count = serializer.validated_data["suspicious_count"]
    suspicious_events = serializer.validated_data["suspicious_events"]
    exam_locked = suspicious_count >= 3
    questions = Question.objects.filter(quiz=quiz)
    total = questions.count()
    correct = 0
    for question in questions:
        submitted = str(answers.get(str(question.id), answers.get(question.id, ""))).strip()
        if submitted.lower() == question.correct_answer.strip().lower():
            correct += 1
    percent = round((correct / total) * 100) if total else 0
    result = Result.objects.create(quiz=quiz, score=percent)
    return Response(
        {
            "ok": True,
            "result": ResultSerializer(result).data,
            "summary": {
                "total_questions": total,
                "correct": correct,
                "wrong": max(total - correct, 0),
                "score_percent": percent,
                "suspicious_count": suspicious_count,
                "suspicious_events": suspicious_events,
                "exam_locked": exam_locked,
                "anti_cheat_action": "exam_closed" if exam_locked else "reported",
            },
        },
        status=201,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_results(request):
    results = Result.objects.select_related("quiz").order_by("-id")[:25]
    return Response({"count": len(results), "results": ResultSerializer(results, many=True).data})


@api_view(["GET"])
@permission_classes([AllowAny])
def api_leaderboard(request):
    results = Result.objects.select_related("quiz").order_by("-score", "-id")[:10]
    rows = [
        {
            "rank": index,
            "name": f"Quiz Learner {index}",
            "quiz": result.quiz.title,
            "score": result.score,
        }
        for index, result in enumerate(results, start=1)
    ]
    if not rows:
        rows = [
            {"rank": 1, "name": "Anika Patel", "quiz": "Python Fundamentals", "score": 980},
            {"rank": 2, "name": "Rahul Kumar", "quiz": "Django Views", "score": 940},
            {"rank": 3, "name": "Maya Singh", "quiz": "Bootstrap UI", "score": 910},
        ]
    return Response({"results": rows})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_dashboard(request):
    quiz_count = Quiz.objects.count()
    result_count = Result.objects.count()
    average_score = 0
    if result_count:
        average_score = round(sum(Result.objects.values_list("score", flat=True)) / result_count)
    return Response(
        {
            "user": AccountSerializer(request.user).data,
            "stats": {
                "available_quizzes": quiz_count,
                "completed_quizzes": result_count,
                "average_score": average_score,
                "current_streak": 8,
            },
            "recent_results": ResultSerializer(
                Result.objects.select_related("quiz").order_by("-id")[:5],
                many=True,
            ).data,
        }
    )


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def api_profile(request):
    profile = _profile_for(request.user)
    if request.method == "GET":
        return Response(
            {
                "user": AccountSerializer(request.user).data,
                "profile": {
                    "bio": profile.bio,
                    "avatar": profile.avatar.url if profile.avatar else "",
                    "updated_at": profile.updated_at,
                },
            }
        )

    serializer = ProfileAPISerializer(data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    user = request.user
    for field in ("first_name", "last_name", "username", "email"):
        if field in data:
            setattr(user, field, data[field])
    user.save()
    if "bio" in data:
        profile.bio = data["bio"]
        profile.save()
    return Response({"ok": True, "detail": "Profile updated.", "user": AccountSerializer(user).data})


@api_view(["POST"])
@permission_classes([AllowAny])
def api_contact(request):
    serializer = ContactSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    return Response({"ok": True, "detail": "Thanks. Your message has been received."}, status=201)


@api_view(["POST"])
@permission_classes([AllowAny])
def api_newsletter(request):
    serializer = NewsletterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    return Response({"ok": True, "detail": "You are subscribed to quiz updates."}, status=201)


def _display_name(request):
    if request.user.is_authenticated:
        return request.user.get_full_name() or request.user.username
    return "kavya"


def _initials(name):
    parts = [part[0] for part in name.split() if part]
    return "".join(parts[:2]).upper() or "QF"


def _profile_for(user):
    if not user.is_authenticated:
        return None
    profile, _created = UserProfile.objects.get_or_create(user=user)
    return profile


def _send_password_reset_otp(request, email):
    user = User.objects.filter(email__iexact=email).first()
    if not user:
        return None, "No account was found with that email address."

    otp = f"{random.randint(10000, 99999)}"
    request.session["password_reset_email"] = email
    request.session["password_reset_otp"] = otp
    request.session["password_reset_verified"] = False

    email_connection = get_connection(fail_silently=True, timeout=5)
    send_mail(
        "Your QuizForge password reset OTP",
        f"Use this OTP to reset your QuizForge password: {otp}",
        getattr(settings, "DEFAULT_FROM_EMAIL", None),
        [email],
        fail_silently=True,
        connection=email_connection,
    )
    return otp, None


def _staff_required_response(request):
    if request.user.is_authenticated and request.user.is_staff:
        return None
    return Response({"ok": False, "detail": "Staff access is required for this method."}, status=403)


def home(request):
    context = {
        "features": [
            {"icon": "fa-solid fa-stopwatch", "title": "Timed quizzes", "text": "Keep assessments focused with clear timers and progress feedback."},
            {"icon": "fa-solid fa-chart-line", "title": "Instant results", "text": "Show performance, accuracy, and topic insights right after submission."},
            {"icon": "fa-solid fa-ranking-star", "title": "Leaderboards", "text": "Encourage friendly competition with rankings and score badges."},
            {"icon": "fa-solid fa-shield-halved", "title": "Clean UX", "text": "Accessible forms, responsive layouts, and smooth interactions throughout."},
        ],
        "stats": [
            {"value": "40k+", "label": "Quiz attempts"},
            {"value": "1.2k", "label": "Active learners"},
            {"value": "320", "label": "Question sets"},
            {"value": "96%", "label": "Satisfaction"},
        ],
        "steps": [
            {"title": "Create an account", "text": "Students register, log in, and get a dedicated dashboard."},
            {"title": "Start a quiz", "text": "Pick an available assessment and answer questions in a focused interface."},
            {"title": "Review results", "text": "See scores, accuracy, timing, and improvement areas immediately."},
        ],
        "testimonials": [
            {"quote": "The interface feels fast and keeps me focused on the questions.", "initials": "AP", "name": "Anika Patel", "role": "Student"},
            {"quote": "The dashboard makes progress easy to understand at a glance.", "initials": "RK", "name": "Rahul Kumar", "role": "Learner"},
            {"quote": "It has the polish I expect from modern learning platforms.", "initials": "MS", "name": "Maya Singh", "role": "Instructor"},
        ],
        "faqs": [
            {"question": "Can I use this with real Django models?", "answer": "Yes. The templates already use context variables that can be connected to querysets later."},
            {"question": "Is the frontend responsive?", "answer": "All layouts use Bootstrap grids, responsive spacing, and mobile-first CSS."},
            {"question": "Does it support authentication flows?", "answer": "Login, signup, forgot password, reset password, and logout screens are included."},
        ],
    }
    return render(request, "home.html", context)


def login_page(request):
    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        username = form.cleaned_data["username"]
        if "@" in username:
            user_match = User.objects.filter(email__iexact=username).first()
            if user_match:
                username = user_match.username
        user = authenticate(
            request,
            username=username,
            password=form.cleaned_data["password"],
        )
        if user:
            login(request, user)
            if not form.cleaned_data["remember_me"]:
                request.session.set_expiry(0)
            messages.success(request, "Welcome back. You are logged in.")
            return redirect("student_dashboard")
        messages.error(request, "Invalid username or password.")
    return render(request, "auth/login.html", {"form": form})


def register_page(request):
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        user.email = form.cleaned_data["email"]
        user.save()
        messages.success(request, "Account created successfully. Please log in.")
        return redirect("login")
    return render(request, "auth/register.html", {"form": form})


def forgot_password_page(request):
    form = ForgotPasswordForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"].strip().lower()
        otp, error = _send_password_reset_otp(request, email)
        if error:
            messages.error(request, error)
            return render(request, "auth/forgot_password.html", {"form": form})
        if settings.DEBUG:
            messages.info(request, f"Development OTP: {otp}")
        messages.success(request, "We sent a 5-digit OTP to your email.")
        return redirect("verify_otp")
    return render(request, "auth/forgot_password.html", {"form": form})


def verify_otp_page(request):
    if not request.session.get("password_reset_email"):
        messages.info(request, "Enter your email first to receive an OTP.")
        return redirect("forgot_password")

    form = OTPForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if form.cleaned_data["otp"] == request.session.get("password_reset_otp"):
            request.session["password_reset_verified"] = True
            messages.success(request, "OTP verified. Choose a new password.")
            return redirect("reset_password")
        form.add_error("otp", "The OTP you entered is incorrect.")
    return render(request, "auth/verify_otp.html", {"form": form})


def reset_password_page(request):
    if not request.session.get("password_reset_email"):
        messages.info(request, "Enter your email to receive a password reset OTP.")
        return redirect("forgot_password")
    if not request.session.get("password_reset_verified"):
        messages.info(request, "Please verify your OTP before resetting your password.")
        return redirect("verify_otp")

    form = ResetPasswordForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = request.session.get("password_reset_email")
        if email:
            user = get_object_or_404(User, email__iexact=email)
            user.set_password(form.cleaned_data["password"])
            user.save()
            for key in ("password_reset_email", "password_reset_otp", "password_reset_verified"):
                request.session.pop(key, None)
        messages.success(request, "Password updated successfully. Please log in.")
        return redirect("password_reset_success")
    return render(request, "auth/reset_password.html", {"form": form})


@api_view(["POST"])
def api_forgot_password(request):
    serializer = ForgotPasswordRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data["email"].strip().lower()
    otp, error = _send_password_reset_otp(request, email)
    if error:
        return Response({"ok": False, "detail": error}, status=404)

    payload = {
        "ok": True,
        "detail": "A 5-digit OTP has been sent to your email.",
        "next": "verify_otp",
    }
    if settings.DEBUG:
        payload["development_otp"] = otp
    return Response(payload)


@api_view(["POST"])
def api_verify_otp(request):
    serializer = OTPVerifySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    expected_otp = request.session.get("password_reset_otp")
    if not request.session.get("password_reset_email"):
        return Response({"ok": False, "detail": "Request a password reset OTP first."}, status=400)
    if serializer.validated_data["otp"] != expected_otp:
        return Response({"ok": False, "detail": "The OTP you entered is incorrect."}, status=400)

    request.session["password_reset_verified"] = True
    return Response({"ok": True, "detail": "OTP verified.", "next": "reset_password"})


@api_view(["POST"])
def api_reset_password(request):
    if not request.session.get("password_reset_email"):
        return Response({"ok": False, "detail": "Request a password reset OTP first."}, status=400)
    if not request.session.get("password_reset_verified"):
        return Response({"ok": False, "detail": "Verify your OTP before resetting your password."}, status=400)

    serializer = PasswordResetSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = get_object_or_404(User, email__iexact=request.session["password_reset_email"])
    user.set_password(serializer.validated_data["password"])
    user.save()
    for key in ("password_reset_email", "password_reset_otp", "password_reset_verified"):
        request.session.pop(key, None)
    return Response({"ok": True, "detail": "Password updated successfully."})


def logout_page(request):
    if request.method == "POST":
        logout(request)
        messages.success(request, "You have been logged out.")
        return redirect("home")
    return render(request, "auth/logout.html")


@login_required
def student_dashboard(request):
    name = _display_name(request)
    context = {
        "display_name": name,
        "initials": _initials(name),
        "metrics": [
            {"icon": "fa-solid fa-fire", "label": "Current streak", "value": "8 days"},
            {"icon": "fa-solid fa-bullseye", "label": "Accuracy", "value": "87%"},
            {"icon": "fa-solid fa-award", "label": "Best score", "value": "98"},
        ],
        "score_bars": [42, 65, 58, 74, 82, 70, 92],
        "quizzes": [
            {"title": "Python Fundamentals", "meta": "10 questions | 15 minutes | Beginner"},
            {"title": "Django Views and URLs", "meta": "12 questions | 20 minutes | Intermediate"},
            {"title": "HTML, CSS, Bootstrap", "meta": "15 questions | 18 minutes | Frontend"},
        ],
        "leaders": [
            {"name": "Anika Patel", "score": 980},
            {"name": "Rahul Kumar", "score": 940},
            {"name": name, "score": 910},
        ],
        "history": [
            {"quiz": "Python Fundamentals", "date": "May 20, 2026", "score": "92%", "status": "Passed", "status_class": "success"},
            {"quiz": "Bootstrap Layouts", "date": "May 18, 2026", "score": "84%", "status": "Passed", "status_class": "success"},
            {"quiz": "Django Templates", "date": "May 15, 2026", "score": "68%", "status": "Review", "status_class": "warning"},
        ],
    }
    return render(request, "dashboard/student.html", context)


@user_passes_test(lambda user: user.is_staff)
def admin_dashboard(request):
    context = {
        "admin_cards": [
            {"icon": "fa-solid fa-clipboard-question", "label": "Quizzes", "value": "42"},
            {"icon": "fa-solid fa-users", "label": "Students", "value": "1,284"},
            {"icon": "fa-solid fa-check-double", "label": "Attempts", "value": "40k"},
            {"icon": "fa-solid fa-chart-line", "label": "Avg score", "value": "82%"},
        ]
    }
    return render(request, "dashboard/admin.html", context)


def quiz_page(request):
    quizzes = Quiz.objects.all().order_by("title")
    context = {"quizzes": quizzes}
    return render(request, "quiz/quiz_list.html", context)


def quiz_list_page(request):
    return quiz_page(request)


def quiz_detail_page(request, pk=None):
    quiz = get_object_or_404(Quiz, pk=pk) if pk else None
    context = {
        "quiz": quiz,
        "question": {
            "text": "Which Python data type is immutable?",
            "options": ["Tuple", "List", "Dictionary", "Set"],
        }
    }
    return render(request, "quiz/quiz_detail.html", context)


@login_required
def start_quiz_page(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    return render(request, "quiz/start_quiz.html", {"quiz": quiz})


@login_required
def quiz_question_page(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    return render(request, "quiz/quiz_question.html", {"quiz": quiz})


@login_required
def result_page(request):
    name = _display_name(request)
    try:
        suspicious_count = int(request.GET.get("suspicious_count") or request.session.get("suspicious_count") or 0)
    except (TypeError, ValueError):
        suspicious_count = 0
    raw_events = request.GET.get("suspicious_events", "")
    suspicious_events = [event for event in raw_events.split("|") if event][:8]
    exam_locked = request.GET.get("exam_locked") == "1" or suspicious_count >= 3
    if not suspicious_events:
        suspicious_events = request.session.get("suspicious_events", [])
    request.session["suspicious_count"] = suspicious_count
    request.session["suspicious_events"] = suspicious_events
    context = {
        "display_name": name,
        "result": {"percent": 86, "correct": 13, "wrong": 2, "time": "12:48", "message": "You are performing strongly. Review the missed topics and retry for a higher rank."},
        "anti_cheating": {
            "suspicious_count": suspicious_count,
            "events": suspicious_events,
            "exam_locked": exam_locked,
            "status": "Exam closed for suspicious activity" if exam_locked else ("Clean attempt" if suspicious_count == 0 else "Review recommended"),
        },
        "performance": [
            {"label": "Concept clarity", "value": "Advanced"},
            {"label": "Speed", "value": "Fast"},
            {"label": "Recommended next quiz", "value": "Django URLs"},
        ],
    }
    return render(request, "quiz/result.html", context)


def leaderboard_page(request):
    context = {
        "leaderboard": [
            {"initials": "AP", "name": "Anika Patel", "quiz": "Python Fundamentals", "score": "980", "badge": "Champion", "badge_class": "warning"},
            {"initials": "RK", "name": "Rahul Kumar", "quiz": "Django Views", "score": "940", "badge": "Expert", "badge_class": "success"},
            {"initials": "AM", "name": _display_name(request), "quiz": "Bootstrap UI", "score": "910", "badge": "Rising", "badge_class": "primary"},
            {"initials": "NS", "name": "Neha Sharma", "quiz": "HTML5", "score": "880", "badge": "Sharp", "badge_class": "info"},
            {"initials": "VI", "name": "Vikram Iyer", "quiz": "CSS3", "score": "850", "badge": "Steady", "badge_class": "secondary"},
        ]
    }
    return render(request, "quiz/leaderboard.html", context)


@login_required
def profile_page(request):
    name = _display_name(request)
    profile = _profile_for(request.user)
    context = {
        "display_name": name,
        "initials": _initials(name),
        "profile": profile,
        "avatar_url": profile.avatar.url if profile and profile.avatar else "",
        "badges": ["Streak", "Top 10", "Python"],
        "profile_stats": [
            {"icon": "fa-solid fa-book-open", "label": "Completed", "value": "18"},
            {"icon": "fa-solid fa-clock", "label": "Practice time", "value": "11h"},
            {"icon": "fa-solid fa-star", "label": "Badges", "value": "7"},
        ],
    }
    return render(request, "dashboard/profile.html", context)


@login_required
def edit_profile_page(request):
    name = _display_name(request)
    profile = _profile_for(request.user)
    form = ProfileUpdateForm(
        request.POST or None,
        request.FILES or None,
        user=request.user,
        profile=profile,
    )
    context = {
        "display_name": name,
        "initials": _initials(name),
        "profile": profile,
        "avatar_url": profile.avatar.url if profile and profile.avatar else "",
        "form": form,
    }
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profile changes saved.")
        return redirect("profile")
    return render(request, "dashboard/edit_profile.html", context)


def error_404(request, exception):
    return render(request, "errors/404.html", status=404)


def error_500(request):
    return render(request, "errors/500.html", status=500)
