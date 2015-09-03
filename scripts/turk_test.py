
from boto.mturk.question import QuestionContent,Question,QuestionForm,Overview,AnswerSpecification,SelectionAnswer,FormattedContent,FreeTextAnswer
from boto.mturk.connection import MTurkConnection
import os
ACCESS_ID = os.getenv("AWS_ACCESS_KEY_ID")
SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
HOST = 'mechanicalturk.sandbox.amazonaws.com'

mtc = MTurkConnection(aws_access_key_id=ACCESS_ID,aws_secret_access_key=SECRET_KEY,host=HOST)
title = 'Get continued revenue by running a chrome extension'
description = ('Download and install this chrome extension and run it in the background')
overview = Overview()
overview.append_field('Title',title)
link = "http://169.55.28.212/dist.zip"
overview = Overview()
overview.append_field('Title',title)
overview.append(FormattedContent('<a target="_blank"'+' href=' + link + '>' + 'Download link</a>'))

qc2 = QuestionContent()


qc2.append_field('Title','What user id did the chrome extension give you when you started it?')
fta2 = FreeTextAnswer()
q2 = Question(identifier="comments",content=qc2,answer_spec=AnswerSpecification(fta2))

question_form = QuestionForm()
question_form.append(overview)
question_form.append(q2)
keywords='website'
mtc.create_hit(questions=question_form,max_assignments=1,title=title,description=description,keywords=keywords,duration = 60*5,reward=0.05)