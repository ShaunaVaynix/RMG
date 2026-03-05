from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse
from .models import Computer, Reservation, UserProfile, Payment
import json
from datetime import datetime
from django.core.exceptions import ValidationError
from django.utils.crypto import get_random_string
from django.views.decorators.csrf import csrf_exempt


# ---------------- Home ----------------
def home(request):
    return render(request, 'todo/home.html')


# ---------------- Registration ----------------
def register_view(request):
    if request.method == "POST":
        first_name = request.POST.get('first_name')
        email = request.POST.get('email')
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect('register')

        user = User.objects.create_user(
            username=username,
            password=password1,
            email=email,
            first_name=first_name
        )
        UserProfile.objects.create(user=user)
        messages.success(request, "Account created successfully! Please login.")
        return redirect('login')

    return render(request, 'registration/register.html')


# ---------------- Login / Logout ----------------
def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            if user.is_staff:
                return redirect('admin_dashboard')
            else:
                return redirect('user_dashboard')
        messages.error(request, "Invalid credentials.")
        return redirect('login')
    return render(request, 'registration/login.html')


def logout_view(request):
    logout(request)
    return redirect('home')


# ---------------- Dashboards ----------------
@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        return redirect('user_dashboard')

    total_computers = Computer.objects.count()
    total_users = User.objects.count()
    total_reservations = Reservation.objects.count()
    available = Computer.objects.filter(status="Available").count()

    # Get computers with color-class mapping
    computers = Computer.objects.all()
    pc_list = []
    for pc in computers:
        color_class = "available"
        if pc.status == "In Use":
            color_class = "inuse"
        elif pc.status == "Reserved":
            color_class = "reserved"
        elif pc.status == "Maintenance":
            color_class = "maintenance"
        elif pc.status == "Offline":
            color_class = "offline"
        pc_list.append({
            "pc_id": pc.pc_id,
            "room": pc.room,
            "status": pc.status,
            "color_class": color_class
        })

    return render(request, 'todo/admin_dashboard.html', {
        "total_computers": total_computers,
        "total_users": total_users,
        "total_reservations": total_reservations,
        "available": available,
        "computers": pc_list
    })


@login_required
def user_dashboard(request):
    if request.user.is_staff:
        return redirect('admin_dashboard')

    my_reservations = Reservation.objects.filter(user=request.user)
    available = Computer.objects.filter(status="Available").count()
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    transactions = Payment.objects.filter(user=request.user).order_by('-date')

    # User computers with color class
    computers = Computer.objects.all()
    pc_list = []
    for pc in computers:
        color_class = "available"
        if pc.status == "In Use":
            color_class = "inuse"
        elif pc.status == "Reserved":
            color_class = "reserved"
        elif pc.status == "Maintenance":
            color_class = "maintenance"
        elif pc.status == "Offline":
            color_class = "offline"
        pc_list.append({
            "pc_id": pc.pc_id,
            "room": pc.room,
            "status": pc.status,
            "color_class": color_class
        })

    return render(request, 'user/user_dashboard.html', {
        "my_reservations": my_reservations,
        "available": available,
        "profile": profile,
        "transactions": transactions,
        "computers": pc_list
    })


# ---------------- Computers ----------------
@login_required
def computers_view(request):
    if not request.user.is_staff:
        return redirect('user_computers')
    computers = Computer.objects.all()
    rooms = {room: computers.filter(room=room) for room in ["VIP", "Gaming", "Regular", "Streaming"]}
    return render(request, "todo/computers.html", {"rooms": rooms})


@login_required
def user_computers(request):
    if request.user.is_staff:
        return redirect('computers')
    computers = Computer.objects.all()
    rooms = {room: computers.filter(room=room) for room in ["VIP", "Gaming", "Regular", "Streaming"]}
    return render(request, "user/user_computers.html", {"rooms": rooms})


# ---------------- Users ----------------
@login_required
def users_view(request):
    users = User.objects.all().select_related('userprofile')
    return render(request, 'todo/users.html', {'users': users})


# ---------------- Reservations ----------------
@login_required
def reserve_view(request):
    if request.user.is_staff:
        reservations = Reservation.objects.all()
        return render(request, 'todo/reservation.html', {'reservations': reservations})
    else:
        return redirect('user_reservation')


@login_required
def user_reservation(request):
    if request.user.is_staff:
        return redirect('admin_dashboard')
    reservations = Reservation.objects.filter(user=request.user)
    return render(request, 'user/user_reservation.html', {'reservations': reservations})


@login_required
def get_reservations_json(request):
    if request.user.is_staff:
        reservations = Reservation.objects.all().values(
            'user__username', 'pc_type', 'seat', 'start_time', 'end_time', 'total_hours', 'total_price', 'status'
        )
    else:
        reservations = Reservation.objects.filter(user=request.user).values(
            'user__username', 'pc_type', 'seat', 'start_time', 'end_time', 'total_hours', 'total_price', 'status'
        )
    return JsonResponse(list(reservations), safe=False)


@login_required
@require_http_methods(["POST"])
def add_reservation(request):
    try:
        data = json.loads(request.body)
        pc_type = data.get("pc_type")
        seat = data.get("seat")
        start_time = datetime.fromisoformat(data.get("start_time"))
        end_time = datetime.fromisoformat(data.get("end_time"))

        reservation = Reservation(
            user=request.user,
            pc_type=pc_type,
            seat=seat,
            start_time=start_time,
            end_time=end_time,
            status="Pending"
        )
        reservation.full_clean()
        reservation.save()
        return JsonResponse({"message": "Reservation added successfully."})
    except ValidationError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


# ---------------- Computers API ----------------
@login_required
def get_computers_json(request):
    rooms = {room: [] for room in ["VIP", "Gaming", "Regular", "Streaming"]}
    for pc in Computer.objects.all():
        if pc.room in rooms:
            rooms[pc.room].append({
                "pc_id": pc.pc_id,
                "room": pc.room,
                "specs": pc.specs,
                "status": pc.status,
                "position": pc.position
            })
    return JsonResponse(rooms)


@login_required
@require_http_methods(["POST"])
def add_computer(request):
    try:
        data = json.loads(request.body)
        pc_id = data.get('pc_id')
        room = data.get('room')
        specs = data.get('specs')
        status = data.get('status', 'Available')
        position = data.get('position', 0)

        if not all([pc_id, room, specs]):
            return JsonResponse({"error": "Missing required fields."}, status=400)

        if Computer.objects.filter(pc_id=pc_id).exists():
            return JsonResponse({"error": "PC ID already exists."}, status=400)

        Computer.objects.create(pc_id=pc_id, room=room, specs=specs, status=status, position=position)
        return JsonResponse({"message": "Computer added successfully."})
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON."}, status=400)


@login_required
@require_http_methods(["DELETE"])
def delete_computer(request, pc_id):
    try:
        pc = Computer.objects.get(pc_id=pc_id)
        pc.delete()
        return JsonResponse({"message": "Deleted successfully."})
    except Computer.DoesNotExist:
        return JsonResponse({"error": "PC not found."}, status=404)


# ---------------- Update PC Status API ----------------
@login_required
@require_http_methods(["POST"])
def update_computer_status(request, pc_id):
    try:
        pc = get_object_or_404(Computer, pc_id=pc_id)
        data = json.loads(request.body)
        new_status = data.get("status")
        if new_status not in ["Available", "In Use", "Reserved", "Offline", "Maintenance"]:
            return JsonResponse({"error": "Invalid status."}, status=400)
        pc.status = new_status
        pc.save()
        return JsonResponse({"message": "Status updated successfully."})
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON."}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


# ---------------- Payment ----------------
@login_required
def payment_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    pending_reservations = Reservation.objects.filter(user=request.user, status__iexact="Pending")
    transactions = Payment.objects.filter(user=request.user).order_by('-date')

    if request.method == "POST":
        reservation_id = request.POST.get("reservation_id")
        reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user, status__iexact="Pending")

        # Update reservation status to SUCCESS
        reservation.status = "SUCCESS"
        reservation.save()

        # Update PC status to Reserved
        try:
            pc = Computer.objects.get(pc_id=reservation.seat)
            pc.status = "Reserved"
            pc.save()
        except Computer.DoesNotExist:
            pass

        # Save Payment transaction
        reference = "REF-" + get_random_string(8)
        Payment.objects.create(user=request.user, amount=reservation.total_price, reference=reference)

        messages.success(request, "Payment Successful!")
        return redirect("payment")

    return render(request, "user/payment.html", {
        "pending_reservations": pending_reservations,
        "transactions": transactions,
        "profile": profile
    })


# ---------------- PC Login ----------------
def pc_login_page(request):
    pcs = Computer.objects.filter(status__in=["Available", "Reserved"])
    return render(request, "pc_login.html", {"pcs": pcs})


@csrf_exempt
def pc_login_api(request):
    if request.method == "POST":
        data = json.loads(request.body)
        username = data.get("username")
        pc_id = data.get("pc_id")

        # Check user exists
        try:
            user = UserProfile.objects.get(user__username=username)
        except UserProfile.DoesNotExist:
            return JsonResponse({"success": False, "error": "User not found!"})

        # Check PC exists
        try:
            pc = Computer.objects.get(pc_id=pc_id)
        except Computer.DoesNotExist:
            return JsonResponse({"success": False, "error": "PC not found!"})

        if pc.status == "In Use":
            return JsonResponse({"success": False, "error": "PC already in use!"})

        # Update PC status
        pc.status = "In Use"
        pc.current_user = user.user
        pc.save()

        # Update reservation if exists
        reservation = pc.reservation_set.filter(user=user.user, status="SUCCESS").first()
        if reservation:
            reservation.status = "In Use"
            reservation.save()

        return JsonResponse({"success": True})
    return JsonResponse({"success": False, "error": "Invalid request"})





@login_required
@require_http_methods(["POST"])
def add_reservation(request):
    try:
        data = json.loads(request.body)
        pc_type = data.get("pc_type")
        seat_input = data.get("seat")  # e.g., "VIP-1"
        start_time = datetime.fromisoformat(data.get("start_time"))
        end_time = datetime.fromisoformat(data.get("end_time"))

        # Normalize seat to match Computer.pc_id
        pc_id_clean = seat_input.replace("-", "").upper()
        pc = Computer.objects.get(pc_id__iexact=pc_id_clean)

        reservation = Reservation(
            user=request.user,
            pc_type=pc.room,
            seat=pc.pc_id,  # always store normalized pc_id
            start_time=start_time,
            end_time=end_time,
            status="Pending"
        )
        reservation.full_clean()
        reservation.save()
        return JsonResponse({"message": "Reservation added successfully."})
    except Computer.DoesNotExist:
        return JsonResponse({"error": f"PC '{seat_input}' not found."}, status=400)
    except ValidationError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)