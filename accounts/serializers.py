from django.contrib.auth.models import User as AuthUser
from rest_framework import serializers

from attempts.models import Question
from quiz.models import Quiz
from results.models import Result


class AccountSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model = AuthUser
        fields = ("id", "username", "email", "first_name", "last_name", "full_name")
        read_only_fields = fields


class ForgotPasswordRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class OTPVerifySerializer(serializers.Serializer):
    otp = serializers.CharField(min_length=5, max_length=5)

    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("OTP must contain digits only.")
        return value


class PasswordResetSerializer(serializers.Serializer):
    password = serializers.CharField(min_length=8, write_only=True)
    password2 = serializers.CharField(min_length=8, write_only=True)

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password2": "Passwords do not match."})
        return attrs


class RegisterAPISerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=150)
    username = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    password2 = serializers.CharField(min_length=8, write_only=True)

    def validate_username(self, value):
        if AuthUser.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate_email(self, value):
        if AuthUser.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value.lower()

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password2": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        full_name = validated_data["full_name"].strip()
        name_parts = full_name.split(" ", 1)
        return AuthUser.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=name_parts[0],
            last_name=name_parts[1] if len(name_parts) > 1 else "",
        )


class LoginAPISerializer(serializers.Serializer):
    username = serializers.CharField(max_length=100)
    password = serializers.CharField(write_only=True)
    remember_me = serializers.BooleanField(required=False, default=False)


class QuizSerializer(serializers.ModelSerializer):
    question_count = serializers.IntegerField(source="question_set.count", read_only=True)

    class Meta:
        model = Quiz
        fields = ("id", "title", "question_count")


class QuizWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = ("title",)


class QuestionWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ("question_text", "correct_answer")


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ("id", "quiz", "question_text")
        read_only_fields = fields


class ResultSerializer(serializers.ModelSerializer):
    quiz_title = serializers.CharField(source="quiz.title", read_only=True)

    class Meta:
        model = Result
        fields = ("id", "quiz", "quiz_title", "score")


class QuizSubmitSerializer(serializers.Serializer):
    answers = serializers.DictField(
        child=serializers.CharField(allow_blank=True),
        help_text="Map question IDs to selected answers.",
    )
    suspicious_count = serializers.IntegerField(required=False, min_value=0, default=0)
    suspicious_events = serializers.ListField(
        child=serializers.CharField(max_length=120),
        required=False,
        default=list,
    )


class ProfileAPISerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    username = serializers.CharField(max_length=100, required=False)
    email = serializers.EmailField(required=False)
    bio = serializers.CharField(required=False, allow_blank=True)


class ContactSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    subject = serializers.CharField(max_length=180, required=False, allow_blank=True)
    message = serializers.CharField(max_length=2000)


class NewsletterSerializer(serializers.Serializer):
    email = serializers.EmailField()
