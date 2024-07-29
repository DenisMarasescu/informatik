import base64
import io
import logging
import re
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.db import models 
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views import View
from accounts.forms import UserProfileForm
import problem_generator.badges as Badges
from django.views.decorators.csrf import csrf_exempt
import openai
import random
from openai import OpenAI
import os
from groq import Groq
import json
from django.http import JsonResponse  # Add this import

import matplotlib
matplotlib.use('Agg')  # Use the Agg backend for non-interactive use
import matplotlib.pyplot as plt
import pandas as pd



from accounts.models import Course, Friendship, Homework, MCQResult, MultipleChoiceProblem, Problem, Solution, User, Message, Notification
from .forms import CourseForm, HomeworkCreationForm, ProblemGenerationForm, SingleDifficultyProblemGenerationForm, SolutionForm, TestCreationForm

# Create your views here.
def generate_problem(request):
    if request.method == 'POST':
        form = SingleDifficultyProblemGenerationForm(request.POST)
        if form.is_valid():
            print("E VALID")
            theme = dict(form.fields['theme'].choices)[form.cleaned_data['theme']]
            difficulty = form.cleaned_data['difficulty']

            system_prompt = '''You are a romanian speaking creative informatics problem generator for highschool students.
              You have to generate problems of different difficulties, offering a friendly problem statement, an input sample and an output sample.
              You will output the problems in the following JSON format:
              {
                "Titlu": "titlu",
                "Enunt": "enunt",
                "Cerinta": "cerinta",
                "Input": "input",
                "Output": "output",
                "Restrictii": "restrictii",
                "Exemplu": "exemplu",
                "Explicatie_exemplu": "explicatie"
              }
              You will output only the JSON, nothing more or less.
              You don't have to offer explanations about the way the problem can be solved. If provided a solution, you can give a grade from 0 to 100.
              The grading system is based on 3 benchmarks: correctness of the syntax, efficiency of the algorithm used, and code readability.
              After grading, explain what can be improved but don't provide a correct solution.
              You have to output the problems only in Romanian.'''

            
            user_prompt = f"Please generate a {difficulty} difficulty problem related to {theme}."
            
            # openai.api_key = "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"
            # client = OpenAI(api_key=openai.api_key, base_url = "https://integrate.api.nvidia.com/v1",)
            # response = client.chat.completions.create(
            #     model="nvidia/nemotron-4-340b-instruct",
            #     messages=[
            #         {"role": "system", "content": system_prompt},
            #         {"role": "user", "content": user_prompt}
            #     ],
            #     temperature=0.5,
            #     max_tokens=1024,
            #     top_p=1,
            #     frequency_penalty=0,
            #     presence_penalty=0,
                
            # )


            client = Groq(api_key="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")
            response = client.chat.completions.create(
                messages=[
                        {
                            "role": "system",
                            "content": system_prompt
                        },
                        {
                            "role": "user",
                            "content": user_prompt,
                        }
                ],
                model="llama3-70b-8192",
            )
            
            generated_problem = response.choices[0].message.content if response.choices else "I couldn't generate a problem. Please try again."
            
            problem = Problem.objects.create(
                text=generated_problem,
                # Set index or homework if needed
            )

            print(generate_problem)

            return redirect('problem_detail', problem_id=problem.id)
    else:
        form = SingleDifficultyProblemGenerationForm()
        print("NU E VALID COAIE")
    return render(request, 'problem_generator/generate_problem.html', {'form': form})

@login_required
def correct_problem(request):
    if request.method == 'POST':
        # Call GPT-4 API to correct the problem based on the form input
        pass  # Replace with actual code to call GPT-4 API
    return render(request, 'problem_generator/correct_problem.html')


@login_required
def search_users(request):
    query = request.GET.get('query', '')
    users = User.objects.filter(Q(username__icontains=query) | Q(email__icontains=query)).exclude(id=request.user.id)
    
    # Fetch the user's friends
    friendships = Friendship.objects.filter(Q(sender=request.user) | Q(receiver=request.user), accepted=True)
    friends = {friendship.receiver.id if friendship.sender == request.user else friendship.sender.id for friendship in friendships}
    
    return render(request, 'problem_generator/search_users.html', {'users': users, 'friends': friends})

@login_required
def send_friend_request(request, user_id):
    receiver = get_object_or_404(User, id=user_id)
    if receiver == request.user:
        messages.error(request, "You cannot send a friend request to yourself.")
        return redirect('search_users')
    
    # Check if a friend request already exists
    friendship, created = Friendship.objects.get_or_create(sender=request.user, receiver=receiver)
    if created:
        messages.success(request, f"Friend request sent to {receiver.username}.")
    else:
        messages.info(request, f"You have already sent a friend request to {receiver.username}.")
    
    return redirect('search_users')


@login_required
def friend_requests(request):
    requests = Friendship.objects.filter(receiver=request.user, accepted=False)
    return render(request, 'problem_generator/friend_requests.html', {'requests': requests})

@login_required
def accept_friend_request(request, request_id):
    friend_request = Friendship.objects.get(id=request_id)
    friend_request.accepted = True
    friend_request.save()
    messages.success(request, f"You are now friends with {friend_request.sender.username}.")

    return redirect('profile')

@login_required
def view_friends(request):
    # Fetch friendships where the current user is either the sender or receiver and the request has been accepted
    friendships = Friendship.objects.filter(
        (models.Q(sender=request.user) | models.Q(receiver=request.user)),
        accepted=True
    )
    # Prepare a list of friend User instances, excluding the current user
    friends = []
    for friendship in friendships:
        if friendship.sender == request.user:
            friends.append(friendship.receiver)
        else:
            friends.append(friendship.sender)

    return render(request, 'problem_generator/friends_list.html', {'friends': friends})

@login_required
def enroll_in_course(request):
    if request.method == "POST":
        entrance_code = request.POST.get('entrance_code')
        course = Course.objects.filter(entrance_code=entrance_code).first()
        if course:
            course.students.add(request.user)
            # Redirect to a success page or the course detail page
            return redirect('problem_generator/course_details', course_id=course.id)
        else:
            # Handle the error (e.g., no course found with the provided code)
            return render(request, 'your_template.html', {'error': 'Invalid entrance code'})
    # If not a POST request, render the enrollment form
    return render(request, 'problem_generator/enroll_in_course.html')

@login_required
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    now = timezone.now()
    if request.user.is_profesor:  # Assuming `is_teacher` is a property or method to check if the user is a teacher
        homeworks = course.homeworks.all()
    else:
        homeworks = course.homeworks.filter(deadline__gte=now)

    return render(request, 'problem_generator/course_details.html', {'course': course, 'homeworks':homeworks, 'page_title': 'Clasă', 'active_section': 'class'})


@login_required
def create_course(request):
    if not request.user.is_profesor:
        return redirect('home')  # Or some other appropriate action

    if request.method == "POST":
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.save()
            course.teachers.add(request.user)  # Add the creator as a teacher
            course.save()
            # Optionally, redirect to a page showing the entrance code or send it to the teacher
            return redirect('course_detail', course_id=course.id)
    else:
        form = CourseForm()
    return render(request, 'problem_generator/create_course.html', {'form': form})

@login_required
def my_courses(request):
    # Assuming your User model has a 'taught_courses' relation to Course
    courses_taught = request.user.taught_courses.all()

    attending_courses = request.user.enrolled_courses.all()

    profesor = False

    if request.user.is_profesor:
        profesor = True

    return render(request, 'problem_generator/my_courses.html', {'courses': courses_taught, 'attending_courses': attending_courses, "profesor": profesor, "page_title":"Clase"})


@login_required
def generate_homework(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.user not in course.teachers.all():
        return redirect('course_detail', course_id=course.id)

    if request.method == 'POST':
        form = HomeworkCreationForm(request.POST)
        test_form = TestCreationForm(request.POST or None)
        if 'submit_homework' in request.POST and form.is_valid():
            num_problems = form.cleaned_data['num_problems']
            min_difficulty = form.cleaned_data['min_difficulty']
            max_difficulty = form.cleaned_data['max_difficulty']
            selected_themes = form.cleaned_data['themes']
            deadline = form.cleaned_data['deadline']
            title = form.cleaned_data.get('title', 'Untitled')
            description = form.cleaned_data.get('description', '')

            print(f"Generating {num_problems} problems with difficulty from {min_difficulty} to {max_difficulty} for themes {selected_themes}")

            system_prompt = '''You are a romanian speaking creative informatics problem generator for highschool students.
            You have to generate problems of different difficulties, offering a friendly problem statement, an input sample and an output sample.
            You will output the problems in the following JSON format:
            {
                "Titlu": "titlu",
                "Enunt": "enunt",
                "Cerinta": "cerinta",
                "Input": "input",
                "Output": "output",
                "Restrictii": "restrictii",
                "Exemplu": "exemplu",
                "Explicatie_exemplu": "explicatie"
            }
            You will output only the JSON, nothing more or less.
            You don't have to offer explanations about the way the problem can be solved. If provided a solution, you can give a grade from 0 to 100.
            The grading system is based on 3 benchmarks: correctness of the syntax, efficiency of the algorithm used, and code readability.
            After grading, explain what can be improved but don't provide a correct solution. You have to output the problems only in Romanian.'''

            user_prompt = f"Please generate a list of {num_problems} informatics problems with difficulty grades from {min_difficulty} to {max_difficulty} related to the following themes: {selected_themes}."

            print(f"User prompt: {user_prompt}")

            client = Groq(api_key="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")
            response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                model="llama3-70b-8192",
            )

            generated_problems = response.choices[0].message.content if response.choices else "I couldn't generate a problem. Please try again."
            print(f"Generated problems: {generated_problems}")

            # Extract the JSON part of the response
            json_start_index = generated_problems.find("[")
            json_end_index = generated_problems.rfind("]") + 1
            json_content = generated_problems[json_start_index:json_end_index]
            
            print(f"Extracted JSON: {json_content}")

            try:
                problems_json = json.loads(json_content)
                homework = Homework.objects.create(
                    course=course,
                    problems='',  # Can be left empty or store a summary
                    deadline=deadline,
                    title=title,
                    description=description,
                    grading_criteria={'correctness': 50, 'efficiency': 30, 'readability': 20},
                )

                problem_texts = []
                for problem in problems_json:
                    problem_instance = Problem.objects.create(
                        homework=homework,
                        text=json.dumps(problem),  # Save the problem as JSON text
                    )
                    problem_texts.append(problem_instance.text)
                    print(f"Saved problem: {problem}")

                # Optionally, you can save a summary or some reference to problems in the `problems` field
                homework.problems = "\n".join(problem_texts)
                homework.save()

                print(f"Homework created: {homework.id}")
                return redirect('course_detail', course_id=course.id)

            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                messages.error(request, "Failed to parse the generated problems. Please try again.")
                return redirect('create_homework', course_id=course.id)
            
        elif 'submit_test' in request.POST and test_form.is_valid():
            topics = test_form.cleaned_data.get('topics')
            difficulty = test_form.cleaned_data.get('difficulty')
            nOq = test_form.cleaned_data.get('number_of_problems')
            deadline = test_form.cleaned_data['deadline']
            title = test_form.cleaned_data.get('title', 'Untitled')

            system_prompt = '''You are a creative, romanian speaking, informatics problem generator that creates multiple problems with quiz-like answers in the following format:
            {
                "Question": "What is X?",
                "Choices": ["A. Option1", "B. Option2", "C. Option3"],
                "Correct": "A",
                "CodeSnippet": "optional code snippet"
            }
            Your task is to generate a specified number of such problems. The questions can be from simple theory questions to provided code separated from the question by ``` (before and after it) with provided input and you will have to tell the correct output.'''

            user_prompt = f"Generate a set of {nOq} quiz subjects with incrementing difficulty based on the topics: {topics}"

            print(f"User prompt for test: {user_prompt}")

            client = Groq(api_key="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")
            response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                model="llama3-70b-8192",
            )

            test = Homework.objects.create(
                title=test_form.cleaned_data['title'],
                deadline=deadline,
                course=course,
            )

            ai_output = response.choices[0].message.content
            print(f"AI output for test: {ai_output}")
            parsed_questions = parse_ai_output(ai_output)

            print(f"Parsed questions: {parsed_questions}")

            for question in parsed_questions:
                MultipleChoiceProblem.objects.create(
                    homework=test,
                    question=question['question'] + "\n\n" + question['code_snippet'] + "\n\n",
                    choices=question['choices'],
                    correct_answer=question['correct_answer'],
                )
                print(f"Saved question: {question}")

            print(f"Test created: {test.id}")
            return redirect('course_detail', course_id=course.id)
        else:
            print(f"Form errors: {form.errors}")
            print(f"Test form errors: {test_form.errors}")
    else:
        form = HomeworkCreationForm()
        test_form = TestCreationForm()

    return render(request, 'problem_generator/generate_homework.html', {'form': form, 'course': course, 'test_form': test_form})



def grade_solution(problem_text ,solution_text):
    system_prompt = """
    You are a Romanian speaking creative informatics problem grader for high school students.
    Your job is to ensure the correctness of the code provided and give a grade from 0 to 100 based on 3 benchmarks:
    - Corectitudinea sintaxei (Correctness of the syntax)
    - Eficiența algoritmului (Efficiency of the algorithm used)
    - Lizibilitatea codului (Readability of the code)

    After grading, provide only small tips for improvement in Romanian. Output only the grades and feedback in the following JSON format:
    {
        "Corectitudinea_sintaxei": score,
        "Eficiența_algoritmului": score,
        "Lizibilitatea_codului": score,
        "Sfaturi": ["tip 1"\n, "tip 2"\n, ...]
    }
    You will output only the JSON, nothing more or less.
    """
            
    user_prompt = f"""
    Correct the given informatics problem solution based on the 3 benchmarks. The problem statement is: {problem_text}.
    The solution: {solution_text}
    """

    # openai.api_key = "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"

    client = Groq(api_key="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")
    response = client.chat.completions.create(
                messages=[
                        {
                            "role": "system",
                            "content": system_prompt
                        },
                        {
                            "role": "user",
                            "content": user_prompt,
                        }
                ],
                model="llama3-70b-8192",
        )
    # pattern = r"Corectitudinea sintaxei: (\d+)</s> Eficiența algoritmului: (\d+)</s> Lizibilitatea codului: (\d+)"
    # matches = re.search(pattern, response.choices[0].message.content if response.choices else "")

    # if matches:
    #     # Extracting grades
    #     grades = [int(matches.group(1)), int(matches.group(2)), int(matches.group(3))]
        
    #     # Calculate average grade
    #     grade = sum(grades) / len(grades)

    #     # Extract feedback after the grades
    #     feedback_start = matches.end()
    #     feedback = response.choices[0].message.content[feedback_start:].strip() if len(response.choices[0].message.content) > feedback_start else "Feedback not available."
    # else:
    #     grade = 0  # Or some form of handling if grades cannot be extracted
    # feedback = response.choices[0].message.content if response.choices else "I couldn't correct the problem. Please try again."

    feedback_json = response.choices[0].message.content if response.choices else "{}"
    print("FEEDBACK: ", feedback_json)
    try:
        feedback_data = json.loads(feedback_json)
        grades = {
            "Corectitudinea_sintaxei": feedback_data.get("Corectitudinea_sintaxei", 0),
            "Eficiența_algoritmului": feedback_data.get("Eficiența_algoritmului", 0),
            "Lizibilitatea_codului": feedback_data.get("Lizibilitatea_codului", 0),
        }
        grade = sum(grades.values()) / len(grades)
        feedback = feedback_data.get("Sfaturi", ["Feedback not available."])
    except json.JSONDecodeError:
        grade = 0
        grades = {
            "Corectitudinea_sintaxei": 0,
            "Eficiența_algoritmului": 0,
            "Lizibilitatea_codului": 0,
        }
        feedback = ["Feedback not available."]

    return grade, feedback, grades
    

@login_required
def problem_detail(request, problem_id):
    problem = get_object_or_404(Problem, id=problem_id)
    latest_solution = Solution.objects.filter(problem=problem, student=request.user).order_by('-submitted_at').first()
    if request.method == 'POST':
        form = SolutionForm(request.POST)
        if form.is_valid():
            solution = form.save(commit=False)
            solution.problem = problem
            solution.student = request.user  # Assuming the user is logged in
            
            Badges.check_and_award_centurion_badge(request.user)
            Badges.check_and_award_first_problem_solved_badge(request.user)

            # AI grading
            solution_text = form.cleaned_data['text']
            grade, feedback, grades = grade_solution(problem.text, solution_text)
            solution.grade = grade
            solution.feedback = feedback
            solution.grades = grades
            
            solution.save()
            return redirect(request.path)  # Adjust the redirect as needed
    else:
        form = SolutionForm()
    return render(request, 'problem_generator/problem_detail.html', {'problem': problem, 'form': form, 'latest_solution': latest_solution, 'page_title':"Problema"})

def homework_detail(request, homework_id):
    homework = get_object_or_404(Homework, id=homework_id)
    is_teacher = request.user in homework.course.teachers.all()
    problems = homework.probleme.all()  # Retrieve the associated problems

    context = {
        'homework': homework,
        'is_teacher': is_teacher,
        'problems': problems,  # Pass the problems to the template
    }

    if is_teacher:
        submissions = MCQResult.objects.filter(homework=homework).select_related('student')
        for submission in submissions:
            submission.grade = (submission.correct_answers / submission.total_questions) * 100
        context['submissions'] = submissions
        context['mcq_results'] = submissions  # Ensure mcq_results is passed to the template
    else:
        context['submissions'] = None

    return render(request, 'problem_generator/homework_detail.html', context)
# @login_required
# def view_solutions(request, problem_id):
#     problem = get_object_or_404(Problem, id=problem_id)
#     # Verify the user is a teacher of the course
#     if request.user not in problem.homework.course.teachers.all():
#         return redirect('some_access_denied_page')  # Ensure you handle unauthorized access appropriately

#     solutions = Solution.objects.filter(problem=problem).order_by('-submitted_at')

#     return render(request, 'problem_generator/view_solutions.html', {
#         'problem': problem,
#         'solutions': solutions
#     })



# def submit_test(request, homework_id):
#     if request.method == 'POST':
#         # This is a simplified approach; in reality, you'll need to handle each question submission.
#         # Assuming `submitted_answers` is a dict with problem IDs as keys and chosen options as values.
#         submitted_answers = request.POST.getlist('answers')  # Adjust based on your actual form structure
#         correct_count = 0
#         total_questions = 0

#         for problem_id, chosen_option in submitted_answers.items():
#             problem = get_object_or_404(MultipleChoiceProblem, id=problem_id)
#             if problem.correct_answer == chosen_option:
#                 correct_count += 1
#             total_questions += 1

#         # Calculate score or proceed as needed
#         # Redirect or render a response

#         return redirect('some_result_page')
    


import re

def parse_ai_output(ai_output):
    try:
        # Regular expression to find JSON-like structures
        pattern = re.compile(r'\{.*?\}', re.DOTALL)
        matches = pattern.findall(ai_output)
        
        parsed_questions = []
        for match in matches:
            try:
                question = json.loads(match)
                parsed_questions.append({
                    'question': question.get('Question', ''),
                    'choices': question.get('Choices', []),
                    'correct_answer': question.get('Correct', ''),
                    'code_snippet': question.get('CodeSnippet', '')
                })
            except json.JSONDecodeError as e:
                print(f"JSON decoding error for match: {match}. Error: {e}")
        
        return parsed_questions
    except json.JSONDecodeError as e:
        print(f"JSON decoding error for ai_output: {ai_output}. Error: {e}")
        return []  # Return an empty list if JSON decoding fails




def generate_test(request):
    if request.method == 'POST':
        form = TestCreationForm(request.POST)
        if form.is_valid():
            topics = form.cleaned_data.get('topics')
            difficulty = form.cleaned_data.get('difficulty')
            nOq = form.cleaned_data.get('number_of_problems')


            system_prompt = "You are a creative, romanian speaking, informatics problem generator that creates multiple problems with quiz-like answers in the following format: Question 1: What is X? </s>A. Option1 </s>B. Option2 </s>C. Option3 </s>Correct: A. You task is to generate a specified number of such problems. The questions can be from simple theory questions to provided code (marked with <code> </code>) with provided input and you will have to tell the correct output."
            
            user_prompt = f"Generate a set of {nOq} quiz subjects with incrementing difficulty based on the topics: {topics}"
            
            openai.api_key = "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"
            client = OpenAI(api_key=openai.api_key)
            response = client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.5,
                    max_tokens=4096,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0,
            )

            test = Homework.objects.create(title=form.cleaned_data['title'])  # Adjust according to your model

            ai_output = response.choices[0].message.content
            parsed_questions = parse_ai_output(ai_output)

            for question in parsed_questions:
                MultipleChoiceProblem.objects.create(
                    homework=test,
                    question=question['question'],
                    choices=question['choices'],
                    correct_answer=question['correct_answer']
                )

            # Here, you handle the creation of the test based on the form data
            # This might include creating a new Test object and associating questions with it
            
            # Redirect to a confirmation page or the test detail page
            return redirect('test_detail', test_id=test.id)
    else:
        form = TestCreationForm()
    return render(request, 'your_template_path/generate_test.html', {'form': form})


def submit_homework(request, homework_id):
    # Ensure this is a POST request
    if request.method == 'POST':
        homework = get_object_or_404(Homework, id=homework_id)
        student = request.user
        mc_problems = homework.multiple_choice_problems.all()
        score = 0
        total = mc_problems.count()

        # Check if the student has already submitted answers
        if not student.is_profesor and MCQResult.objects.filter(student=student, homework=homework).exists():
            messages.error(request, "You have already submitted your answers for this homework.")
            return redirect('course_detail', course_id=homework.course.id)

        # Iterate over each multiple-choice problem to check answers
        for mc_problem in mc_problems:
            # The key in request.POST should match the input's name attribute
            selected_answer = request.POST.get(f'question_{mc_problem.id}', None)
            print(f"Question ID: {mc_problem.id}")
            print(f"Selected Answer: {selected_answer}")
            print(f"Correct Answer: {mc_problem.correct_answer}")

            # Check if the selected answer is correct
            if selected_answer and selected_answer == mc_problem.correct_answer:
                score += 1
            print(f"Current Score: {score}")

        # Create or update the MCQResult for the student and this homework
        MCQResult.objects.update_or_create(
            student=student,
            homework=homework,
            defaults={'correct_answers': score, 'total_questions': total}
        )

        # Redirect or inform the student based on their performance
        messages.success(request, f"You scored {score}/{total} correct answers.")
        return redirect('course_detail', course_id=homework.course.id)
    else:
        # If it's not a POST request, redirect to the homework detail page or some other appropriate page
        return redirect('homework_detail_view', homework_id=homework_id)
    
def landingPage(request):
    return render(request, 'problem_generator/landingPage.html')


@login_required
def profile(request):
    received_requests = Friendship.objects.filter(receiver=request.user, accepted=False)
    sent_requests = Friendship.objects.filter(sender=request.user, accepted=False)
    friendships = Friendship.objects.filter(
        models.Q(sender=request.user) | models.Q(receiver=request.user),
        accepted=True
    )
    friends = [friendship.receiver if friendship.sender == request.user else friendship.sender for friendship in friendships]
    
    # Fetch solutions for the logged-in user
    solutions = Solution.objects.filter(student=request.user).order_by('submitted_at')

    # Prepare data for the chart
    if solutions:
        df = pd.DataFrame(list(solutions.values('submitted_at', 'grade')))
        df['submitted_at'] = pd.to_datetime(df['submitted_at'])
        df.set_index('submitted_at', inplace=True)

        plt.figure(figsize=(10, 5))
        plt.plot(df.index, df['grade'], marker='o')
        plt.title('User Grades Over Time')
        plt.xlabel('Date')
        plt.ylabel('Grade')
        plt.grid(True)

        # Save the plot to a BytesIO object
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()

        chart_url = f"data:image/png;base64,{image_base64}"
    else:
        chart_url = None
    
    context = {
        'user': request.user,
        'received_requests': received_requests,
        'sent_requests': sent_requests,
        'friends': friends,
        'chart_url': chart_url,
    }
    
    return render(request, 'problem_generator/profile.html', context)

@login_required
def chat_detail(request, username):
    return render(request, 'problem_generator/chat.html', {'username': username})

@login_required
def get_past_messages(request, friend_username):
    user = request.user
    friend = User.objects.get(username=friend_username)
    
    messages = Message.objects.filter(
        (Q(sender=user) & Q(receiver=friend)) |
        (Q(sender=friend) & Q(receiver=user))
    ).order_by('timestamp')

    messages_data = [
        {'sender': message.sender.username, 'content': message.content, 'timestamp': message.timestamp}
        for message in messages
    ]
    
    return JsonResponse(messages_data, safe=False)




@login_required
def ai_tutor(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user_query = data.get('query')
        
        # Call your AI model here (using Groq)
        # client = Groq(api_key="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")
        client = OpenAI(api_key="sk-proj-eDURNSRDWPQ6QgWjeRDvT3BlbkFJJkgwiJ5eBx2xMeBfo6qZ")
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a romanian/english helpful informatics tutor. Your task is to provide easy to understand answers about programming in general. Anything outside of the programming field will not be answered to. Also, you will not give solving solutions to informatics problems if provided. The answer must be completly plain text and new lines marked with '\n'"},
                {"role": "user", "content": user_query}
            ],
            model="gpt-4o-mini",
        )
        ai_response = response.choices[0].message.content if response.choices else "I couldn't find an answer. Please try again."
        
        return JsonResponse({'response': ai_response})

    return JsonResponse({'error': 'Invalid request method'}, status=400)




@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            user.social_links = form.cleaned_data['social_links']
            user.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Error updating profile. Please check the form and try again.')
            print(form.errors)  # Debugging: print form errors to the console
    else:
        user = request.user
        initial_data = {
            'link1': user.social_links.get('link1'),
            'link2': user.social_links.get('link2'),
            'link3': user.social_links.get('link3'),
            'link4': user.social_links.get('link4'),
            'link5': user.social_links.get('link5'),
        }
        form = UserProfileForm(instance=user, initial=initial_data)
    return render(request, 'problem_generator/edit_profile.html', {'form': form})



@login_required
def leaderboard(request):
    # Calculate total problems solved and average score for each user
    leaderboard_data = (
        User.objects.annotate(
            total_solved=Count('solutions', filter=models.Q(solutions__grade__gte=75)),
            total_score=Sum('solutions__grade', filter=models.Q(solutions__grade__gte=75)),
            avg_score=Avg('solutions__grade', filter=models.Q(solutions__grade__gte=75))
        )
        .order_by('-total_score', '-avg_score', '-total_solved')[:25]
    )

    return render(request, 'problem_generator/leaderboard.html', {'leaderboard_data': leaderboard_data})


@login_required
def view_profile(request, username):
    user = get_object_or_404(User, username=username)
    received_requests = user.received_friend_requests.filter(accepted=False)
    sent_requests = user.sent_friend_requests.filter(accepted=False)
    friendships = user.sent_friend_requests.filter(accepted=True) | user.received_friend_requests.filter(accepted=True)
    friends = [friendship.receiver if friendship.sender == user else friendship.sender for friendship in friendships]

    context = {
        'user_profile': user,
        'received_requests': received_requests,
        'sent_requests': sent_requests,
        'friends': friends,
    }
    return render(request, 'problem_generator/view_profile.html', context)


@login_required
def get_notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')
    notifications_data = [
        {
            'id': notification.id,
            'message': {
                'sender': {
                    'username': notification.message.sender.username
                },
                'content': notification.message.content
            },
            'is_read': notification.is_read,
            'timestamp': notification.timestamp
        }
        for notification in notifications
    ]
    return JsonResponse(notifications_data, safe=False)


@require_POST
@login_required
def mark_notification_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'status': 'success'})


@method_decorator(login_required, name='dispatch')
class CreateNotificationView(View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        receiver_username = data.get('receiver')
        message_content = data.get('message')
        
        receiver = get_object_or_404(User, username=receiver_username)
        sender = request.user
        
        message = Message.objects.create(sender=sender, receiver=receiver, content=message_content)
        
        Notification.objects.create(user=receiver, message=message)
        
        return JsonResponse({'status': 'success'})
    


logger = logging.getLogger(__name__)

@csrf_exempt
def chat_generate_problem(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = json.loads(request.body)
        step = data.get('step')
        user_message = data.get('message')
        theme = data.get('theme')
        difficulty = data.get('difficulty')

        try:
            if step == 1:
                question = "Bun. Acum alege o dificultate: usor, mediu, greu"
                choices = [('easy', 'Usor'), ('medium', 'Mediu'), ('hard', 'Greu')]
                return JsonResponse({'question': question, 'choices': choices})
            elif step == 2:
                question = f"Se genereaza o problema de dificultate {difficulty} cu tema {theme}. Te rog sa astepti..."
                choices = []

                # Generate the problem here
                system_prompt = '''You are a romanian speaking creative informatics problem generator for highschool students.
                                  You have to generate problems of different difficulties, offering a friendly story like problem statement, an input sample and an output sample.
                                  You will output the problems in the following JSON format:
                                  {
                                    "Titlu": "titlu",
                                    "Enunt": "enunt",
                                    "Cerinta": "cerinta",
                                    "Input": "input",
                                    "Output": "output",
                                    "Restrictii": "restrictii",
                                    "Exemplu": "exemplu",
                                    "Explicatie_exemplu": "explicatie"
                                  }
                                  You will output only the JSON, nothing more or less.
                                  You don't have to offer explanations about the way the problem can be solved. If provided a solution, you can give a grade from 0 to 100.
                                  The grading system is based on 3 benchmarks: correctness of the syntax, efficiency of the algorithm used, and code readability.
                                  After grading, explain what can be improved but don't provide a correct solution.
                                  You have to output the problems only in Romanian.'''

                user_prompt = f"Please generate a {difficulty} difficulty problem related to {theme}."

                client = Groq(api_key="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")
                response = client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt
                        },
                        {
                            "role": "user",
                            "content": user_prompt,
                        }
                    ],
                    model="llama3-70b-8192",
                )

                generated_problem = response.choices[0].message.content if response.choices else "I couldn't generate a problem. Please try again."

                problem = Problem.objects.create(
                    text=generated_problem,
                    # Set index or homework if needed
                )

                return JsonResponse({'question': 'Problema generata cu succes!', 'choices': [], 'problem_id': problem.id})

        except Exception as e:
            logger.error("Error in chat_generate_problem: %s", str(e), exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)

    return render(request, 'problem_generator/chat_generate_problem.html', {'form': SingleDifficultyProblemGenerationForm()})
