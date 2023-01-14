from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.conf import settings

from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm


def paginate(request, posts, page_count=settings.PAGINATE_POST_COUNT):
    paginator = Paginator(posts, page_count)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def index(request):
    template = 'posts/index.html'
    posts = Post.objects.all()
    page_obj = paginate(request, posts)
    context = {'page_obj': page_obj}
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = paginate(request, posts)
    context = {'group': group,
               'page_obj': page_obj, }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    page_obj = paginate(request, posts)
    posts_count = posts.count()
    if request.user.id is None:
        following = False
    else:
        following = Follow.objects.filter(user_id=request.user.id,
                                          author_id=author.id).exists()
    context = {'page_obj': page_obj,
               'posts_count': posts_count,
               'author': author,
               'following': following,
               }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, id=post_id)
    posts_count = post.author.posts.all().count()
    form = CommentForm()
    comments = post.comments.all()
    context = {'post': post,
               'posts_count': posts_count,
               'comments': comments,
               'form': form}
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    form = PostForm(request.POST or None, files=request.FILES or None)

    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = request.user
        new_post.save()
        return redirect('posts:profile', request.user.username)

    return render(request, template, {'form': form})


def post_edit(request, post_id):
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, id=post_id)

    if get_object_or_404(User, id=post.author_id) != request.user:
        return redirect('posts:post_detail', post_id)

    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=post)

    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)

    return render(request, template, {'form': form, 'is_edit': True})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
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
    following = Follow.objects.filter(user=request.user).values('author_id')
    posts = Post.objects.filter(author__in=following)

    page_obj = paginate(request, posts)
    context = {'page_obj': page_obj}
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    user = get_object_or_404(User, username=request.user)
    author = get_object_or_404(User, username=username)
    if not Follow.objects.filter(
            user_id=user.id,
            author_id=author.id).exists() and user.id != author.id:
        Follow.objects.create(user_id=user.id, author_id=author.id)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    user = get_object_or_404(User, username=request.user)
    author = get_object_or_404(User, username=username)
    if Follow.objects.filter(user_id=user.id,
                             author_id=author.id).exists():
        Follow.objects.filter(user_id=user.id, author_id=author.id).delete()
    return redirect('posts:profile', username=username)
