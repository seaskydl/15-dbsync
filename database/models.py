from tortoise import fields
from .core import CoreModel

class User(CoreModel):
  name = fields.CharField(max_length=50, null=False)

class Task(CoreModel):
  name = fields.CharField(max_length=50, null=False)

class Account(CoreModel):
  name = fields.CharField(max_length=50, null=False)

class Course(CoreModel):
  name = fields.CharField(max_length=50, null=False)

class Exam(CoreModel):
  name = fields.CharField(max_length=50, null=False)

class Log(CoreModel):
  name = fields.CharField(max_length=50, null=False)
