from django.db import models
from django.contrib.auth.models import User

class Computer(models.Model):
    pc_id = models.CharField(max_length=20, unique=True)  # VIP1, VIP2
    room = models.CharField(max_length=50)
    status = models.CharField(max_length=20, default="Available")
    position = models.PositiveIntegerField(default=0)

    # user currently using the PC
    current_user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="active_pc"
    )

    def __str__(self):
        return f"{self.pc_id} ({self.room})"


class Session(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pc = models.ForeignKey(Computer, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField()
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - {self.pc.pc_id}"