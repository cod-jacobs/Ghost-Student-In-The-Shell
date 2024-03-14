import os
from openai import OpenAI
from canvasapi import Canvas
from canvasapi.course import Course
from canvasapi.assignment import Assignment
from dotenv import load_dotenv

load_dotenv()

# Initialize a new Canvas object
canvas = Canvas(os.environ.get("CANVAS_API_URL"), os.environ.get("CANVAS_API_KEY"))
# Initialize a new OpenAI object
openai_client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

# iterate assignments in shell

for course in canvas.get_courses():
    course: Course
    print(course)
    for assignment in course.get_assignments():
        assignment: Assignment
        print("\t" + str(assignment))
        if hasattr(assignment, "discussion_topic"):
            discussion_topic = course.get_discussion_topic(assignment.discussion_topic["id"])
            # submit prompt to chatgpt
            chat_completion = openai_client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": discussion_topic.message,
                    }
                ],
                model="gpt-3.5-turbo",
            )
            # submit chatgpt response to discussion post
            # todo: find exactly what part of the openai response contains
            #       the discussion response
            discussion_topic.post_entry(message=chat_completion.choices[0])
