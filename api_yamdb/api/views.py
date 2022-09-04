from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.filters import SearchFilter
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken

from . import filtres, mixins, serializers
from .pagination import ReviewCommentPagination
from .permissions import IsAdmin, IsAdminOrReadonly, IsAuthorOrStaffOrReadOnly
from api_yamdb import settings
from reviews.models import Category, Genre, Title

User = get_user_model()


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.all().annotate(rating=Avg("reviews__score"))
    filter_backends = [DjangoFilterBackend]
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
        IsAdminOrReadonly
    ]
    filter_backends = [DjangoFilterBackend]
    filterset_class = filtres.TitleFilter
    lookup_field = "id" or "name"
    pagination_class = ReviewCommentPagination

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return serializers.ReadTitleSerializer
        return serializers.WriteTitleSerializer


class CategoryViewSet(mixins.CreateDestroyViewSet):
    queryset = Category.objects.all()
    serializer_class = serializers.CategorySerializer
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
        IsAdminOrReadonly
    ]
    filter_backends = [SearchFilter]
    search_fields = ["name"]
    lookup_field = "slug"


class GenreViewSet(mixins.CreateDestroyViewSet):
    queryset = Genre.objects.all()
    serializer_class = serializers.GenreSerializer
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
        IsAdminOrReadonly
    ]
    filter_backends = [SearchFilter]
    search_fields = ["name"]
    lookup_field = "slug"


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.ReviewSerializer
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
        IsAuthorOrStaffOrReadOnly
    ]
    pagination_class = ReviewCommentPagination

    def get_queryset(self):
        """Достаем отзывы произведения"""
        title = get_object_or_404(Title, pk=self.kwargs.get("title_id"))
        return title.reviews.all()

    def perform_create(self, serializer):
        """Добавляем отзыв к произведению и назначаем автора"""
        title = get_object_or_404(Title, pk=self.kwargs.get("title_id"))

        title_data = {"title": title, "author": self.request.user}
        serializer.save(**title_data)


@api_view(["post"])
def signup(request):
    serializer = serializers.UserEmailSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    user = get_object_or_404(User, username=request.data.get("username"))
    if not user.confirmation_code:
        user.confirmation_code = default_token_generator.make_token(user)
        user.save()
    send_mail(
        subject="Confirmation code",
        message=f"{user.confirmation_code}",
        from_email=settings.SEND_FROM_EMAIL,
        recipient_list=[user.email],)
    return Response(status=status.HTTP_200_OK, data=serializer.data)


@api_view(["post"])
def token(request):
    serializer = serializers.TokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = get_object_or_404(User, username=request.data.get("username"))

    if default_token_generator.check_token(
        user, serializer.data["confirmation_code"]
    ):
        token = AccessToken.for_user(user)
        return Response({"token": str(token)}, status=status.HTTP_200_OK)
    return Response(status=status.HTTP_400_BAD_REQUEST)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.CommentSerializer
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
        IsAuthorOrStaffOrReadOnly
    ]
    pagination_class = ReviewCommentPagination

    def get_queryset(self):
        """Достаем комментарии к отзыву произведения"""
        title = get_object_or_404(Title, pk=self.kwargs.get("title_id"))

        review = get_object_or_404(
            title.reviews, pk=self.kwargs.get("review_id")
        )
        return review.comments.all()

    def perform_create(self, serializer):
        """Добавляем комментарий к отзыву произведения"""
        title = get_object_or_404(Title, pk=self.kwargs.get("title_id"))
        review = get_object_or_404(
            title.reviews, pk=self.kwargs.get("review_id")
        )

        title_data = {"review": review, "author": self.request.user}
        serializer.save(**title_data)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = serializers.AdminSerializer
    lookup_field = "username"
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    filter_backends = [filters.SearchFilter]
    search_fields = ["username"]
    pagination_class = LimitOffsetPagination

    @action(
        methods=["patch", "get"],
        permission_classes=[IsAuthenticated],
        detail=False,
        url_path="me",
        url_name="me",
    )
    def me(self, request, *args, **kwargs):
        user = self.request.user
        serializer = serializers.UserSerializer(user)
        if self.request.method == "PATCH" and user.role != "user":
            serializer = serializers.UserSerializer(
                user, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return Response(serializer.data)
