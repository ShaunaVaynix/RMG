from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

# ---------------- User Profile ----------------
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(
        max_length=10,
        choices=[('Active', 'Active'), ('Inactive', 'Inactive')],
        default='Active'
    )

    def __str__(self):
        return self.user.username


# ---------------- Computers ----------------
class Computer(models.Model):

    ROOM_CHOICES = [
        ('VIP', 'VIP'),
        ('Gaming', 'Gaming'),
        ('Regular', 'Regular'),
        ('Streaming', 'Streaming'),
    ]

    STATUS_CHOICES = [
        ('Available', 'Available'),
        ('In Use', 'In Use'),
        ('Reserved', 'Reserved'),
        ('Maintenance', 'Maintenance'),
        ('Offline', 'Offline'),
    ]

    room = models.CharField(max_length=20, choices=ROOM_CHOICES)
    pc_id = models.CharField(max_length=20, unique=True)
    specs = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Available'
    )
    current_user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="current_pc")
    maintenance = models.TextField(blank=True)
    position = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.pc_id} ({self.status})"


# ---------------- Reservations ----------------
class Reservation(models.Model):

    PC_CHOICES = [
        ('VIP', 'VIP'),
        ('Gaming', 'Gaming'),
        ('Regular', 'Regular'),
        ('Streaming', 'Streaming'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Active', 'Active'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    pc_type = models.CharField(max_length=20, choices=PC_CHOICES)
    seat = models.CharField(max_length=20)

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    total_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    def clean(self):
        # Check for overlapping reservations
        overlapping = Reservation.objects.filter(
            seat=self.seat,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time
        ).exclude(id=self.id)

        if overlapping.exists():
            raise ValidationError("This seat is already reserved at this time.")

        if self.start_time >= self.end_time:
            raise ValidationError("End time must be after start time.")

    def save(self, *args, **kwargs):
        # Calculate duration & price
        duration = self.end_time - self.start_time
        hours = duration.total_seconds() / 3600
        self.total_hours = round(hours, 2)
        self.total_price = round(hours * 20, 2)  # Assuming 20 PHP/hour
        super().save(*args, **kwargs)

        # 🔥 AUTO UPDATE COMPUTER STATUS
        try:
            computer = Computer.objects.get(pc_id=self.seat)

            if self.status in ["Confirmed", "Active"]:
                computer.status = "Reserved"
            elif self.status in ["Completed", "Cancelled"]:
                computer.status = "Available"
            computer.save()

        except Computer.DoesNotExist:
            pass

    def __str__(self):
        user_name = self.user.username if self.user else "No User"
        return f"{user_name} - {self.seat} ({self.status})"


# ---------------- Payments ----------------
class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.FloatField()
    reference = models.CharField(max_length=20)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - ₱{self.amount} - {self.reference}"