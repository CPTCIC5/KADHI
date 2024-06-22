from django.contrib import admin
from .models import Note,BlockNote,Convo,Prompt,PromptFeedback
# Register your models here.
admin.site.register(Note)
admin.site.register(BlockNote)
admin.site.register(Convo)
admin.site.register(Prompt)
admin.site.register(PromptFeedback)
