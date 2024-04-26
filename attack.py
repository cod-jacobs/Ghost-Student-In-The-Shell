import os
import re
import click
import pandas as pd
from openai import OpenAI
from canvasapi import Canvas
from dotenv import load_dotenv

load_dotenv()

def discussion_ai(OPENAI_API_KEY, user, course, topic_content):
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

    images = re.findall(r"(?<=img src=\").*?(?=\")", topic_content)

    content = [
        {
            "type": "text", 
            "text": "Respond with the context that you are a community college student.\n\n" +
                    f"Additional information: my name is '{user.name}', course title is '{course.name}'\n\n" +
                    f"Question data: {topic_content}\n\n" + 
                    "Interpret the image(s) that came with the post as well."
        },
    ]
    for image in images:
        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": image,
                },
            },
        )

    response = openai_client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {
            "role": "user",
            "content": content
            }
        ]
    )

    return response

# Processing for each student
def processing(CANVAS_API_URL, CANVAS_API_KEY, OPENAI_API_KEY, df):
    """
    relies on .env file with
        CANVAS_API_URL
        CANVAS_API_KEY
        OPENAI_API_KEY
    df is a CSV with columns:
        user,course,assignmentid,assignmenttype
    """
    canvas = Canvas(CANVAS_API_URL, CANVAS_API_KEY)

    user = canvas.get_current_user()

    # Assignment processing for all courses
    for course in canvas.get_courses():
        for assignment in course.get_assignments():
            if assignment.id not in df[df.user==user.id].assignmentid:
                if hasattr(assignment, "discussion_topic"):
                    assignment_type = "discussion"
                    discussion_topic = course.get_discussion_topic(assignment.discussion_topic["id"])
                    topic = discussion_topic.message
                    response = discussion_ai(OPENAI_API_KEY, user, course, topic)
                    discussion_topic.post_entry(message=response.choices[0])
                elif hasattr(assignment, "quiz_id"):
                    assignment_type="quiz"
                else:
                    assignment_type=None
            
                record = pd.DataFrame(
                    {
                        'user': [user.id],
                        'course': [course.id],
                        'assignmentid': [assignment.id],
                        'assignmenttype': [assignment_type],
                    }
                )

                df = pd.concat([df, record], ignore_index=True)
    
    return df
            
# requires argument as follows:
# python attack --user_data=user_data.csv
# where user_data.csv contains columns
#   user,course,assignmentid,assignmenttype
@click.command()
@click.option("--user_data", required=True, type=str)
def main(user_data):
    i = 1
    data = pd.read_csv(user_data)
    try:
        while True:
            data = processing(
                os.environ.get("CANVAS_API_URL"),
                os.environ.get(f"CANVAS_API_KEY_{i}"),
                os.environ.get("OPENAI_API_KEY"),
                data
            )
            i+=1
    except:
        pass

    user_data.to_csv(user_data)

if __name__ == "__main__":
    main()
