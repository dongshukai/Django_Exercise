# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView
from django.core.mail import send_mail
from taggit.models import Tag
from .forms import EmailPostform, CommentForm
from .models import Post


def post_list(request, tag_slug):
    posts_list = Post.published.all()
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        posts_list = posts_list.filter(tags__in=[tag])
    paginator = Paginator(posts_list, 3) # 3篇文章一页
    page = request.GET.get('page')

    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)

    result = {
        'page': page,
        'posts': posts,
        'tag': tag,
    }

    return render(request, 'blog/post/list.html', result)


def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post,
                             slug=post,
                             status='published',
                             publish__year=year,
                             publish__month=month,
                             publish__day=day)
    # post的所有active=True的评论
    comments = post.comments.filter(active=True)
    new_comment = None

    if request.method == 'POST':
        # 生成一个评论
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            # 评论生成，但未保存到数据库
            new_comment = comment_form.save(commit=False)
            # 为评论分配一个博客文章
            new_comment.post = post
            # 将评论保存到数据库
            new_comment.save()
    else:
        comment_form = CommentForm()

    result = {
        'post': post,
        'comments': comments,
        'new_comment': new_comment,
        'comment_form': comment_form,
    }

    return render(request, 'blog/post/detail.html', result)


class PostListView(ListView):
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'blog/post/list.html'


def post_share(request, post_id):
    post = get_object_or_404(Post, id=post_id, status='published')
    cd = None
    sent = False
    if request.method == 'POST':
        # 提交表单，开始验证
        form = EmailPostform(request.POST)
        if form.is_valid():
            # 验证通过
            cd = form.cleaned_data  # 获取合法数据
            # 发送邮件...
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = '{} ({}) recommends you reading "{}"'.format(cd['name'], cd['email'], post.title)
            message = 'Read "{}" at {}\n\n{}\'s comments: {}'.format(post.title, post_url, cd['name'], cd['comments'])
            send_mail(subject, message, '1753123779@qq.com', [cd['to']])
            sent = True

    else:
        form = EmailPostform()

    result = {
        'post': post,
        'form': form,
        # 'cd': cd,
        'sent': sent,
    }
    return render(request, 'blog/post/share.html', result)
