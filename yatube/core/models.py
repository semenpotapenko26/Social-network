from django.db import models


class PubDateModel(models.Model):
    '''Абстрактная модель. Добавляет дату публикации'''
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        abstract = True


class CreatedModel(models.Model):
    '''Абстрактная модель. Добавляет дату создания комментария'''
    created = models.DateTimeField(
        'Дата создания',
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        abstract = True
