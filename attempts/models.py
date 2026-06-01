from django.db import models
from quiz.models import Quiz


class Question(models.Model):
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE
    )
    question_text = models.TextField()
    correct_answer = models.CharField(max_length=255)

    def __str__(self):
        return self.question_text