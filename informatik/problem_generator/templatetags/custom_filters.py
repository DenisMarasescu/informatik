import re
from django import template

register = template.Library()

@register.filter(name='split_problems')
def split_problems(value, key='</endprob>'):
    """Split the problems string by a key and return a list."""
    return value.split(key) if value else []


# @register.simple_tag
# def parse_problem_text(problem_text):
#     sections = {
#         'Titlu': '',
#         'Enunt': '',
#         'Cerinta': '',
#         'Input': '',
#         'Output': '',
#         'Restrictii': '',
#         'Exemplu': '',
#     }
#     # Regular expression patterns for each section
#     patterns = {
#         'Titlu': r'Titlu: (.+?) Enunt:',
#         'Enunt': r'Enunt: (.+?) Cerinta:',
#         'Cerinta': r'Cerinta: (.+?) Input:',
#         'Input': r'Input: (.+?) Output:',
#         'Output': r'Output: (.+?) Restrictii:',
#         'Restrictii': r'Restrictii: (.+?) Exemplu:',
#         'Exemplu': r'Exemplu: (.+)',
#     }

#     for key, pattern in patterns.items():
#         match = re.search(pattern, problem_text, re.DOTALL)
#         if match:
#             sections[key] = match.group(1).strip()

#     return sections 


@register.simple_tag
def parse_problem_text(problem_text):
    # Assuming each section is separated by a newline and the title
    # print(problem_text)
    sections = re.split(r'(Titlu:|Enunt:|Cerinta:|Input:|Output:|Restrictii:|Exemplu:|Explicatie exemplu:)', problem_text)
    print(sections)
    sections_dict = {}
    for i in range(1, len(sections), 2):
        # Adjusting the keys in the custom template tag
        key = sections[i].replace(':', '').replace(' ', '_').strip()  # Also replace spaces with underscores
        sections_dict[key] = sections[i + 1].strip()
    return sections_dict


@register.filter(name='split_tips')
def split_tips(value, separator='</s>'):
    # Remove the leading "Sfaturi" if it exists
    value = value.replace('Sfaturi:', '', 1).strip()

    # Split the string into a list where each tip is an element
    tips = re.split(separator, value)
    # Filter out empty strings in case there are multiple separators in sequence
    tips = [tip.strip() for tip in tips if tip.strip()]
    return tips