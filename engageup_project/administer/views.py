# from django.shortcuts import render, redirect
# from django.urls import reverse_lazy
# from django.views.generic import ListView,UpdateView
# from main.models import User,Constant
# from .forms import UserRankForm,ConstantForm

# def administer_index(request):
#     return render(request, "administer/administer_index.html")
# class UserListView(ListView):
#     model = User
#     template_name = 'administer/ad_user_list.html'
#     context_object_name = 'users'
#     paginate_by = 10

#     def get_queryset(self):
#         show = self.request.GET.get('show')

#         if show == 'all':
#             return User.objects.all()
#         return User.objects.filter(is_active=True)

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['show_all'] = self.request.GET.get('show') == 'all'
#         return context

#     def post(self, request, *args, **kwargs):
#         action = request.POST.get('action')
#         selected_users = request.POST.getlist('selected_user')

#         if action == 'soft_delete' and selected_users:
#             User.objects.filter(
#                 pk__in=selected_users,
#                 is_active=True
#             ).exclude(
#                 pk=request.user.pk
#             ).update(is_active=False)

#         return redirect(request.path)

# class UserRankListView(ListView):
#     model = User
#     context_object_name = 'users'
#     template_name = 'administer/ad_select_rank.html'
#     paginate_by = 10  # ← スペル修正

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['form'] = UserRankForm()
#         return context

#     def post(self, request, *args, **kwargs):
#         selected_users = request.POST.getlist('selected_user')
#         form = UserRankForm(request.POST)

#         if selected_users and form.is_valid():
#             new_rank = form.cleaned_data['rank']

#             users = User.objects.filter(pk__in=selected_users)

#             for user in users:
#                 # ★ 自分自身はスキップ
#                 if user == request.user:
#                     continue

#                 user.rank = new_rank
#                 user.save()

#         return redirect('administer:select_rank')


# class ConstantListView(ListView):
#     model = Constant
#     context_object_name = 'constants'
#     template_name = 'administer/ad_constant_list.html'
#     paginate_by = 10  # ← スペル修正

# class ConstantUpdateView(UpdateView):
#     model = Constant
#     form_class = ConstantForm
#     template_name = 'administer/ad_constant_update.html'
#     success_url = reverse_lazy('constant_list')

#     def get_object(self, queryset=None):
#         return Constant.objects.first()

from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, UpdateView
from django.db.models import Q  # 検索機能のために追加
from main.models import User, Constant
from .forms import UserRankForm, ConstantForm

def administer_index(request):
    return render(request, "administer/administer_index.html")

# ==========================================================
# 【修正・統合】ユーザー一覧ビュー (Admin / Moderator 共通)
# ==========================================================
class UserListView(ListView):
    model = User
    template_name = 'administer/ad_user_list.html'
    context_object_name = 'users'
    paginate_by = 10

    # administer/views.py の UserListView 内

    def get_queryset(self):
        show = self.request.GET.get('show')
        query = self.request.GET.get('q')
        rank_filter = self.request.GET.get('rank') # ★追加：ランクのパラメータを取得

        # 1. 基本のフィルタ（有効・全表示）
        if show == 'all':
            queryset = User.objects.all()
        else:
            queryset = User.objects.filter(is_active=True)

        # 2. ランクでの絞り込み (星野追加)
        if rank_filter and rank_filter != 'all':
            queryset = queryset.filter(rank=rank_filter)

        # 3. 検索キーワードでの絞り込み
        if query:
            queryset = queryset.filter(
                Q(username__icontains=query) | 
                Q(email__icontains=query)
            )
        
        return queryset.order_by('-pk')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # ★現在選ばれているランクをHTMLに伝える
        context['current_rank'] = self.request.GET.get('rank', 'all')
        # ★ランクの選択肢をリストで渡す（models.pyの定義に合わせて適宜修正してください）
        context['rank_choices'] = ['administer', 'moderator', 'staff', 'visitor'] 
        
        context['show_all'] = self.request.GET.get('show') == 'all'
        return context

    def get_context_data(self, **kwargs):
        """HTMLに渡す追加データを定義"""
        context = super().get_context_data(**kwargs)
        
        # --- 星野追加：権限に応じたベーステンプレートの切り替え ---
        if self.request.user.rank == 'administer':
            context['base_template'] = "administer/administer_base.html"
        else:
            context['base_template'] = "moderator/moderator_base.html"
        # ------------------------------------------------------

        context['show_all'] = self.request.GET.get('show') == 'all'
        return context

    def post(self, request, *args, **kwargs):
        """一括削除・一括復元の処理 (Adminのみ実行可能)"""
        # モデレーターは何もしない
        if request.user.rank != 'administer':
            return redirect(request.path)

        action = request.POST.get('action')
        selected_users = request.POST.getlist('selected_user')

        if selected_users:
            if action == 'soft_delete':
                User.objects.filter(pk__in=selected_users).exclude(pk=request.user.pk).update(is_active=False)
            elif action == 'restore':
                User.objects.filter(pk__in=selected_users).update(is_active=True)

        return redirect(request.path)
# ==========================================================


# class UserRankListView(ListView):
#     model = User
#     context_object_name = 'users'
#     template_name = 'administer/ad_select_rank.html'
#     paginate_by = 10

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['form'] = UserRankForm()
#         return context
# administer/views.py

class UserRankListView(ListView):
    model = User
    context_object_name = 'users'
    template_name = 'administer/ad_select_rank.html'
    paginate_by = 10

    def get_queryset(self):
        # 権限変更画面なので、削除済みも含めて全て表示できるように調整
        # (削除済みを隠したい場合は .filter(is_active=True) にしてください)
        queryset = User.objects.all()

        # 1. 検索キーワードでの絞り込み
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(username__icontains=query) | 
                Q(email__icontains=query)
            )

        # 2. 権限（ランク）フィルタでの絞り込み
        rank_filter = self.request.GET.get('rank_filter')
        if rank_filter and rank_filter != 'all':
            queryset = queryset.filter(rank=rank_filter)
            
        return queryset.order_by('-pk')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # テンプレート切り替えロジック
        if self.request.user.rank == 'administer':
            context['base_template'] = "administer/administer_base.html"
        else:
            context['base_template'] = "moderator/moderator_base.html"

        # フィルタ用データ
        context['rank_choices'] = ['administer', 'moderator', 'staff', 'visitor'] 
        context['current_rank'] = self.request.GET.get('rank_filter', 'all')
        
        context['form'] = UserRankForm()
        return context

    def post(self, request, *args, **kwargs):
        selected_users = request.POST.getlist('selected_user')
        form = UserRankForm(request.POST)

        if selected_users and form.is_valid():
            new_rank = form.cleaned_data['rank']
            users = User.objects.filter(pk__in=selected_users)
            for user in users:
                if user == request.user:
                    continue
                user.rank = new_rank
                user.save()

        return redirect('administer:select_rank')


class ConstantListView(ListView):
    model = Constant
    context_object_name = 'constants'
    template_name = 'administer/ad_constant_list.html'
    paginate_by = 10

# administer/views.py

class ConstantUpdateView(UpdateView):
    model = Constant
    form_class = ConstantForm
    template_name = 'administer/ad_constant_update.html'
    
    success_url = reverse_lazy('administer:constant_list')

    def get_object(self, queryset=None):
        return Constant.objects.first()