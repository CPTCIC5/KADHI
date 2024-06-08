from django.db import models
from django.contrib.auth.models import User
from django.core.validators import validate_image_file_extension
from random import randint
from django.dispatch import receiver
from django.db.models.signals import post_save



# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(
        upload_to="avatars/",
        default="default.jpeg",
        null=True,
        blank=True,
        validators=[validate_image_file_extension],
    )
    phone_number = models.CharField(max_length=15, blank=True, null=True, unique=True)

    referral_code = models.CharField(max_length=6, unique=True, blank=True)
    total_referrals = models.IntegerField(default=0)

    def create_random(self):
        return "".join([str(randint(0, 9)) for _ in range(6)])

    def save(self, *args, **kwargs):
        if not self.referral_code:
            referal_codee = self.create_random()
            # print('ur reff is ',referal_codee)
            if Profile.objects.filter(referral_code=referal_codee).exists():
                while Profile.objects.filter(referral_code=referal_codee).exists():
                    referal_codee = self.create_random()
                    # print("new ref code",referal_codee)
                    self.referral_code = referal_codee
            self.referral_code = referal_codee
        super().save(*args, **kwargs)

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(user=instance)

    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, **kwargs):
        instance.profile.save()

    def __str__(self):
        return str(self.user)
    
class Feedback(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,default=1)
    title=models.CharField(max_length=100)
    desc=models.TextField()
    posted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-posted_at']