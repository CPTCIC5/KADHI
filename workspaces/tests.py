from django.db import models
from workspaces.models import WorkSpace
from django.conf import settings
from dotenv import load_dotenv
from openai import OpenAI
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from .rag import RagData
import re
from django.core.files.base import ContentFile
import uuid

from openai.types.beta.threads.text_content_block import TextContentBlock
from openai.types.beta.threads.image_url_content_block import ImageURLContentBlock
from openai.types.beta.threads.image_file_content_block import ImageFileContentBlock
from typing_extensions import override
from openai import AssistantEventHandler

COLOR_CHOICES = (
    ("#90EE90","#90EE90"),
    ("#FFCCCC","#FFCCCC"),
    ("#D3D3D3","#D3D3D3"),
    ("#E6E6FA","#E6E6FA"),
    ("#ADD8E6","#ADD8E6")
)

class Note(models.Model):
    prompt = models.ForeignKey("Prompt",on_delete= models.CASCADE)
    blocknote = models.ForeignKey("BlockNote", on_delete=models.CASCADE)
    note_text= models.CharField(max_length=500)
    created_at= models.DateTimeField(auto_now_add=True)
    color = models.CharField(max_length=30, choices=COLOR_CHOICES, default="#ADD8E6")

    def __str__(self):
        return str(self.blocknote)


class BlockNote(models.Model):
    user= models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    workspace= models.ForeignKey(WorkSpace, on_delete=models.CASCADE, null=True, blank=True)
    title=  models.CharField(max_length=50)
    image= models.CharField(max_length=500,blank=True)
    created_at =  models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    

    
class Folder(models.Model):
    text=models.CharField(max_length=50)
    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text
    

    
class Convo(models.Model):
    #folder= models.ForeignKey(Folder, on_delete=models.PROTECT, blank=True, null=True)
    thread_id = models.CharField(max_length=100,blank=True,null=True)
    workspace = models.ForeignKey(WorkSpace, on_delete=models.CASCADE)
    title = models.CharField(max_length=100,default= 'New Chat')
    archived =  models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']
    
    @property
    def all_notes(self):
        # Fetch all Prompts related to the Convo
        prompts = self.prompt_set.all()
        # Fetch all Notes related to the Prompts
        notes = Note.objects.filter(prompt__in=prompts)
        return notes
    
def generate_insights_with_gpt4(user_query: str, convo: int, namespace, file=None):
    get_convo = get_object_or_404(Convo, id=convo)
    history = get_convo.prompt_set.all()
    all_prompts = history.count()

    

    # Call RagData function with the user query to get RAG context
    rag_context = RagData(user_query, namespace) #we need to pass namespaces into this function how can we do it?
    print('this-is-rag-contextttt',rag_context)



    # Creating a new conversation thread
    if all_prompts >= 1:
        thread = client.beta.threads.retrieve(
            thread_id=get_convo.thread_id
        )

    else:
        thread = client.beta.threads.create()
        get_convo.thread_id = thread.id
        get_convo.save()
        #convo.assistant_id = thread


        

    if file is not None:
        file.open()

        message_file = client.files.create(
          file=file.file.file, purpose="assistants"
        )
        file.close()

        message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_query,
                attachments=[
            {
                "file_id": message_file.id,
                "tools": [{"type": "file_search"}, {"type":"code_interpreter"} ]
            }
        ]
        )
        
    else:
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_query
        )

    # Posting RAG context as a message in the thread for the Assistant
    for context in rag_context:
        rag_message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="assistant",
            content=context.page_content
        )

    # Initiating a run
    '''run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=get_convo.workspace.assistant_id,
        stream=True
    )

    for event in run:
        # wait until the run is completed
        if event.event == "thread.message.completed":
            break'''

    with client.beta.threads.runs.stream(
    thread_id=thread.id,
    assistant_id=get_convo.workspace.assistant_id,
    event_handler=EventHandler(),
    ) as stream:
        stream.until_done()

    # Retrieve messages added by the Assistant to the thread
    all_messages = client.beta.threads.messages.list(
        thread_id=thread.id
    )

    # Return the content of the first message added by the Assistant
    assistant_response= all_messages.data[0].content[0]
    print(assistant_response)

    if type(assistant_response) == TextContentBlock:
        print('block-1')
        return {'text': assistant_response.text.value}
    elif  type(assistant_response) == ImageFileContentBlock:
        print('block-2')
        file_content = client.files.content(assistant_response.image_file.file_id).content
        image_file = ContentFile(file_content, name=f"{uuid.uuid4()}.png")
        if 'text' in assistant_response.type:
            return {'text': assistant_response.text.value, 'image': image_file}
        else:
            return {'image': image_file}
    
    elif  type(assistant_response) == ImageURLContentBlock:
        raise Exception("received ImageURLContentBlock, unable to process this...")
        # print('block-3')
        # print(assistant_response.image_url_content_block)
        # return {'image': assistant_response.image_file.image_url_content_block}
    

class Prompt(models.Model):
    convo= models.ForeignKey(Convo,on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    text_query = models.TextField(max_length=10_000)
    file_query = models.FileField(upload_to='Prompts-File/', blank=True,null=True)
    
    response_text=  models.TextField(max_length=10_000,blank=True, null=True)  #GPT generated response
    response_image = models.ImageField(upload_to='Response-Image/',blank= True, null=True) # gpt generated image
    #blocknote = models.ForeignKey(BlockNote,on_delete=models.CASCADE,blank=True,null=True)
    #blocknote = models.ManyToManyField(BlockNote,null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    chart_data = models.JSONField(blank=True, null=True)
    table_data= models.JSONField(null=True, blank=True)

    def save(self,*args,**kwargs):

        history_counts= self.convo.prompt_set.all().count()
        if history_counts >= 1:
            thread= client.beta.threads.retrieve(
                thread_id=self.convo.thread_id
            )

        else:
            thread = client.beta.threads.create()
            self.convo.thread_id = thread.id
            self.convo.save()


        super().save(*args, **kwargs)

        # error is coming from here
        print('namespace',self.author.workspace_set.first().pinecone_namespace)
        response_data = generate_insights_with_gpt4(user_query=self.text_query, 
                                                    convo=self.convo.id, 
                                                    file=self.file_query or None, 
                                                    namespace=self.author.workspace_set.first().pinecone_namespace
                                                    )
        self.response_text = response_data.get('text', None)
        self.response_image = response_data.get('image', None)

        super().save()



CATEGORY  = (
        (1, "Don't like the style"),
        (2, "Not factually correct"),
        (3, "Being Lazy"),
        (4, "Other")
    )

class PromptFeedback(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    prompt = models.ForeignKey(Prompt,on_delete=models.CASCADE)
    category = models.IntegerField(choices=CATEGORY)
    note = models.TextField()

    def __str__(self):
        return str(self.user)