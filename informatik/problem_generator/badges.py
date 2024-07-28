# badges.py

import logging

# Set up logging
logger = logging.getLogger(__name__)

from accounts.models import Badge, Solution

def award_badge(user, badge_name):
    try:
        badge = Badge.objects.get(name=badge_name)
        if not user.badges.filter(name=badge_name).exists():
            user.badges.add(badge)
            user.save()
            logger.info(f"Badge '{badge_name}' awarded to user '{user.username}'")
            return True
    except Badge.DoesNotExist:
        logger.error(f"Badge '{badge_name}' does not exist")
    return False

def check_and_award_centurion_badge(user):
    high_score_solutions = Solution.objects.filter(student=user, grade__gte=75).count()
    if high_score_solutions >= 100:
        if award_badge(user, "Centurion"):
            logger.info(f"Centurion badge awarded to {user.username}")
        else:
            logger.info(f"Centurion badge already awarded to {user.username}")

def check_and_award_first_problem_solved_badge(user):
    solved_problems_count = Solution.objects.filter(student=user).count()
    if solved_problems_count >= 1:
        if award_badge(user, "First Problem Solved"):
            logger.info(f"First Problem Solved badge awarded to {user.username}")
        else:
            logger.info(f"First Problem Solved badge already awarded to {user.username}")
# Add more badge-checking functions as needed
