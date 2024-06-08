from django.db import models
from django.contrib.auth.models import User
from openai import OpenAI
from .rag import rag
# Create your models here.

class Convo(models.Model):
    thread_id = models.CharField(max_length=100,blank=True,null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100,default= 'New Chat')
    archived =  models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']


def create_gptkadi(user_query):
    r = rag()

    client= OpenAI()
    thread= client.beta.threads.create()
    rag_context= r.rag_context(user_query) #this is a list

    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_query
        )

    for context in rag_context:
        rag_message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="assistant",
            content=context.page_content, #must be a string
            metadata=context.metadata)

    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id='asst_3V31eiuHdV5EIrYTpjQ8etZn'
    )

    while run.status != "completed":
        keep_retrieving_run = client.beta.threads.runs.retrieve(
        thread_id=thread.id,
        run_id=run.id
    )
        print(f"Run status: {keep_retrieving_run.status}")

        if keep_retrieving_run.status == "completed":
            break


    # Retrieve messages added by the Assistant to the thread
    all_messages = client.beta.threads.messages.list(
        thread_id=thread.id
    )

    # Return the content of the first message added by the Assistant
    assistant_response= all_messages.data[0].content[0]
    return (assistant_response)



class Prompt(models.Model):
    convo= models.ForeignKey(Convo,on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    
    text_query = models.TextField(max_length=10_000)
    
    response_text=  models.TextField(max_length=10_000,blank=True)  #GPT generated response

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        response_data= create_gptkadi(self.text_query).text.value
        self.response_text= response_data
        super().save(*args, **kwargs)


    def __str__(self):
        return str(self.convo)

