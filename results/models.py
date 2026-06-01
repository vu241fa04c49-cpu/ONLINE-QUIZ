from django.db import models

class Result(models.Model):
    quiz = models.ForeignKey(
        'quiz.Quiz',
        on_delete=models.CASCADE
    )
    score = models.IntegerField()