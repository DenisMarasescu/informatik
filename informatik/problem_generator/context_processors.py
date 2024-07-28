# problem_generator/context_processors.py

from accounts.models import Friendship
from django.db.models import Q

def friends_list(request):
    if request.user.is_authenticated:
        friendships = Friendship.objects.filter(
            Q(sender=request.user) | Q(receiver=request.user),
            accepted=True
        )
        friends = [friendship.receiver if friendship.sender == request.user else friendship.sender for friendship in friendships]
    else:
        friends = []
    return {'friends': friends}
