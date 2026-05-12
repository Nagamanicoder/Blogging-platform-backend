from django.shortcuts import render

# Create your views here.
import django.utils.timezone as timezone
from rest_framework import viewsets
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Blog
from .serializers import BlogSerializer, BlogUpdateSerializer
from .services.utils import upload_image, replace_image, delete_image




class BlogViewSet(viewsets.ViewSet):

    def get_permissions(self):
        if self.action in ('public_list', 'retrieve'):
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_object(self, pk):
        try:
            return Blog.objects.get(pk=pk, is_deleted=False)
        except Blog.DoesNotExist:
            return None

    # CREATE
    def create(self, request):
        serializer = BlogSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        uploaded_image = request.FILES.get('uploaded_image')

        blog = Blog.objects.create(
            creator=request.user,
            title=serializer.validated_data['title'],
            content=serializer.validated_data['content'],
        )

        if uploaded_image:
            try:
                image_data = upload_image(uploaded_image)
                blog.image_url = image_data['image_url']
                blog.object_key = image_data['object_key']
                blog.save()
            except Exception:
                blog.delete()
                return Response({'message': 'image upload failed'}, status=502)

        return Response(BlogSerializer(blog).data, status=201)

    # UPDATE
    def partial_update(self, request, pk=None):
        blog = self.get_object(pk)
        if not blog:
            return Response({'message': 'blog not found'}, status=404)

        if blog.creator != request.user:
            return Response({'message': 'permission denied'}, status=403)

        serializer = BlogUpdateSerializer(blog, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        new_image = request.FILES.get('uploaded_image')

        if new_image:
            try:
                if blog.object_key:
                    new_url = replace_image(new_image, blog.object_key)
                    blog.image_url = new_url
                else:
                    image_data = upload_image(new_image)
                    blog.image_url = image_data['image_url']
                    blog.object_key = image_data['object_key']
            except Exception:
                return Response({'message': 'image upload failed'}, status=502)

        blog.title = serializer.validated_data.get('title', blog.title)
        blog.content = serializer.validated_data.get('content', blog.content)
        blog.save()

        return Response(BlogSerializer(blog).data, status=200)

    # DELETE
    def destroy(self, request, pk=None):
        blog = self.get_object(pk)
        if not blog:
            return Response({'message': 'blog not found'}, status=404)

        if blog.creator != request.user:
            return Response({'message': 'permission denied'}, status=403)

        if blog.object_key:
            delete_image(blog.object_key)

        blog.is_deleted = True
        blog.deleted_at = timezone.now()
        blog.save()

        return Response({'message': 'Blog deleted successfully'}, status=200)

    # PUBLISH
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        blog = self.get_object(pk)
        if not blog:
            return Response({'message': 'blog not found'}, status=404)

        if blog.creator != request.user:
            return Response({'message': 'permission denied'}, status=403)

        if blog.is_published:
            return Response({'message': 'already published'}, status=400)

        blog.is_published = True
        blog.published_at = timezone.now()
        blog.save()

        return Response({'message': 'published', 'published_at': blog.published_at})

    # DRAFTS
    @action(detail=False, methods=['get'])
    def drafts(self, request):
        blogs = Blog.objects.filter(
            creator=request.user,
            is_published=False,
            is_deleted=False
        )
        return Response(BlogSerializer(blogs, many=True).data)

    @action(detail=True, methods=['get'], url_path='draft')
    def draft_detail(self, request, pk=None):
        blog = get_object_or_404(Blog, pk=pk, creator=request.user, is_published=False, is_deleted=False)
        return Response(BlogSerializer(blog).data)

    # ME
    @action(detail=False, methods=['get'])
    def me(self, request):
        blogs = Blog.objects.filter(
            creator=request.user,
            is_deleted=False
        )
        return Response(BlogSerializer(blogs, many=True).data)

    # PUBLIC
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def public_list(self, request):
        blogs = Blog.objects.filter(
            is_published=True,
            is_deleted=False
        )
        return Response(BlogSerializer(blogs, many=True).data)

    # get particular blog
    def retrieve(self, request, pk=None):
        blog = self.get_object(pk)
        if not blog:
            return Response({'message': 'blog not found'}, status=404)

        # allow public access only if published
        if not blog.is_published:
            return Response({'message': 'not available'}, status=403)

        return Response(BlogSerializer(blog).data)