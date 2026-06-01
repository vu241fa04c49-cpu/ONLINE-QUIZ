from django import forms
from django.contrib.auth.models import User

from .models import UserProfile


class LoginForm(forms.Form):
    username = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput)
    remember_me = forms.BooleanField(required=False)


class RegisterForm(forms.Form):
    full_name = forms.CharField(max_length=150)
    username = forms.CharField(max_length=100)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)
    terms = forms.BooleanField(error_messages={"required": "You must accept the terms to continue."})

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password2 = cleaned_data.get("password2")
        if password2 and password != password2:
            self.add_error("password2", "Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        name_parts = self.cleaned_data["full_name"].strip().split(" ", 1)
        user = User(
            username=self.cleaned_data["username"],
            email=self.cleaned_data["email"],
            first_name=name_parts[0],
            last_name=name_parts[1] if len(name_parts) > 1 else "",
        )
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField()


class OTPForm(forms.Form):
    otp = forms.CharField(
        min_length=5,
        max_length=5,
        widget=forms.TextInput(
            attrs={
                "inputmode": "numeric",
                "autocomplete": "one-time-code",
                "maxlength": "5",
                "pattern": "[0-9]{5}",
            }
        ),
    )


class ResetPasswordForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password2 = cleaned_data.get("password2")
        if password2 and password != password2:
            self.add_error("password2", "Passwords do not match.")
        return cleaned_data


class ProfileUpdateForm(forms.Form):
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    username = forms.CharField(max_length=100)
    email = forms.EmailField()
    bio = forms.CharField(required=False, widget=forms.Textarea)
    avatar = forms.FileField(required=False)

    def __init__(self, *args, user=None, profile=None, **kwargs):
        self.user = user
        self.profile = profile
        initial = kwargs.pop("initial", {})
        if user:
            initial.update(
                {
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "username": user.username,
                    "email": user.email,
                }
            )
        if profile:
            initial["bio"] = profile.bio
        super().__init__(*args, initial=initial, **kwargs)

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        queryset = User.objects.filter(username__iexact=username)
        if self.user:
            queryset = queryset.exclude(pk=self.user.pk)
        if queryset.exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        queryset = User.objects.filter(email__iexact=email)
        if self.user:
            queryset = queryset.exclude(pk=self.user.pk)
        if queryset.exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean_avatar(self):
        avatar = self.cleaned_data.get("avatar")
        if not avatar:
            return avatar
        allowed_types = {"image/jpeg", "image/png", "image/webp"}
        if getattr(avatar, "content_type", "") not in allowed_types:
            raise forms.ValidationError("Upload a JPG, PNG, or WebP image.")
        if avatar.size > 2 * 1024 * 1024:
            raise forms.ValidationError("Profile image must be 2 MB or smaller.")
        return avatar

    def save(self):
        user = self.user
        profile = self.profile or UserProfile(user=user)
        user.first_name = self.cleaned_data["first_name"].strip()
        user.last_name = self.cleaned_data["last_name"].strip()
        user.username = self.cleaned_data["username"]
        user.email = self.cleaned_data["email"]
        user.save()
        profile.bio = self.cleaned_data.get("bio", "").strip()
        avatar = self.cleaned_data.get("avatar")
        if avatar:
            profile.avatar = avatar
        profile.save()
        return user, profile
