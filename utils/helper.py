import json
import re

#* cleans and parses the response to json, or returns plain text if not JSON

def clean_markdown(text):
    # Remove bold (**text**) and italics (*text*)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Remove bold
    text = re.sub(r'\*([^*]+)\*', r'\1', text)        # Remove italics
    # Remove leading * or - or whitespace at line start
    text = re.sub(r'^[\*\-]\s*', '', text, flags=re.MULTILINE)
    # Remove extra backticks
    text = text.replace('`', '')
    # Optionally, remove extra blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def clean_content(response):
    content = response.strip('```').replace('json', '').replace('`','')
    try:
        return json.loads(content)
    except Exception:
        return clean_markdown(content.strip())

def parse_mcq_text(mcq_text):
    """
    Parses AI-generated MCQ text into a list of question dicts.
    Expects format similar to:
    1. Question text\n    a) Option1\n    b) Option2\n    ...\n    Answer Key:\n    1. b\n    2. c\n    ...
    """
    import re
    questions = []
    # Split off the answer key
    parts = re.split(r'Answer Key:', mcq_text, flags=re.IGNORECASE)
    if len(parts) < 2:
        return []  # Can't parse
    questions_block, answer_block = parts[0], parts[1]

    # Parse answers
    answer_map = {}
    # Accepts formats like: 1. B, 1. (B), 1. B), 1) B, 1) (B), etc.
    answer_pattern = re.compile(r"""
        (\d+)            # Question number
        [\.)]            # Dot or parenthesis after number
        \s*              # Optional whitespace
        \(?([a-dA-D])\)? # Optional parenthesis around answer letter
        \s*[\)]?        # Optional whitespace and closing parenthesis
    """, re.VERBOSE)
    for line in answer_block.strip().splitlines():
        m = answer_pattern.match(line.strip())
        if m:
            qnum, ans = m.groups()
            answer_map[int(qnum)] = ans.lower()

    # Parse questions
    q_pattern = re.compile(r'\n?(\d+)\.\s*(.*?)\n((?:\s*[a-dA-D]\)[^\n]*\n?)+)', re.DOTALL)
    opt_pattern = re.compile(r'([a-dA-D])\)\s*([^\n]+)')
    for qmatch in q_pattern.finditer(questions_block):
        qnum = int(qmatch.group(1))
        qtext = qmatch.group(2).strip()
        opts_block = qmatch.group(3)
        options = []
        correct = None
        for om in opt_pattern.finditer(opts_block):
            label, opt = om.groups()
            options.append(opt.strip())
            if answer_map.get(qnum) == label.lower():
                correct = opt.strip()
        questions.append({
            'id': qnum,
            'type': 'Multiple Choice',
            'question': qtext,
            'options': options,
            'correct': correct
        })
    return questions

def parse_sqs_text(sqs_text):
    """
    Parses AI-generated SQS (short answer) text into a list of question dicts.
    Expects format similar to:
    1. Question text
    2. Question text
    ...
    """
    import re
    questions = []
    # Remove any intro text before the first question
    sqs_text = re.sub(r'^.*?\n?1\.\s+', '1. ', sqs_text, flags=re.DOTALL)
    q_pattern = re.compile(r'\n?(\d+)\.\s*(.*?)(?=\n\d+\.|$)', re.DOTALL)
    for qmatch in q_pattern.finditer(sqs_text):
        qnum = int(qmatch.group(1))
        qtext = qmatch.group(2).strip()
        questions.append({
            'id': qnum,
            'type': 'Short Answer',
            'question': qtext
        })
    return questions

def parse_lqs_text(lqs_text):
    """
    Parses AI-generated LQS (long answer) text into a list of question dicts.
    Expects format similar to:
    1. Question text
    2. Question text
    ...
    """
    import re
    questions = []
    # Remove any intro text before the first question
    lqs_text = re.sub(r'^.*?\n?1\.\s+', '1. ', lqs_text, flags=re.DOTALL)
    q_pattern = re.compile(r'\n?(\d+)\.\s*(.*?)(?=\n\d+\.|$)', re.DOTALL)
    for qmatch in q_pattern.finditer(lqs_text):
        qnum = int(qmatch.group(1))
        qtext = qmatch.group(2).strip()
        questions.append({
            'id': qnum,
            'type': 'Long Questions',
            'question': qtext
        })
    return questions

def parse_blanks_text(blanks_text):
    """
    Parses AI-generated Fill in the Blanks text into a list of question dicts.
    Expects format similar to:
    1. Question text with blank(s)
    ...
    Answer Key:
    answer1
    answer2
    ...
    """
    import re
    questions = []
    # Split off the answer key
    parts = re.split(r'Answer Key:', blanks_text, flags=re.IGNORECASE)
    if len(parts) < 2:
        # fallback: just parse questions, no answers
        blanks_text = re.sub(r'^.*?\n?1\.\s+', '1. ', blanks_text, flags=re.DOTALL)
        q_pattern = re.compile(r'\n?(\d+)\.\s*(.*?)(?=\n\d+\.|$)', re.DOTALL)
        for qmatch in q_pattern.finditer(blanks_text):
            qnum = int(qmatch.group(1))
            qtext = qmatch.group(2).strip()
            questions.append({
                'id': qnum,
                'type': 'Fill in the Blanks',
                'question': qtext,
                'answer': ''
            })
        return questions
    questions_block, answer_block = parts[0], parts[1]
    # Parse questions
    questions_block = re.sub(r'^.*?\n?1\.\s+', '1. ', questions_block, flags=re.DOTALL)
    q_pattern = re.compile(r'\n?(\d+)\.\s*(.*?)(?=\n\d+\.|$)', re.DOTALL)
    qlist = []
    for qmatch in q_pattern.finditer(questions_block):
        qnum = int(qmatch.group(1))
        qtext = qmatch.group(2).strip()
        qlist.append(qtext)
    # Parse answers (one per line, ignore empty lines)
    answers = [a.strip() for a in answer_block.strip().splitlines() if a.strip()]
    # Pair questions and answers
    for idx, qtext in enumerate(qlist):
        answer = answers[idx] if idx < len(answers) else ''
        questions.append({
            'id': idx+1,
            'type': 'Fill in the Blanks',
            'question': qtext,
            'answer': answer
        })
    return questions

def parse_true_false_text(tf_text):
    """
    Parses AI-generated True/False text into a list of question dicts.
    Handles both in-line answers and an 'Answer Key' section at the end.
    """
    import re
    questions = []
    # Check for Answer Key section
    parts = re.split(r'Answer Key:', tf_text, flags=re.IGNORECASE)
    if len(parts) > 1:
        questions_block, answer_block = parts[0], parts[1]
        # Parse questions
        questions_block = re.sub(r'^.*?\n?1\.\s+', '1. ', questions_block, flags=re.DOTALL)
        q_pattern = re.compile(r'\n?(\d+)\.\s*True or False:\s*(.*?)(?=\n\d+\.|$)', re.DOTALL | re.IGNORECASE)
        qlist = []
        for qmatch in q_pattern.finditer(questions_block):
            qnum = int(qmatch.group(1))
            qtext = qmatch.group(2).strip()
            qlist.append(qtext)
        # Parse answers (one per line, ignore empty lines, remove numbering and parens)
        answers = []
        for a in answer_block.strip().splitlines():
            a = a.strip()
            m = re.match(r'(\d+\.|\(|\))*\s*(True|False)', a, re.IGNORECASE)
            if m:
                answers.append(m.group(2).capitalize())
            elif a:
                answers.append(a.capitalize())
        # Pair questions and answers
        for idx, qtext in enumerate(qlist):
            answer = answers[idx] if idx < len(answers) else ''
            questions.append({
                'id': idx+1,
                'type': 'True/False',
                'question': qtext,
                'answer': answer
            })
        return questions
    # Fallback: in-line answers
    tf_text = re.sub(r'^.*?\n?1\.\s+', '1. ', tf_text, flags=re.DOTALL)
    q_pattern = re.compile(r'\n?(\d+)\.\s*True or False:\s*(.*?)(?:\((True|False)\)[^\)]*\))?(?=\n\d+\.|$)', re.DOTALL | re.IGNORECASE)
    for qmatch in q_pattern.finditer(tf_text):
        qnum = int(qmatch.group(1))
        qtext = qmatch.group(2).strip()
        # Try to extract the first (True/False) after the question
        answer = None
        m = re.search(r'\((True|False)\)', qtext, re.IGNORECASE)
        if m:
            answer = m.group(1).capitalize()
            qtext = re.sub(r'\((True|False)\)', '', qtext, count=1, flags=re.IGNORECASE).strip()
        elif qmatch.group(3):
            answer = qmatch.group(3).capitalize()
        else:
            # fallback: try to extract answer from end of question
            m2 = re.search(r'\((True|False)\)', tf_text[qmatch.start():qmatch.end()], re.IGNORECASE)
            if m2:
                answer = m2.group(1).capitalize()
            else:
                answer = ''
        questions.append({
            'id': qnum,
            'type': 'True/False',
            'question': qtext,
            'answer': answer
        })
    return questions

