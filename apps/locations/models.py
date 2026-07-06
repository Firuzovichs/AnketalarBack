from django.db import models


class Country(models.Model):
    name    = models.CharField(max_length=100)                    # English
    name_uz = models.CharField(max_length=100, blank=True)        # O'zbekcha
    name_ru = models.CharField(max_length=100, blank=True)        # Русский
    code    = models.CharField(max_length=3, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Davlat'
        verbose_name_plural = 'Davlatlar'

    def __str__(self):
        return self.name_uz or self.name


class Region(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='regions')
    name    = models.CharField(max_length=100)                    # English / asosiy
    name_uz = models.CharField(max_length=100, blank=True)        # O'zbekcha
    name_ru = models.CharField(max_length=100, blank=True)        # Русский

    class Meta:
        ordering = ['name_uz', 'name']
        verbose_name = 'Viloyat'
        verbose_name_plural = 'Viloyatlar'

    def __str__(self):
        return self.name_uz or self.name


class District(models.Model):
    region  = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='districts')
    name    = models.CharField(max_length=100)                    # English / asosiy
    name_uz = models.CharField(max_length=100, blank=True)        # O'zbekcha
    name_ru = models.CharField(max_length=100, blank=True)        # Русский

    class Meta:
        ordering = ['name_uz', 'name']
        verbose_name = 'Tuman'
        verbose_name_plural = 'Tumanlar'

    def __str__(self):
        return self.name_uz or self.name
