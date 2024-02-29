import re
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.db import models 
from django.contrib import messages
from django.utils import timezone
import openai
import random
from openai import OpenAI

from accounts.models import Course, Friendship, Homework, MCQResult, MultipleChoiceProblem, Problem, Solution, User
from .forms import CourseForm, HomeworkCreationForm, ProblemGenerationForm, SingleDifficultyProblemGenerationForm, SolutionForm, TestCreationForm

# Create your views here.
def generate_problem(request):
    if request.method == 'POST':
        form = SingleDifficultyProblemGenerationForm(request.POST)
        if form.is_valid():
            print("E VALID")
            theme = dict(form.fields['theme'].choices)[form.cleaned_data['theme']]
            difficulty = form.cleaned_data['difficulty']
            
            system_prompt = "You are a romanian speaking creative informatics problem generator for highschool students. You have to generate problems of different difficulties, offering a friendly problem statement, an input sample and an output sample. You will output the problems in the following format: Titlu: titlu</s> Enunt: enunt</s> Cerinta: cerinta</s> Input: input</s> Output: output:</s> Restrictii: restrictii</s> Exemplu: exemplu</s> Explicatie exemplu: explicatie</s>. You don't have to offer explanations about the way the problem can be solved. If provided a solution, you can give a grade from 0 to 100. The grading system is based on 3 benchmarks. Corectness of the syntax, efficiency of the algorithm used and the code readability. After grading, explain what can be improved but don't provide a correct solution. You have to output the problems in romanian."
            
            user_prompt = f"Please generate a {difficulty} difficulty problem related to {theme}."
            
            openai.api_key = settings.OPENAI_API_KEY
            client = OpenAI()
            response = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.5,
                max_tokens=1024,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
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


def search_users(request):
    query = request.GET.get('query', '')
    users = User.objects.exclude(id=request.user.id)
    return render(request, 'problem_generator/search_users.html', {'users': users})


@login_required
def send_friend_request(request, user_id):
    receiver = User.objects.get(id=user_id)
    Friendship.objects.create(sender=request.user, receiver=receiver)
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
    return redirect('friend_requests')

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

    return render(request, 'problem_generator/my_courses.html', {'courses': courses_taught, 'attending_courses': attending_courses, "profesor": profesor})


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
            selected_themes = form.cleaned_data['themes']  # This will be a list of selected theme keys
            deadline = form.cleaned_data['deadline']  # Make sure to add a DateTimeField in your form for the deadline


            system_prompt = "You are a romanian speaking creative informatics problem generator for highschool students. You have to generate problems of different difficulties, offering a friendly problem statement, an input sample and an output sample. You will output the problems in the following format: Titlu: titlu</s> Enunt: enunt</s> Cerinta: cerinta</s> Input: input</s> Output: output:</s> Restrictii: restrictii</s> Exemplu: exemplu</s> Explicatie exemplu: explicatie</s>. You don't have to offer explanations about the way the problem can be solved. If provided a solution, you can give a grade from 0 to 100. The grading system is based on 3 benchmarks. Corectness of the syntax, efficiency of the algorithm used and the code readability. After grading, explain what can be improved but don't provide a correct solution. You have to output the problems in romanian."
            
            user_prompt = f"Please generate a list of {num_problems} informatics problems with difficulty grades from {min_difficulty} to {max_difficulty}  related to the following themes: {selected_themes}. Separate each problem with the symbol </endprob> and separate the problem statement from the input and output using the </s> symbol."
            
            openai.api_key = settings.OPENAI_API_KEY
            client = OpenAI()
            response = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.5,
                max_tokens=2048,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
            )
            
            generated_problems = response.choices[0].message.content if response.choices else "I couldn't generate a problem. Please try again."

            problem_texts = generated_problems.split('</endprob>')
            # Save the generated homework
            homework = Homework.objects.create(
                course=course,
                problems='',
                deadline=deadline,
                grading_criteria={  # Example criteria, adjust as needed
                    'correctness': 50,
                    'efficiency': 30,
                    'readability': 20,
                }
            )

            for problem_text in problem_texts:
                if problem_text.strip():  # Check if the problem text is not just whitespace
                    Problem.objects.create(
                        homework=homework,
                        text=problem_text.strip(),
                        # Optionally set 'index' or other fields if needed
                    )

            return redirect('/problems/course_detail', course_id=course.id)
        elif 'submit_test' in request.POST and test_form.is_valid():
            topics = test_form.cleaned_data.get('topics')
            print("\n\n\n\n", topics, "\n\n\n\n")
            difficulty = test_form.cleaned_data.get('difficulty')
            nOq = test_form.cleaned_data.get('number_of_problems')
            print("\n\n\n\n\n\n", nOq, "\n\n\n\n")
            deadline = test_form.cleaned_data['deadline']

            system_prompt = "You are a creative, romanian speaking, informatics problem generator that creates multiple problems with quiz-like answers in the following format: Question 1: What is X? </s>A. Option1 </s>B. Option2 </s>C. Option3 </s>**Correct: A. You task is to generate a specified number of such problems. The questions can be from simple theory questions to provided code separated from the question by ```(before and after it) with provided input and you will have to tell the correct output. Every qustion has to start with '#### Question'. The output has to be in romanian."
            
            user_prompt = f"Generate a set of {nOq} quiz subjects with incrementing difficulty based on the topics: {topics}"
            
            openai.api_key = settings.OPENAI_API_KEY
            client = OpenAI()
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

            test = Homework.objects.create(
                    title=test_form.cleaned_data['title'],
                    deadline=deadline,
                    course=course,

                )  # Adjust according to your model

            ai_output = response.choices[0].message.content
            print("AI Output:", ai_output)
            parsed_questions = parse_ai_output(ai_output)

            for question in parsed_questions:
                MultipleChoiceProblem.objects.create(
                    homework=test,
                    question=question['question'] + "\n\n" +question['code_snippet'] + "\n\n",
                    choices=question['choices'],
                    correct_answer=question['correct_answer'],
                    
                )

            # Here, you handle the creation of the test based on the form data
            # This might include creating a new Test object and associating questions with it
            
            # Redirect to a confirmation page or the test detail page

            return redirect('/problems/course_detail', course_id=course.id)
        else:
            print(test_form.errors)
    else:
        form = HomeworkCreationForm()
        test_form = TestCreationForm()

    return render(request, 'problem_generator/generate_homework.html', {'form': form, 'course': course, 'test_form': test_form,})


def grade_solution(problem_text ,solution_text):
    
    system_prompt = "You are a romanian speaking creative informatics problem generator for highschool students. You have to generate problems of different difficulties, offering a friendly problem statement, an input sample and an output sample. You don't have to offer explanations about the way the problem can be solved. If provided a solution, you can give a grade from 0 to 100. The grading system is based on 3 benchmarks. Corectness of the syntax, efficiency of the algorithm used and the code readability. After grading, explain what can be improved but don't provide a correct solution. The format for the improvement tips is the following: 'Sfaturi: 1.Sfatul numarul 1</s> 2. Sfatul numarul 2</s>......'. You have to output the problems in romanian."
            
    user_prompt = f"Correct the given informatics problem solution based on the 3 benchmarks. The problem statement is: {problem_text}. After each grade, write the </s> symbol. The format for the score output is: Corectitudinea sintaxei: score</s> Eficiența algoritmului: score</s> Lizibilitatea codului: score</s>. Give tips for improvement in romanian after grading, without providing the corrected code. If the provided solution is for the wrong problem, all the grades are automaticly 0. The solution: {solution_text}"
            
    openai.api_key = settings.OPENAI_API_KEY
    client = OpenAI()
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
    pattern = r"Corectitudinea sintaxei: (\d+)</s> Eficiența algoritmului: (\d+)</s> Lizibilitatea codului: (\d+)"
    matches = re.search(pattern, response.choices[0].message.content if response.choices else "")

    if matches:
        # Extracting grades
        grades = [int(matches.group(1)), int(matches.group(2)), int(matches.group(3))]
        
        # Calculate average grade
        grade = sum(grades) / len(grades)

        # Extract feedback after the grades
        feedback_start = matches.end()
        feedback = response.choices[0].message.content[feedback_start:].strip() if len(response.choices[0].message.content) > feedback_start else "Feedback not available."
    else:
        grade = 0  # Or some form of handling if grades cannot be extracted
    # feedback = response.choices[0].message.content if response.choices else "I couldn't correct the problem. Please try again."
    return grade, feedback

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
            
            # AI grading
            solution_text = form.cleaned_data['text']
            grade, feedback = grade_solution(problem.text, solution_text)
            solution.grade = grade
            solution.feedback = feedback
            
            solution.save()
            return redirect(request.path)  # Adjust the redirect as needed
    else:
        form = SolutionForm()
    return render(request, 'problem_generator/problem_detail.html', {'problem': problem, 'form': form, 'latest_solution': latest_solution,})

def homework_detail(request, homework_id):
    homework = get_object_or_404(Homework, id=homework_id)
    is_teacher = request.user in homework.course.teachers.all()  # Check if the user is a teacher of the course
    context = {
        'homework': homework,
        'is_teacher': is_teacher,
        # Additional context data...
    }

    if is_teacher:
        submissions = MCQResult.objects.filter(homework=homework).select_related('student')
        for submission in submissions:
            # Assuming the grade is already calculated and saved in MCQResult
            # If you need to calculate it here instead, you can do so based on submission details
            # For example, if grades are not pre-calculated:
            submission.grade = (submission.correct_answers / submission.total_questions) * 100
            context['submissions'] = submissions
            pass  # Remove this pass statement once you add any necessary logic
    else:
        submissions = None  # Students do not need to see all submissions, only their own
    

    if request.user.is_profesor:
        mcq_results = MCQResult.objects.filter(homework=homework)
        context['mcq_results'] = mcq_results

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
    

def parse_ai_output(ai_output):
    # Split the output into questions
    questions_parts = ai_output.split('#### ')[1:]  # Each question starts with '#### '
    parsed_questions = []

    for part in questions_parts:
        # Initialize a dictionary to hold the parts of each question
        question_data = {'question': '', 'choices': [], 'correct_answer': '', 'code_snippet': ''}
        lines = part.split('\n')
        
        # Extract the question text and detect if there's a code block
        in_code_block = False
        code_snippet = []
        for line in lines:
            if line.strip().startswith('```'):  # Detect code block start or end
                in_code_block = not in_code_block
                continue  # Skip the code block markers themselves
            
            if in_code_block:
                code_snippet.append(line)
            elif line.startswith('A.') or line.startswith('B.') or line.startswith('C.'):
                question_data['choices'].append(line)
            elif line.startswith('**Correct:'):
                correct_answer = line.split('**')[1].strip()
                question_data['correct_answer'] = correct_answer.split('.')[0]  # Extract just the letter
            else:
                # Append line to question text if not in code block and not a choice
                if line.strip() and not in_code_block:
                    question_data['question'] += line + '\n'
        
        # Join the code snippet lines back together, if any
        if code_snippet:
            question_data['code_snippet'] = '\n'.join(code_snippet)
        
        parsed_questions.append(question_data)

    return parsed_questions



def generate_test(request):
    if request.method == 'POST':
        form = TestCreationForm(request.POST)
        if form.is_valid():
            topics = form.cleaned_data.get('topics')
            difficulty = form.cleaned_data.get('difficulty')
            nOq = form.cleaned_data.get('number_of_problems')


            system_prompt = "You are a creative, romanian speaking, informatics problem generator that creates multiple problems with quiz-like answers in the following format: Question 1: What is X? </s>A. Option1 </s>B. Option2 </s>C. Option3 </s>Correct: A. You task is to generate a specified number of such problems. The questions can be from simple theory questions to provided code (marked with <code> </code>) with provided input and you will have to tell the correct output."
            
            user_prompt = f"Generate a set of {nOq} quiz subjects with incrementing difficulty based on the topics: {topics}"
            
            openai.api_key = settings.OPENAI_API_KEY
            client = OpenAI()
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
        # Prevents re-submission if not a teacher
        if not student.is_profesor and MCQResult.objects.filter(student=student, homework=homework).exists():
            messages.error(request, "You have already submitted your answers for this homework.")
            return redirect('course_detail', course_id=homework.course.id)

        # Iterate over each multiple-choice problem to check answers
        for mc_problem in mc_problems:
            # The key in request.POST should match the input's name attribute
            selected_answer = "Correct: " + request.POST.get(f'question_{mc_problem.id}', None)

            # Check if the selected answer is correct
            if selected_answer and selected_answer == mc_problem.correct_answer:
                score += 1

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