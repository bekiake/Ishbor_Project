from django.db import models


class User(models.Model):
    telegram_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    is_worker = models.BooleanField(default=False, verbose_name='Is Worker')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name if self.name else "Unknown User"


class Skills(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True, verbose_name='Name')

    def __str__(self):
        return self.name



class Worker(models.Model):
    PAYMENT_CHOICES = (
        ('naqd','Naqd'),
        ('karta','Karta'),
        ('barchasi','Barchasi')
    )

    GENDER_CHOICES = (
        ('male','Male'),
        ('female','Female')
    )
    
    TIME_CHOICES = (
        ('kunlik','Kunlik'),
        ('soatlik','Soatlik'),
        ('oylik','Oylik'),
        ('haftalik','Haftalik'),
        ('barchasi','Barchasi')
    )
    DISABILITY_CHOICES = (
        ('no', 'Nogiron emas'),
        ('1', '1-daraja nogironlik'),
        ('2', '2-daraja nogironlik'),
        ('3', '3-daraja nogironlik'),
    )


    telegram_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255, null=True, blank=True, verbose_name='Name')
    about = models.TextField(max_length=255, null=True, blank=True, verbose_name='About')
    image = models.ImageField(upload_to='media/uploads/workers/', null=True, blank=True)
    age = models.IntegerField(null=True, blank=True, verbose_name='Age')
    phone = models.CharField(max_length=255,null=True, blank=True, verbose_name='Phone', unique=True)
    gender = models.CharField(max_length=255, choices=GENDER_CHOICES, null=True, blank=True, verbose_name='Gender')
    payment_type = models.CharField(max_length=255, choices=PAYMENT_CHOICES, default='barchasi', null=True, blank=True, verbose_name='Payment Type')
    time_type = models.CharField(max_length=255, choices=TIME_CHOICES, default='barchasi', null=True, blank=True, verbose_name='Time Type')
    daily_payment = models.IntegerField(null=True, blank=True, verbose_name='Daily Payment')
    languages = models.CharField(max_length=255, null=True, blank=True, verbose_name='Languages')
    skills = models.TextField(max_length=255, null=True, blank=True, verbose_name='Skills')
    location = models.CharField(max_length=255, null=True, blank=True, verbose_name='Location')
    is_active = models.BooleanField(default=True, verbose_name='Active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    disability_degree = models.CharField(max_length = 2,choices = DISABILITY_CHOICES,default = 'no',verbose_name = 'Nogironlik darajasi')
    aliment_payer=models.BooleanField(default=False,verbose_name='Aliment Payer')
    aliment_payer_code = models.CharField(
        max_length = 255, null = True, blank = True, verbose_name = 'Aliment Payer Kod'
    )

    def __str__(self):
        return self.name if self.name else "Unknown Worker"

    def get_languages_list(self):
        return [lang.strip() for lang in self.languages.split(",")] if self.languages else []

    def get_skills_list(self):
        return [skill.strip() for skill in self.skills.split(",")] if self.skills else []

    def set_languages(self, languages_list):
        self.languages = ", ".join(languages_list)

    def set_skills(self, skills_list):
        self.skills = ", ".join(skills_list)
    
    def __str__(self):
        return self.name if self.name else "Unknown Worker"


class Feedback(models.Model):
    RATE_CHOICES = [
        (1, '1 - Very Bad'),
        (2, '2 - Bad'),
        (3, '3 - Neutral'),
        (4, '4 - Good'),
        (5, '5 - Excellent'),
    ]

    worker = models.ForeignKey(Worker, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rate = models.IntegerField(choices=RATE_CHOICES, default=1)
    text = models.TextField(max_length=255, null=True, blank=True, verbose_name='Text')
    create_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, verbose_name='Active')
    update_at = models.DateTimeField(auto_now=True)
    

class News(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True, verbose_name='Name')
    title = models.CharField(max_length=255, null=True, blank=True, verbose_name='Title')
    description = models.TextField(max_length=255, null=True, blank=True, verbose_name='Description')
    image = models.ImageField(upload_to='media/uploads/news/', null=True, blank=True)
    count_views = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name if self.name else "Unknown News"

class NewsView(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='news_views')
    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name='views')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'news')

    def __str__(self):
        return f"{self.user} viewed {self.news}"