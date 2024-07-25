from django.conf import settings
from django.db import models
import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class MyUserManager(BaseUserManager):
    def create_user(self, email, password=None, is_profesor=False, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        user = self.model(email=email, is_profesor=is_profesor, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_profesor', True)  # Assuming superusers are professors by default
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    username = models.CharField(max_length=30, unique=True)
    is_profesor = models.BooleanField(default=False)  # This field determines the user's role
    school = models.CharField(max_length=255, null=True, blank=True)  # Optional field for profesor
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = MyUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'username']

    def __str__(self):
        return self.email


class Friendship(models.Model):
    sender = models.ForeignKey(User, related_name="sent_friend_requests", on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name="received_friend_requests", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender} -> {self.receiver}"
    

class Course(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField()
    teachers = models.ManyToManyField(User, related_name='taught_courses', limit_choices_to={'is_profesor': True}, blank=True)
    entrance_code = models.CharField(max_length=50, unique=True, blank=True)
    students = models.ManyToManyField(User, related_name='enrolled_courses', blank=True)

    def save(self, *args, **kwargs):
        if not self.entrance_code:
            # Generate a unique entrance code
            self.entrance_code = get_random_string(length=8)  # Adjust length as needed
            while Course.objects.filter(entrance_code=self.entrance_code).exists():
                self.entrance_code = get_random_string(length=8)
        super(Course, self).save(*args, **kwargs)

    def __str__(self):
        return self.name
    

class Homework(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='homeworks')
    problems = models.TextField(default='No problems assigned')
    grading_criteria = models.TextField(default='No grading criteria set')
    title = models.CharField(max_length=255)
    description = models.TextField()
    deadline = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)


class Problem(models.Model):
    homework = models.ForeignKey(Homework, on_delete=models.CASCADE, related_name='probleme', null=True, blank=True)
    text = models.TextField()
    index = models.IntegerField(null=True, blank=True)  # Useful for ordering within homework

    def __str__(self):
        return f"Problem {self.id} {'in Homework ' + str(self.homework.id) if self.homework else 'Standalone'}"
    
    
class Solution(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='solutions')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='solutions')
    text = models.TextField()
    grade = models.IntegerField(null=True, blank=True)  # Assuming grading is numerical
    feedback = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    grades = models.JSONField(default=dict)

    def __str__(self):
        return f"Solution by {self.student} for Problem {self.problem.id}"
    

class MultipleChoiceProblem(models.Model):
    homework = models.ForeignKey(Homework, on_delete=models.CASCADE, related_name='multiple_choice_problems', null=True, blank=True)
    question = models.TextField()
    choices = models.JSONField()  # Stores choices as JSON, e.g., {"A": "Option 1", "B": "Option 2", "C": "Option 3"}
    correct_answer = models.CharField(max_length=1)  # Assuming single-letter answers

    def __str__(self):
        return f"MultipleChoiceProblem {self.id} in Homework {self.homework.id if self.homework else 'Standalone'}"
    

class MCQResult(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mcq_results')
    homework = models.ForeignKey(Homework, on_delete=models.CASCADE, related_name='mcq_results')
    correct_answers = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"MCQResult: {self.student.username} for Homework {self.homework.id} - {self.correct_answers}/{self.total_questions}"

    @property
    def score_percentage(self):
        if self.total_questions > 0:
            return (self.correct_answers / self.total_questions) * 100
        return 0
    


class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='received_messages', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender} to {self.receiver} at {self.timestamp}"