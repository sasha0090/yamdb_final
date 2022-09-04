from django.contrib.auth import get_user_model
from django.core.validators import (MaxValueValidator, MinValueValidator,
                                    validate_slug)
from django.db import models

from reviews import constants

User = get_user_model()


class Category(models.Model):
    name = models.CharField(max_length=256, db_index=True)
    slug = models.SlugField(
        unique=True, max_length=50, validators=[validate_slug]
    )

    class Meta:
        verbose_name = "Категория"
        ordering = ["-name"]

    def __str__(self):
        return self.name[:constants.CATEGORY_STRING_LENGTH]


class Genre(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = "Жанр"
        ordering = ["-name"]

    def __str__(self):
        return self.name[:constants.GENRE_STRING_LENGTH]


class Title(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    year = models.IntegerField(null=True, blank=True)
    description = models.TextField(null=True)
    genre = models.ManyToManyField(Genre, related_name="titles", blank=True)
    category = models.ForeignKey(
        Category, null=True, on_delete=models.SET_NULL, related_name="category"
    )

    def __str__(self):
        return self.name[:constants.TITLE_STRING_LENGTH]

    class Meta:
        verbose_name = "Произведение"
        ordering = ["-name"]


class Review(models.Model):
    title = models.ForeignKey(
        Title, on_delete=models.CASCADE, related_name="reviews"
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="reviews"
    )
    text = models.TextField("Текст")
    score = models.IntegerField(
        "Оценка", validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    pub_date = models.DateTimeField("Дата публикации", auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["title", "author"],
                name="unique_review",
            )
        ]
        ordering = ["-pub_date"]

    def __str__(self):
        return self.text[:constants.TITLE_STRING_LENGTH]


class Comment(models.Model):
    review = models.ForeignKey(
        Review, on_delete=models.CASCADE, related_name="comments"
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="comments"
    )
    text = models.TextField("Текст")
    pub_date = models.DateTimeField("Дата публикации", auto_now_add=True)

    class Meta:
        ordering = ["-pub_date"]

    def __str__(self):
        return self.text[:constants.TITLE_STRING_LENGTH]
