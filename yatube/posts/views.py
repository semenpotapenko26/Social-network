from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, Group, User, Follow
from .constants import PER_PAGE
from .forms import PostForm, CommentForm
from django.contrib.auth.decorators import login_required
from .utils import paginate_page


def index(request):
    template = 'posts/index.html'
    post_list = Post.objects.all()
    page_obj = paginate_page(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    post_list = Post.objects.all()
    page_obj = paginate_page(request, post_list)
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()[:PER_PAGE]
    context = {
        'group': group,
        'posts': posts,
        'page_obj': page_obj
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    posts = Post.objects.filter(author__username=username).all()
    author = get_object_or_404(User, username=username)
    page_obj = paginate_page(request, posts)
    following = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(user=request.user).filter(
            author=author
        ).exists()
    context = {
        'author': author,
        'posts': posts,
        'page_obj': page_obj,
        'following': following
    }
    return render(request, template, context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    post_count = Post.objects.filter(author=post.author).count()
    template = 'posts/post_detail.html'
    form = CommentForm()
    context = {
        'post': post,
        'post_count': post_count,
        'form': form,
        'username': request.user,
        'comments': post.comments.all(),
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    form = PostForm(
        request.POST or None,
        files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user.username)
    context = {
        'form': form,
    }
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'form': form,
        'is_edit': True,
        'post': post,
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = paginate_page(request, posts)
    context = {
        'posts': posts,
        'page_obj': page_obj
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    follow = Follow.objects.filter(user=user, author=author)
    if user != author and not follow.exists():
        Follow.objects.create(user=user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    follow = Follow.objects.get(user=user, author=author)
    if user != author and follow:
        follow.delete()
    return redirect('posts:profile', username=username)
